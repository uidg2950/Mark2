#!/usr/bin/python3
#######################################################################
#
# Copyright Notice:
# Copyright (C) 2023
# Continental Automotive GmbH
# Alle Rechte vorbehalten. All Rights Reserved.
# The reproduction, transmission or use of this document or its
# contents is not permitted without express written authority.
# Offenders will be liable for damages.
# All rights, including rights created by patent grant or registration
# of a utility model or design, are reserved.
#
#######################################################################

""" compare two given versions of a repo """

__author__ = "Kurt Hanauer"
__version__ = "0.2.0"
__date__ = "2023-11-16"
__credits__ = "Copyright (C) 2023 Continental Automotive GmbH"

#######################################################################
#
# Module-History
#  Date        Author               Reason
#  2020-09-10  Kurt Hanauer         Initial version
#######################################################################

import re
import os
import sys
import argparse
import shutil
import json
from code_compare_utils import GERRIT_REF_REGEX, PATCH_PATHS_REGEX_LIST, create_main_index_page
import magic
from diff2HtmlCompare import diff2HtmlCompare
import filecmp
from code_compare_utils import print_header, launch_command, get_sorted_subdir_list, COMMIT_REV_REGEX, COMMIT_REV_LEN, check_to_skip, PATCHED_REPOS_CMD_TMPL

def parseargs():
    """ parse command line arguments

    Parameters
    ----------
    None

    Returns
    -------
    args:
        parser result argument list
    """
    parser = argparse.ArgumentParser(description="compare two given versions of a repo.")
    parser.add_argument('-r', action='store', dest='repo', help="full repo name, e.g. p1/project/drt/main")
    parser.add_argument('-s', '--second_repo', action='store', dest='repo2', help="full modified/SECOND repo name (only needed if two different repos need to be compared)")
    parser.add_argument('-b', '--base_version', action='store', help="Base (first) repo version for compare")
    parser.add_argument('-m', '--modified_version', action='store', help="Modified (second) repo version for compare")
    parser.add_argument('--host', action='store', dest="host_name", help="gerrit host name to connect to (for git commands and output links)", default="buic-scm-ias.contiwan.com")
    parser.add_argument('--port', action='store', dest="gerrit_port", help="gerrit port", default = "29418")
    parser.add_argument('--patch', action='store_true', help="attempt to create a simple patch file from base_version to modified_version")
    parser.add_argument('--patch_path', action='store', help="output_path for patch file (defaults to './patch'", default="patch")
    parser.add_argument('--output_path', action='store', help="Output path for html pages (defaults to 'html')", default="html")
    parser.add_argument('--verbose', action='store_true', help="verbose output")
    args=parser.parse_args()
    if (args.repo==None) or (args.base_version==None) or (args.modified_version==None):
        parser.print_help()
        sys.exit(1)
    print(args)
    return args

def get_gerrit_rev(host, port, commit, patchset="latest"):
    """get the git revision for the given Gerrit commit and patchset (if given)

    Args:
        host (str): Gerrit host name
        port (str): Gerrit port
        commit (str): Gerrit commit number
        patchset (str, optional): patchset number. Defaults to "latest".

    Returns:
        str: revision belonging to commit/patchset
        str: branch belonging to commit/patchset
        str: project/repo name belonging to commit/patchset
    """
    print_header(f"Get Gerrit rev for {commit}, {patchset}")
    if patchset == "latest":
        get_from_gerrit_cmd = f"ssh -p {port} {host} gerrit query --format=JSON --current-patch-set {commit}"
    else:
        get_from_gerrit_cmd = f"ssh -p {port} {host} gerrit query --format=JSON --patch-sets {commit}"
    ret_code, query_result = launch_command(get_from_gerrit_cmd, False)
    revision = None
    if ret_code == 0:
        # remove transfer info...
        json_input = str(query_result, "utf-8").rsplit("\n",2)
        #print(json_input[0])
        json_result = json.loads(json_input[0])
        if patchset == "latest":
            #print("Patchset is 'latest'")
            revision = json_result["currentPatchSet"]["revision"]
            #print(json_result)
        else:
            for patchset_content in json_result["patchSets"]:
                #print(f"checking {patchset_content['number']}")
                if patchset_content["number"] == f"{patchset}":
                    #print(f"Match for {patchset_content}")
                    revision = patchset_content["revision"]
                    break
        branch = json_result["branch"]
        project = json_result["project"]
    return revision, branch, project


def load_repo(host_name, port, repo, revision, verbose=False, reference_path=None, output_path=None, commit=None, patchset=None, fetch=False):
    """load a Gerrit repo

    Args:
        host_name (str): Gerrit host name
        port (str): Gerrit port
        repo (str): repo name to clone
        revision (str): revision to clone (will be corrected, if 'None', a branch or tag given)
        verbose (bool, optional): verbose output. Defaults to False.
        reference_path (str, optional): a reference path for 'git clone'. Will speed up the cloning if given. Defaults to None.
        output_path (str, optional): you can pre-define the output path here. If it already exists, cloning will be skipped. Defaults to None.
        commit (str, optional): Gerrit commit number. Defaults to None.
        patchset (str, optional): Gerrit commit patchset. Defaults to None.
        fetch (bool, optional): do a fetch after cloning and before checkout. Defaults to False.

    Raises:
        Exception: raised if clone fails
        Exception: raised if fetch/checkout fails

    Returns:
        str: patch to cloned repo
        str: revision of cloned repo
    """
    host = host_name
    # fix for repos, where there isn't a revision given in the manifest file...
    if revision == None:
        revision = to_revision(host, port, repo, "master")
        fetch = True
    elif not re.fullmatch(COMMIT_REV_REGEX, revision): # check if revision is a not a revision number...
        revision = to_revision(host, port, repo, revision)
        fetch = True
    print_header("Getting revision {} for repo {}".format(revision, repo))
    repo_name = repo.replace('/', '_')
    repo_path = "repo_{}_{}".format(repo_name, revision)
    if output_path != None and os.path.exists(output_path.rsplit('/',1)[0]):
        repo_path = output_path
    if os.path.exists(repo_path) and os.path.isdir(repo_path):
        #shutil.rmtree(repo_path)
        print("A directory with that revision {} already exists! ***skip cloning***".format(revision))
    else:
        # clone repo
        options = ""
        if reference_path != None and os.path.isdir(reference_path):
            options = " --reference {} ".format(reference_path)
        else:
            # check for other repos with that name...
            reference_dirs = get_sorted_subdir_list(os.getcwd())
            for reference_dir in reference_dirs:
                if repo_name in reference_dir:
                    reference_path = reference_dir
                    print("Using existing {} as reference!".format(reference_path))
                    options = " --reference {} ".format(reference_path)
                    break

        clone_command = "git clone ssh://{hn}:{p}/{r} {o} {rp} && scp -p -P {p} {hn}:hooks/commit-msg {rp}/.git/hooks/".format(hn=host, p=port, r=repo, o=options, rp=repo_path)
        ret_code, result = launch_command( clone_command, verbose)
        if ret_code != 0:
            print("Error on {} command:\n{}".format(clone_command, result))
            #if an error occured here, attempt a clone without reference here, before giving up!
            if os.path.exists(repo_path) and os.path.isdir(repo_path):
                shutil.rmtree(repo_path)
            clone_command = "git clone ssh://{hn}:{p}/{r} {rp} && scp -p -P {p} {hn}:hooks/commit-msg {rp}/.git/hooks/".format(hn=host, p=port, r=repo, rp=repo_path)
            ret_code, result = launch_command( clone_command, verbose)
            if ret_code != 0:
                print("Error on {} command:\n{}".format(clone_command, result))
                raise Exception("Error on git clone for {}".format(repo))

        if commit == None:
            if fetch == False:
                rev_command = "cd {}; git checkout {}".format(repo_path, revision)
            else:
                rev_command = "cd {}; git fetch; git checkout {}".format(repo_path, revision)
        else:
            rev_command = "cd {rp}; git fetch ssh://{hn}:{p}/{r} refs/changes/{coend}/{co}/{ps} && git checkout FETCH_HEAD".format(rp=repo_path, hn=host, p=port, r=repo, o=options, coend=commit[-2:], co=commit, ps=patchset)
        ret_code, rev_result = launch_command( rev_command, verbose )
        if ret_code != 0 and commit == None:
            # retry...
            rev_command = "cd {}; git fetch origin; git fetch origin {rev}; git checkout {rev}".format(repo_path, rev=revision)
            ret_code, rev_result = launch_command( rev_command, verbose )
        if ret_code != 0:
            print("Error on {} command:\n{}".format(rev_command, rev_result))
            raise Exception("Error on checking out {}".format(repo))

        print_header("repo successfully cloned and checkout done!")
    return repo_path, revision

def get_file_list(repo_path, remove_path=False, verbose=False):
    """get full file and directory lists for a path

    Args:
        repo_path (str): repo path to check for files and directories
        remove_path (bool, optional): remove the given 'repo_path' from the returned list elements. Defaults to False.
        verbose (bool, optional): verbose output. Defaults to False.

    Returns:
        list: subdirectories
        list: files
    """
    # get full file and directory lists for a path
    subdirs = []
    files = []

    for f in os.scandir(repo_path):
        if f.is_symlink() and os.path.isdir(f.path):
            if verbose==True:
                print("*** Skipping directory symlink {}!".format(f))
            continue
        if f.is_symlink() and not os.path.exists(os.readlink(f.path)):
            if verbose==True:
                print("!!! Error: {} is a broken symlink! Skipping!".format(f))
            continue
        if f.is_symlink() and os.readlink(f.path) == f.path:
            if verbose==True:
                print("### ERROR: DISCOVERED RECURSIVE FILE LINK {}!!! SKIPPING!".format(f))
            continue
        if f.is_dir():
            subdirs.append(f.path)
        if f.is_file():
            fileinfo = magic.detect_from_filename(f.path)
            if fileinfo.encoding == 'binary':
                if verbose==True:
                    print(f"--- Skipping binary file {f}: {fileinfo}")
                continue
            files.append(f.path)
            #if verbose==True:
            #    print ( f.path )

    for directory in list(subdirs):
        if ".git" in directory:
            continue
        sub_d, sub_f = get_file_list(directory)
        subdirs.extend(sub_d)
        files.extend(sub_f)

    ret_subdirs = []
    ret_files = []
    if remove_path==True:
        len_to_remove = len( repo_path )
        for subdir in subdirs:
            subd = subdir[len_to_remove:]
            #subd = subdir.lstrip( repo_path )
            #subd = subd.lstrip( '/')
            if verbose==True:
                print( subd )
            ret_subdirs.append( subd )
        for f in files:
            fl = f[len_to_remove:]
            #fl = f.lstrip( repo_path )
            #fl = fl.lstrip( '/' )
            if verbose==True:
                print( fl )
            ret_files.append( fl )
    else:
        ret_files = files
        ret_subdirs = subdirs
    return ret_subdirs, ret_files


def compare_repo_versions(repo_path_base, repo_path_modified, outputfolder="html", verbose=False, format_timeout=30):
    """gets file lists for base and modified repo paths and compares the resulting file list by contest

    Args:
        repo_path_base (str): path to base (first) repo folder for the comparison
        repo_path_modified (str): path to modified (second) repo folder for the comparison
        outputfolder (str, optional): folder, where the compare result files will be stored. Defaults to "html".
        verbose (bool, optional): verbose output. Defaults to False.
        format_timeout (int, optional): timeout for one file comparison in seconds. Defaults to 30.

    Returns:
        list: list of files, which are only in the base folder
        list: list of files, which are only in the modified folder
    """
    # compare two versions of a repo
    print_header(f"Comparing repo versions for {outputfolder}", 60)
    dir_list_base = []
    file_list_base = []
    dir_list_modified = []
    file_list_modified = []
    files_only_in_base_list = []
    files_only_in_modified_list = []
    if repo_path_base != repo_path_modified:
        # get the file lists:
        if repo_path_base != None and repo_path_base != '':
            dir_list_base, file_list_base = get_file_list(repo_path_base, True, verbose)
        if repo_path_modified != None and repo_path_modified != '':
            dir_list_modified, file_list_modified = get_file_list(repo_path_modified, True, verbose)

        #dirs_in_both = list ( set(dir_list_base).intersection( set(dir_list_modified)))
        #dirs_only_in_list_base = list ( set(dir_list_base).difference( set(dir_list_modified)))
        #dirs_only_in_list_modified = list ( set(dir_list_modified).difference( set(dir_list_base)))

        files_in_both = list( set(file_list_base).intersection( set(file_list_modified)))
        files_only_in_base_list = list( set(file_list_base).difference( set(file_list_modified)))
        files_only_in_modified_list = list( set(file_list_modified).difference( set(file_list_base)))

        # argparse arguments are expected by diff2HtmlCompare, so create a parser object...
        parser = argparse.ArgumentParser(description="For diff2HtmlCompare")
        parser.add_argument('-p', '--print-width', action='store_true' )
        parser.add_argument('-c', '--syntax-css', action='store', default="vs")
        parser.add_argument('-v', '--verbose', action='store_true' )
        parser.add_argument('-d', '--depth', action='store',default=0, help="subdir depth for output file")
        parser.add_argument('--timeout', action="store", help="timeout for page formatting in seconds (defaults to 60)", default="60")


        # prepare output folder
        if os.path.exists(outputfolder) and os.path.isdir(outputfolder):
            print(f"Warning {outputfolder} already existed. will be removed!")
            shutil.rmtree(outputfolder)
        if not os.path.exists(outputfolder):
            os.makedirs(outputfolder, exist_ok=True)

        for file_in_both in files_in_both:
            file_base = "{}/{}".format(repo_path_base, file_in_both)
            file_modified = "{}/{}".format(repo_path_modified, file_in_both)
            outputfile = "{}/{}.html".format(outputfolder, file_in_both)
            if not filecmp.cmp( file_base, file_modified, shallow=False):
                depth = file_in_both.count('/')
                args = parser.parse_args(['-c', 'vs', '-d', "{}".format(depth), '--timeout', f"{format_timeout}" ])
                codeDiff = diff2HtmlCompare.CodeDiff(file_base, file_modified, name=file_in_both)
                codeDiff.format(args)
                codeDiff.write(outputfile)

        for file_only_in_base_list in files_only_in_base_list:
            file_base = "{}/{}".format(repo_path_base, file_only_in_base_list)
            outputfile = "{}/{}.html".format(outputfolder, file_only_in_base_list)

            depth = file_only_in_base_list.count('/')
            if verbose==True:
                print("File only in base list is {}".format(file_only_in_base_list))
            args = parser.parse_args(['-c', 'vs', '-d', "{}".format(depth), '--timeout', f"{format_timeout}" ])
            codeDiff = diff2HtmlCompare.CodeDiff(file_base, None, totxt="FILE DOES NOT EXIST", name=file_only_in_base_list)
            codeDiff.format(args)
            codeDiff.write(outputfile)

        for file_only_in_modified_list in files_only_in_modified_list:
            file_modified = "{}/{}".format(repo_path_modified, file_only_in_modified_list)
            outputfile = "{}/{}.html".format(outputfolder, file_only_in_modified_list)

            depth = file_only_in_modified_list.count('/')
            if verbose==True:
                print("File only in modified list is {}".format(file_only_in_modified_list ))
            args = parser.parse_args(['-c', 'vs', '-d', "{}".format(depth), '--timeout', f"{format_timeout}" ])
            codeDiff = diff2HtmlCompare.CodeDiff(None, file_modified, fromtxt="FILE DOES NOT EXIST", name=file_only_in_modified_list)
            codeDiff.format(args)
            codeDiff.write(outputfile)

        dirs, files = get_file_list(outputfolder)
        if len(files) > 0:
            if not os.path.exists(os.path.join(outputfolder, "html_deps")):
                shutil.copytree( "{}/diff2HtmlCompare/html_deps".format(sys.path[0]), "{}/html_deps".format(outputfolder))
            print("Compare finished successfully!")
        else:
            print(f"No difference found! Skipping {outputfolder}!")
            os.rmdir(outputfolder)
    else:
        print("INFO: Sorry won't compare identical folder paths!!!")
    return files_only_in_base_list, files_only_in_modified_list

def get_git_log_modified(modified_folder, base_revision, modified_version, verbose=False):
    """get the 'oneliner' git log entries for the differences base to modified versions

    Args:
        modified_folder (str): folder in which git log will be executed
        base_version (str): base revision
        modified_version (str): modified revision
        verbose (bool, optional): verbose output. Defaults to False.

    Returns:
        list: list with git log entries
        boolean: have results been swapped? This will happen if the base revision is newer than the modified revision
    """
    git_log_command = "cd {}; git log --pretty=oneline {}..{}".format(modified_folder, base_revision, modified_version)
    ret_code, git_log_result = launch_command( git_log_command, verbose)
    if ret_code != 0:
        print("Skipped ERROR git log {} {}".format(base_revision,modified_version))
        return 'Skip', False

    swapped = False
    git_log_entries = git_log_result.split('\n')
    if len(git_log_entries) == 0 or len(git_log_entries[0]) == 0:
        # try a reverted call
        git_log_command = "cd {}; git log --pretty=oneline {}..{}".format(modified_folder, modified_version, base_revision)
        ret_code, git_log_result = launch_command( git_log_command, verbose)
        if ret_code != 0:
            print("Skipped ERROR git log {} {}".format(base_revision,modified_version))
            return 'Skip', False
        else:
            print("INFO: commit order 'git log' is swapped for {}!!!".format(modified_folder))
            git_log_entries = git_log_result.split('\n')
            swapped = True
    return git_log_entries, swapped

def create_index_page(folder, repo, base_revision, modified_revision, files_only_in_base_list=[], files_only_in_modified_list=[], modified_folder=None, verbose=False, repo2 = None):
    """create an index page for a repo diff

    Args:
        folder (str): output folder name
        repo (str): repo name
        base_revision (str): base revision for comparison
        modified_revision (str): modified revision for comparison
        files_only_in_base_list (list, optional): list of files, which are only in the base folder. Defaults to [].
        files_only_in_modified_list (list, optional): list of files, which are only in the modified folder. Defaults to [].
        modified_folder (str, optional): needed to create 'git log' entries for the revision diffs. Defaults to None.
        verbose (bool, optional): verbose output. Defaults to False.
        repo2 (str, optional): in case you compare two different repos. Added as last parameter for compability to existing code...
    """
    if os.path.isdir(folder):
        git_log_entries = []
        log_swapped = False
        if modified_folder:
            git_log_entries, log_swapped = get_git_log_modified(modified_folder, base_revision, modified_revision, True)
            if git_log_entries == 'Skip':
                git_log_entries = []
                #return
            #print( "Git log: {}".format(git_log_entries))

        print_header( "Creating index.html page...")
        HTML_START = """
<!DOCTYPE html>
<html class="no-js">
    <head>
        <!--
          html_title:    browser tab title
          page_title:    title shown at the top of the page. This should be the filename of the files being diff'd
        -->
        <meta charset="utf-8">
        <title>
            {html_title}
        </title>
    </head>
    <body>
        <hr>
        <h3 style="font-family:verdana;"">{page_title}</h3>
        <hr>
        <h4 style="font-family:monospace;">version {base_version}
        compared with
        version {modified_version}</h4>
        <hr>
        <br><br>
"""
        HTML_END = """
    </body>
</html>
"""
        repo_text = repo if repo2 == None else "{} to {}".format(repo, repo2)
        page_fill = {
            "html_title":     "Folder diff for {}".format(repo_text),
            "page_title":     "Folder diff for {}".format(repo_text),
            "base_version"  :     base_revision,
            "modified_version"  :     modified_revision
        }
        INDEX_PAGE = HTML_START.format(**page_fill)
        html_folders, html_files = get_file_list(folder, True, True)
        add_changed_removed_re = re.compile(r"added/changed/removed\(right side\): (\d*/\d*/\d*)")
        if len(html_files) > 0:
            INDEX_PAGE = INDEX_PAGE + """
            <table border="1" style="font-family:monospace;">
            <tr><th>changed file(s)</th><th>additional information</th><th>added/changed/removed<br>(right side)</th></tr>\n
    """
            #print("files_only_in_base_list is >{}<".format(files_only_in_base_list))
            #print("files_only_in_modified_list is >{}>".format(files_only_in_modified_list))
            for html_file_name in sorted(html_files):
                if html_file_name.startswith('/'):
                    html_file = html_file_name[1:]
                else:
                    html_file = html_file_name
                if not html_file.startswith("html_deps"):
                    #print("html_file is >{}<".format(html_file))
                    ADDITIONAL_INFO = "MODIFIED"
                    temp_filename = "/{}".format(html_file[:-len(".html")])
                    if temp_filename in files_only_in_base_list:
                        ADDITIONAL_INFO = "REMOVED"
                    elif temp_filename in files_only_in_modified_list:
                        ADDITIONAL_INFO = "NEW"
                    change_info = "-/-/-"
                    if ADDITIONAL_INFO == "MODIFIED":
                        change_ref_text = "added/changed/removed(right side):"
                        with open(os.path.join(folder,html_file)) as file_contents:
                            lines = file_contents.readlines()
                            for line in lines:
                                if change_ref_text in line:
                                    change_info_match = add_changed_removed_re.search(line)
                                    if change_info_match != None:
                                        change_info = change_info_match.group(1)
                                    else:
                                        print("No change entry found for {}!".format(html_file))
                                    break

                    INDEX_PAGE += '\n           <tr><td><a href="{}">{}</a></td><td>{}</td><td>{}</td></tr>'.format(html_file, html_file, ADDITIONAL_INFO, change_info)
            INDEX_PAGE += "\n        </table>\n"

            if git_log_entries != []:
                swapped_text = ''
                if log_swapped:
                    swapped_text = 'ATTENTION: swapped compare results!!!'

                INDEX_PAGE += '<br/><br/><h4 style="font-family:monospace;">GIT LOG ENTRIES: {}</h4>\n'.format(swapped_text)
                INDEX_PAGE = INDEX_PAGE + """        <table border="1" style="font-family:monospace;">
                    <tr><th>ID</th><th>log entry text</th></tr>\n
    """
                for log_entry in git_log_entries:
                    if log_entry != '':
                        INDEX_PAGE += "<tr>\n"
                        log_parts=log_entry.split(" ", 1)
                        log_ID = log_parts[0]
                        log_ID_link = "https://buic-scm:8443/gitweb?p={}.git;a=commit;h={}".format( repo, log_ID)
                        INDEX_PAGE += '<td><a href="{}">{}</a></td>'.format( log_ID_link, log_ID )
                        INDEX_PAGE += '<td>{}</td></tr>\n'.format( log_parts[1] )
                INDEX_PAGE += "</table>\n"
            INDEX_PAGE += HTML_END

            with open("{}/index.html".format(folder), "w") as index_file:
                index_file.write( INDEX_PAGE )
            print_header("Index page successfully created!")
        else:
            print_header("no different files found! Skipping!")

def create_patch(args, repo_path_base,repo_path_modified):
    """create a simple patch from a diff between repo_path_base and repo_path_modified
    TODO: check if still useable!!!

    Args:
        args (Namespace): command line arguments
        repo_path_base (str): path to base repo
        repo_path_modified (str): path to modified repo
    """
    print_header("Creating patch file...")

    repo_full_path = args.repo
    repo_name = args.repo[args.repo.rfind("/")+1:]
    patch_name = "{}_XX_description.patch".format(repo_name)

    # prepare output folder
    patch_dir = args.patch_path
    if os.path.exists(patch_dir):
        shutil.rmtree(patch_dir)
    os.mkdir(patch_dir)

    # now create the patch
    patch_command = "diff -rup --exclude=.git {} {} > {}/{}".format(repo_path_base, repo_path_modified, patch_dir, patch_name)
    ret_code, patch_result = launch_command( patch_command, args.verbose )
    # Exit status is 0 if inputs are the same, 1 if different, 2 if trouble.
    if ret_code == 2:
        print( "Error on {} command:\n{}".format( patch_command, patch_result ))
        sys.exit(1)
    # Replace paths in the patch file
    patch_file_path = os.path.join(patch_dir, patch_name)
    with open(patch_file_path, 'r') as file:
        patch_content = file.read()

    # Assuming the paths to replace start with 'repo_' and end with a hash
    # Adjust the start and end strings according to your actual paths
    patch_content = patch_content.replace(repo_path_base, repo_full_path)
    patch_content = patch_content.replace(repo_path_modified, repo_full_path)

    with open(patch_file_path, 'w') as file:
        file.write(patch_content)
    print("Patch {}/{} successfully created!".format(patch_dir, patch_name))

def get_revision_from_remote_branch(host, port, repo, branch):
    """get the revision from remove branch name

    Args:
        host (str): host for remote connection
        port (str): port for remote connection
        repo (str): repo name
        branch (str): remote branch

    Returns:
        str: revision
    """
    ls_remote_cmd = f"git ls-remote ssh://{host}:{port}/{repo} {branch} | cut -d$'\\t' -f1  | cut -d$'\\n' -f1"
    ret_code, result = launch_command(ls_remote_cmd)
    if ret_code !=  0:
        print_header("ERROR: ls-remote failed!")
        print(result)
        sys.exit(1)
    return result.strip()

def get_branch_from_revision(host, port, repo, revision):
    """ get the branch name belonging to a given repo revision

    Args:
        host (str): hostname
        port (str): port
        repo (str): repo name
        revision (str): code revision

    Returns:
        str: branch name
    """
    directory, revision = load_repo(host, port, repo, revision)
    #rev_name_cmd = f"cd {directory}; git name-rev --name-only --exclude=tags/* {revision}"
    rev_name_cmd = f"cd {directory}; git name-rev --name-only {revision}"
    ret_code, result = launch_command(rev_name_cmd)
    if ret_code != 0:
        print_header("ERROR: ls-remote failed!")
        print(result)
        sys.exit(1)
    branch = result.strip()
    print(f"get_branch_from_revison returned {branch}")
    branch = branch.rsplit('~')[0]
    branch = branch.rsplit('/')[-1]
    print(f"returning {branch}")
    return branch

def to_revision(host, port, repo, version):
    """get the revision out of the given 'version', which could be a revision, a branch name or a commit number

    Args:
        host (str): Gerrit host
        port (str): Gerrit port
        repo (str): repo name
        version (str): version string (whatever version can be...)

    Returns:
        _type_: _description_
    """
    rev = version if version != None else "master"
    if not re.fullmatch(COMMIT_REV_REGEX, rev):
        if re.fullmatch(GERRIT_REF_REGEX, rev):
            commit = rev.split('/')[-2]
            patchset = rev.split('/')[-1]
            rev, branch, project = get_gerrit_rev(host, port, commit, patchset)
        else:
            rev = get_revision_from_remote_branch(host, port, repo, rev)
    return rev

def execute_patching(path_to_patched_repos, repos, project_name, cas_target_hw, hw_variant, additional_exports, args, verbose=False):
    """patch 'repos' (on base of existing cloned repos) for given project and cas_target_hw

    Args:
        path_to_patched_repos (str): path, where the patching has to take place
        repos (list): list with repos (element trees)
        project_name (str): name of the project
        cas_target_hw (str): cas_target_hw string. Needed to apply the correct patches
        hw_variant: HW_VARIANT string. Needed to apply patches correctly
        additional_exports: additional project specific exports. Will be added to an own export [settings] line
        args: argiuments: passsed for having host and port
        verbose: verbose output. Defaults to 'False'
    """
    if os.path.exists(path_to_patched_repos):
        shutil.rmtree(path_to_patched_repos)
    os.mkdir(path_to_patched_repos)
    workarea = os.getcwd()
    # go to patches top folder
    os.chdir(path_to_patched_repos)
    for repo in repos:
        # try to filter projects by those, which do not contain the project name...
        repo_name = repo.get('name')
        repo_rev = repo.get('revision')
        repo_rev = to_revision(args.host_name, args.gerrit_port, repo_name, repo_rev)
        repo_path = repo.get('path')
        # load repo from reference dir
        ref_repo_name = repo_name.replace('/', '_')
        ref_repo_path = os.path.join(workarea, "repo_{}_{}".format(ref_repo_name, repo_rev))
        #output_dir = os.path.dirname(os.path.join(os.getcwd(), repo_path))
        output_dir = os.path.join(os.getcwd(), repo_path)
        print("Ouput dir is: {}".format(output_dir))
        if not os.path.exists(output_dir.rsplit('/', 1)[0]):
                os.makedirs(output_dir.rsplit('/', 1)[0])
        base_repo_path, repo_rev = load_repo(args.host_name, args.gerrit_port, repo_name, repo_rev, verbose, ref_repo_path, output_dir)
   # apply patches
    print_header( "[{}] Patching mechanism in progress for {}!".format(project_name, os.getcwd()))
    os.makedirs("logs", exist_ok=True)
    patches_dir = os.path.join(os.getcwd(), "patches")
    # first repair deny_clobber_patch !
    #repair_cmd_drt15 = "sed '/# SyI out-of-band imports/,/popd >/dev/null/ {{/repo download.*/d,s@\(pushd tools/build >/dev/null\)@\1\ngit fetch ssh://buic-scm:29418/p1/project/vivace/build refs/changes/31/1820931/13 && git cherry-pick FETCH_HEAD@}}' -i {pdir}/common/build_00_DO-618_PART_1_deny_clobber_logs_removal.shxb".format(pdir=patches_dir)
    # TODO: search a not project specific solution!
    if project_name == "drt15":
        if os.path.exists(f"{patches_dir}/common/build_00_DO-618_PART_1_deny_clobber_logs_removal.sh"):
            os.rename(f"{patches_dir}/common/build_00_DO-618_PART_1_deny_clobber_logs_removal.sh", f"{patches_dir}/common/build_00_DO-618_PART_1_deny_clobber_logs_removal.shxb")
        repair_cmd_drt15 = "sed 's/\\(|| {{\\)\\( \\${{CAS_TARGET_HW:0:8}} = drt15-sa \\]\\)/\\1 [\\2/' -i {pdir}/common/build_00_DO-618_PART_1_deny_clobber_logs_removal.sh*; sed '/# SyI out-of-band imports/,/# DRT15-35194/ {{/repo download.*/d;/.*cd tools.*/d;/pushd tool.*/d;/git reset.*/d;/popd .*/d;s@^$@if [ -z $_dl ]; then _dl=1820931/13; fi; _dl=refs/changes/${{_dl:5:2}}/${{_dl}};pushd tools/build >/dev/null\\ngit fetch ssh://buic-scm:29418/p1/project/vivace/build $_dl \\&\\& git cherry-pick FETCH_HEAD\\npopd >/dev/null\\n@}}' -i {pdir}/common/build_00_DO-618_PART_1_deny_clobber_logs_removal.sh*".format(pdir=patches_dir)
        launch_command(repair_cmd_drt15)
        #repair_cmd_drt15_2 = "sed 's/patch -NElup1 -i/patch -NElup1 --follow-symlinks -i/' -i {pdir}/install_patches".format(pdir=patches_dir)
        #launch_command(repair_cmd_drt15_2)
        # workaround for wrong patch :-(
        if cas_target_hw == "drt15-imx8-le21":
            fix_link_cmd = "cd {curdir}/layers/project; ln -s imx8-xl-gm/ {targethw}".format(curdir=os.getcwd(), targethw=cas_target_hw)
            launch_command(fix_link_cmd)
    if additional_exports != None:
        add_exports="export {}".format(additional_exports.replace(',', ' '))
    patch_cmd = "set -x; mkdir -p .build; touch logs/logfile.log; touch .build/env-common; touch .build/env-buildsys-static; export log_file=logs/logfile.log; export bld_dry_run=0; export bld_log_dir={curdir}/logs; export bld_log_id=42; touch logs/.fifo.42; touch logs/.summary.42; export bld_top_dir={curdir}; export bld_target_hw={targethw}; export HW_VARIANT={hwvar}; export CAS_TARGET_HW={targethw}; {addexp}; cd {curdir}; {patchdir}/install_patches `mktemp` &>> {curdir}/logs/patches.log".format(curdir=os.getcwd(), targethw=cas_target_hw, hwvar=hw_variant, patchdir=patches_dir, addexp=add_exports)
    ret_code, output = launch_command(patch_cmd, True)
    if ret_code != 0:
        print_header("ERROR: patching failed!")
        print(output)
        sys.exit(1)
    os.chdir(workarea)

def get_patched_repo_list(path_patched_repos, cas_target_hw):
    """get a list of patched repos from the given path. Uses predefined templates to execute shell 'find' commands.
    First the 'common' patches will be checked, after that the patches for CAS_TARGET_HW

    Args:
        path_patched_repos (str): path to the top folder, where the patched repos are stored
        cas_target_hw (str): cas_target_hw, for which the patches have beed applied

    Returns:
        list: list of patched repo paths
    """
    patched_repos = []
    patched_repos_cmd_common = PATCHED_REPOS_CMD_TMPL.format(patches_path=path_patched_repos, search_path="common")
    launch_command(patched_repos_cmd_common, True)
    with open("{}/patches/patches_paths_common_sorted.txt".format(path_patched_repos)) as inputfile:
        for line in inputfile:
            patched_repos.append(line.rstrip('\n'))
    patched_repos_cmd_cas_target_hw = PATCHED_REPOS_CMD_TMPL.format(patches_path=path_patched_repos, search_path=cas_target_hw)
    launch_command(patched_repos_cmd_cas_target_hw, True)
    with open("{}/patches/patches_paths_{}_sorted.txt".format(path_patched_repos, cas_target_hw)) as inputfile:
        for line in inputfile:
            patched_repos.append(line.rstrip('\n'))
    patched_repos = list(set(patched_repos))
    return patched_repos

def compare_patched_repos(project_name, workarea, args, path_patched_base_repos, patched_base_repos, base_version_tag, path_patched_new_repos, patched_new_repos, new_version_tag, VERBOSE_OUTPUT=False):
    """compare two patched repos.

    Args:
        project_name (str): the project name
        workarea (str): main workarea path (used to join full folder paths)
        args (Namespace): command line arguments
        path_patched_base_repos (str): path to patched base repos
        patched_base_repos (list): list of patched base repos
        base_version_tag (str): base version tag name for index page creation
        path_patched_new_repos (str): path to patches new repos
        patched_new_repos (list): list of patched new repos
        new_version_tag (str): new version tag name for index page creation
        VERBOSE_OUTPUT (bool, optional): verbose output. Defaults to False.
    """
    print_header("Comparing patched repos...", 50)
    common_repos = [ "/layers/project", f"/layers/project-{project_name}", "/patches" ]
    patched_base_repos.extend(common_repos)
    patched_new_repos.extend(common_repos)
    if VERBOSE_OUTPUT:
        print(patched_new_repos)
        print(patched_base_repos)

    patched_base_repos_list = []
    patched_new_repos_list = []
    for regex in PATCH_PATHS_REGEX_LIST:
        regc = re.compile( regex )
        for patched_base_repo in patched_base_repos:
            matched = regc.match(patched_base_repo)
            if matched != None:
                print("Found {}! Appending to base repos...".format(matched[1]))
                patched_base_repos_list.append(matched[1])
        for patched_new_repo in patched_new_repos:
            matched = regc.match(patched_new_repo)
            if matched != None:
                print("Found {}! Appending to new repos...".format(matched[1]))
                patched_new_repos_list.append(matched[1])
    # eleminate duplicates:
    patched_base_repos_list = list(set(patched_base_repos_list))
    patched_new_repos_list = list(set(patched_new_repos_list))
    # create diffs:
    patched_in_both = list(set(patched_base_repos_list).intersection(set(patched_new_repos_list)))
    patched_in_base = list(set(patched_base_repos_list).difference(set(patched_new_repos_list)))
    patched_in_new = list(set(patched_new_repos_list).difference(set(patched_base_repos_list)))
    # now compare...
    for patched in patched_in_both:
        pure_repo_name = "patched_{}".format(patched.replace('/', '_'))
        files_only_in_base_list, files_only_in_modified_list = compare_repo_versions(os.path.join(workarea, path_patched_base_repos, patched.lstrip('/')), os.path.join(workarea, path_patched_new_repos, patched.lstrip('/')), "{}/{}/".format(args.output_path,pure_repo_name), VERBOSE_OUTPUT)
        create_index_page("{}/{}/".format(args.output_path,pure_repo_name), pure_repo_name, base_version_tag, new_version_tag, files_only_in_base_list, files_only_in_modified_list, None, True)
    for patched in patched_in_base:
        pure_repo_name = "patched_{}".format(patched.replace('/', '_'))
        files_only_in_base_list, files_only_in_modified_list = compare_repo_versions(os.path.join(workarea, path_patched_base_repos, patched.lstrip('/')), None, "{}/{}/".format(args.output_path,pure_repo_name), VERBOSE_OUTPUT)
        create_index_page("{}/{}/".format(args.output_path,pure_repo_name), pure_repo_name, base_version_tag, new_version_tag, files_only_in_base_list, files_only_in_modified_list, None, True)
    for patched in patched_in_new:
        pure_repo_name = "patched_{}".format(patched.replace('/', '_'))
        files_only_in_base_list, files_only_in_modified_list = compare_repo_versions(None, os.path.join(workarea, path_patched_new_repos, patched.lstrip('/')), "{}/{}/".format(args.output_path,pure_repo_name), VERBOSE_OUTPUT)
        create_index_page("{}/{}/".format(args.output_path,pure_repo_name), pure_repo_name, base_version_tag, new_version_tag, files_only_in_base_list, files_only_in_modified_list, None, True)


def compare_projects(base_projects, new_projects, repos_to_skip_compare, args, apply_patches=False, VERBOSE_OUTPUT=False):
    """compare content of project lists: compare repos which are in both, create lists for added or removed projects...
       New: add comparison of repos with different names but identical paths!

    Args:
        base_projects (list): list of base repos/projects for comparison
        new_projects (list): list of new repos/projects for comparison
        repos_to_skip_compare (list): list which contains repos to skip. Very complex or big repos may be excluded to speed up the comparison
        args (Namespace): command line arguments
        apply_patches (bool, optional): if set unused repos in the list will be cloned anyway, because they are needed to apply patches later. Defaults to False.
        VERBOSE_OUTPUT (bool, optional): verbose output. Defaults to False.
    """
    new_projects_not_in_base = []
    base_projects_not_in_new = []
    found_base_projects = []
    found_new_projects = []
    for base_project in base_projects:
        base_project_found = False
        base_project_name = base_project.get('name')
        base_project_path = base_project.get('path')
        for new_project in new_projects:
            new_project_name = new_project.get('name')
            new_project_path = new_project.get('path')
            if (base_project_name == new_project_name) and check_to_skip(base_project_name, repos_to_skip_compare) == False :
                base_project_rev = base_project.get('revision')
                new_project_rev = new_project.get('revision')
                if (base_project_rev !=  new_project_rev):
                    print_header("\nComparing revisions for {}\n".format(base_project_name))
                    base_repo_path, base_project_rev = load_repo(args.host_name, args.gerrit_port, base_project_name, base_project_rev, VERBOSE_OUTPUT)
                    new_repo_path, new_project_rev = load_repo(args.host_name, args.gerrit_port, new_project_name, new_project_rev, VERBOSE_OUTPUT, reference_path=base_repo_path)

                    pure_repo_name = "{}_{}".format(base_project_name.replace('/', '_'), base_project_path.replace('/', '_')) #[base_project_name.rfind('/')+1:]
                    if '//' not in "{}/{}/".format(args.output_path,pure_repo_name) and (base_project_path == new_project_path):
                        files_only_in_base_list, files_only_in_modified_list = compare_repo_versions(base_repo_path, new_repo_path, "{}/{}/".format(args.output_path,pure_repo_name), VERBOSE_OUTPUT)
                        create_index_page("{}/{}/".format(args.output_path,pure_repo_name), base_project_name, base_project_rev, new_project_rev, files_only_in_base_list, files_only_in_modified_list, new_repo_path)
                    elif (base_project_path != new_project_path):
                        print("paths do not match for repo {}: {} <> {}".format(base_project_name, base_project_path, new_project_path))
                        continue
                    else:
                        print("Skipping file with strange path >{}/{}/<".format(args.output_path,pure_repo_name))
                        continue
                else:
                    if apply_patches == True: # and (project_name not in base_project_name):
                        print("Revisions is the same, but needed to apply patches! Cloning...")
                        base_repo_path, base_project_rev = load_repo(args.host_name, args.gerrit_port, base_project_name, base_project_rev, VERBOSE_OUTPUT)
                    else:
                        print("Revision is the same for {}! Skipping...".format(base_project_name))
                base_project_found = True
                found_base_projects.append(base_project)
                found_new_projects.append(new_project)
                break
        if base_project_found == False:
            base_projects_not_in_new.append( base_project )
    for new_project in new_projects:
        if new_project not in found_new_projects and check_to_skip(new_project.get('name'), repos_to_skip_compare) == False:
            new_projects_not_in_base.append(new_project)

    if len(base_projects_not_in_new) > 0 and len(new_projects_not_in_base) > 0:
        print_header("Checking for remaining projects with same path entry but different name...:")
        base_to_remove = []
        new_to_remove = []
        for base_project in base_projects_not_in_new:
            base_project_name = base_project.get('name')
            base_project_rev = base_project.get('revision')
            base_project_path = base_project.get('path')
            if check_to_skip(base_project_name, repos_to_skip_compare) == False:
                for new_project in new_projects_not_in_base:
                    print("{}".format(new_project))
                    new_project_name = new_project.get('name')
                    new_project_rev = new_project.get('revision')
                    new_project_path = new_project.get('path')
                    if base_project_path == new_project_path:
                        print_header("\nMATCH! Comparing {} path content for {} and {}\n".format(base_project_path, base_project_name, new_project_name))
                        base_repo_path, base_project_rev = load_repo(args.host_name, args.gerrit_port, base_project_name, base_project_rev, VERBOSE_OUTPUT)
                        new_repo_path, new_project_rev = load_repo(args.host_name, args.gerrit_port, new_project_name, new_project_rev, VERBOSE_OUTPUT, reference_path=base_repo_path)
                        pure_repo_name = "{}_{}".format(base_project_name.replace('/', '_'), base_project_path.replace('/', '_'))
                        files_only_in_base_list, files_only_in_modified_list = compare_repo_versions(base_repo_path, new_repo_path, "{}/{}/".format(args.output_path,pure_repo_name), VERBOSE_OUTPUT)
                        create_index_page("{}/{}/".format(args.output_path,pure_repo_name), base_project_name, base_project_rev, new_project_rev, files_only_in_base_list, files_only_in_modified_list, new_repo_path, VERBOSE_OUTPUT, new_project_name)
                        base_to_remove.append(base_project)
                        new_to_remove.append(new_project)
                        break
        # correct lists:
        for to_remove in base_to_remove:
            base_projects_not_in_new.remove(to_remove)
        for to_remove in new_to_remove:
            new_projects_not_in_base.remove(to_remove)

    if len(base_projects_not_in_new) > 0:
        print_header("Removed projects:")
        for base_project in base_projects_not_in_new:
            base_project_name = base_project.get('name')
            base_project_rev = base_project.get('revision')
            base_project_path = base_project.get('path')
            if check_to_skip(base_project_name, repos_to_skip_compare) == False:
                print("{}".format(base_project_name))
                base_repo_path, base_project_rev = load_repo(args.host_name, args.gerrit_port, base_project_name, base_project_rev, VERBOSE_OUTPUT)
                pure_repo_name = "{}_{}".format(base_project_name.replace('/', '_'), base_project_path.replace('/', '_'))
                files_only_in_base_list, files_only_in_modified_list = compare_repo_versions(base_repo_path, None, "{}/{}/".format(args.output_path,pure_repo_name), VERBOSE_OUTPUT)
                create_index_page("{}/{}/".format(args.output_path,pure_repo_name), base_project_name, base_project_rev, "REMOVED", files_only_in_base_list, files_only_in_modified_list)
    if len(new_projects_not_in_base) > 0:
        print_header("Added projects:")
        for new_project in new_projects_not_in_base:
            print("{}".format(new_project))
            new_project_name = new_project.get('name')
            new_project_rev = new_project.get('revision')
            new_project_path = new_project.get('path')
            if check_to_skip(new_project_name, repos_to_skip_compare) == False:
                print("{}".format(new_project_name))
                new_repo_path, new_project_rev = load_repo(args.host_name, args.gerrit_port, new_project_name, new_project_rev, VERBOSE_OUTPUT)
                pure_repo_name = "{}_{}".format(new_project_name.replace('/', '_'), new_project_path.replace('/', '_'))
                files_only_in_base_list, files_only_in_modified_list = compare_repo_versions(None, new_repo_path, "{}/{}/".format(args.output_path,pure_repo_name), VERBOSE_OUTPUT)
                create_index_page("{}/{}/".format(args.output_path,pure_repo_name), new_project_name, "ADDED", new_project_rev, files_only_in_base_list, files_only_in_modified_list)


if __name__ == '__main__':
    """repo version compare main. compare two given versions of a repo
    """
    # get input and output file
    args = parseargs()
    # introduce comparision between two different repos! So check if a second repo name was given
    repo = args.repo
    repo2 =  args.repo
    if args.repo2:
        repo2 = args.repo2

    #GERRIT_HOST="{}:{}".format(args.host_name, args.gerrit_port)
    VERBOSE_OUTPUT = False
    if args.verbose:
        VERBOSE_OUTPUT = True
    # output path needs at least two levels, so that html_deps can be found...
    if args.output_path.split("/")[0] == args.output_path:
        output_path = os.path.join(args.output_path, args.repo.replace('/', '_'))
        if not os.path.exists(os.path.join(args.output_path, "html_deps")):
            shutil.copytree( "{}/diff2HtmlCompare/html_deps".format(sys.path[0]), "{}/html_deps".format(args.output_path))
    else:
        output_path = args.output_path
    # check versions...
    regex = re.compile(COMMIT_REV_REGEX)
    hitlist = regex.findall(args.base_version)
    #print("len base_version {}, len hitlist {}".format(len(args.base_version), len(hitlist)))
    if len(args.base_version) == COMMIT_REV_LEN and len(hitlist) > 0:
        base_version = args.base_version
    else:
        base_version = get_revision_from_remote_branch(args.host_name, args.gerrit_port, repo, args.base_version)
    hitlist = regex.findall(args.modified_version)
    if len(args.modified_version) == COMMIT_REV_LEN and len(hitlist) > 0:
        modified_version = args.modified_version
    else:
        modified_version = get_revision_from_remote_branch(args.host_name, args.gerrit_port, repo2, args.modified_version)

    repo_path_base, base_version = load_repo(args.host_name, args.gerrit_port, repo, base_version, VERBOSE_OUTPUT)
    repo_path_modified, modified_version = load_repo(args.host_name, args.gerrit_port, repo2, modified_version, VERBOSE_OUTPUT)

    files_only_in_base_list, files_only_in_modified_list = compare_repo_versions(repo_path_base, repo_path_modified, output_path, VERBOSE_OUTPUT)
    create_index_page(output_path, args.repo, base_version, modified_version, files_only_in_base_list, files_only_in_modified_list, repo_path_modified, VERBOSE_OUTPUT, repo2)
    # create a (simple) patch between these two repo versions only if requested:
    if args.patch:
        create_patch(args, repo_path_base, repo_path_modified)

    # create main_index.html
    print_header("\nCreating MAIN INDEX PAGE...\n", 50)
    create_main_index_page(args.output_path, "repo code compare for {}: {} to {}: {}".format(repo, base_version, repo2, modified_version))

    # clean input dirs
    #shutil.rmtree(repo_path_base)
    #shutil.rmtree(repo_path_modified)


