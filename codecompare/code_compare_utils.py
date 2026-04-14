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

""" common utility methods for code comparisons """

__author__ = "Kurt Hanauer"
__version__ = "0.1.0"
__date__ = "2023-11-03"
__credits__ = "Copyright (C) 2023 Continental Automotive GmbH"

#######################################################################
#
# Module-History
#  Date        Author               Reason
#  2023-11-03  Kurt Hanauer         Initial version
#######################################################################

import os
import re
import shutil
import sys
import subprocess

########################################################################################################
# constants
########################################################################################################
COMMIT_REV_LEN = 40
COMMIT_REV_REGEX = r"[A-Za-z0-9]{40}"
GERRIT_REF_REGEX = r"refs/changes/[0-9]{2}/[0-9]{7}/[0-9]+"
PATCH_PATHS_REGEX_LIST = [ r"(/tools/build)", r"(/tools/platform)", r"(/package/specs)", r"(/package/nxp/[^/]*)", \
                        r"(/package/codeaurora/[^/]*)", r"(/package/conti/[^/]*)", r"(/package/opensource/[^/]*)", \
                        r"(/package/qualcomm/[^/]*)", r"(/package/marben/[^/]*)", r"(/layers/project[^/]*)", \
                        r"(/patches)", r"(/.repo/manifests)" ]
PATCHED_REPOS_CMD_TMPL = "cd {patches_path}/patches; export patch_files=$(find {search_path}/ \\( -name *.patch -or -name *sh* \\)); for filename in ${{patch_files[@]}}; do echo $filename | cut -d'/' -f2 | cut -d'_' -f1 | xargs -i  grep -m1 {{}} $filename; done > patched_files.txt; sed 's/--- a//' patched_files.txt | grep '^/' | sed 's@\\(.*\\)/.*@\\1@' > patches_paths_{search_path}.txt; cat patches_paths_{search_path}.txt | sort > patches_paths_{search_path}_sorted.txt"
OTP_PROJECT = 'otp'
OTP_MANIFEST_NAME = "p1/project/otp/manifest"

########################################################################################################
# functions
########################################################################################################

def print_header(text, numOfStars=30):
    """ print a header line

    Args:
        text (str): header text
        numOfStars (int, optional): number of starts printed in the lines above and below the text line. Defaults to 30.
    """
    print("*"*numOfStars)
    print(text)
    print("*"*numOfStars, flush=True)

def launch_command(cmd, display=True):
    """launch a command. For linux launch command(s) in a shell or just launching the command in windows (not used here)

    Args:
        cmd (str): full command string to launch in linux shell
        display (bool, optional): display command execution. Defaults to True.

    Returns:
        int: return code
        bytes: output for parsing or error string
    """
    if display:
        print(cmd)
    # This is done in order to have compatibility cross-platform
    # for windows to be able to use the command the shell has to be set to
    # false and true for Unix
    if os.name == "nt":
        use_shell = False
    else:
        use_shell = True

    processOutput = subprocess.Popen(cmd, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=use_shell)
    out, err = processOutput.communicate()
    # Decode output if it's in bytes.
    out = out.decode("utf-8") if isinstance(out, bytes) else out
    err = err.decode("utf-8") if isinstance(err, bytes) else err
    # Determine the final output based on the presence of stderr.
    if len(err) > 0:
        output = err
    else:
        output = out
    if display:
        print(output)

    # Get the command return code
    return_code = processOutput.returncode

    if display:
        print(f'RC({return_code})')  # Display the return code.

    return return_code, output

def create_main_index_page(folder, title, use_tables=False, project_name="drt15"):
    """
    create the main html overview page for all code compare index pages under that folder

    Args:
        folder (str): folder to handle. Also the output folder for the main index page
        title (str): title line for the page
    """
    if os.path.exists("{}/html_deps".format(folder)) and os.path.isdir("{}/html_deps".format(folder)):
        shutil.rmtree("{}/html_deps".format(folder))
    os.makedirs(folder, exist_ok=True)
    shutil.copytree( "{}/diff2HtmlCompare/html_deps".format(sys.path[0]), "{}/html_deps".format(folder))

    subdirs = []
    index_files = []
    otp_base_index_files = []
    otp_new_index_files = []
    for f in os.scandir(folder):
        if f.is_dir():
            subdirs.append(f.path)

    for directory in list(subdirs):
        if ".git" in directory:
            continue
        for f in os.scandir(directory):
            if f.is_file() and (f.name == "index.html"):
                index_path = f.path
                if index_path.startswith(folder):
                    index_path = index_path[len(folder)+1:]
                index_files.append(index_path)
                print ( index_path )
            elif  f.name.startswith("included_releases_"):
                index_path = f.path
                if index_path.startswith(folder):
                    index_path = index_path[len(folder)+1:]
                if "included_in_base_version" in directory:
                    otp_base_index_files.append(index_path)
                elif "included_in_new_version" in directory:
                    otp_new_index_files.append(index_path)
                print ( index_path )

    print( "Creating main_index.html page...")
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
        <h3 style="font-family:verdana;font-size:2em;">{page_title}</h3>
        <hr>
        <hr>
        <br><br>
"""
    HTML_END = """
    </body>
</html>
"""
    page_fill = {
        "html_title":     "Main index {}".format(title),
        "page_title":     "Main index {}".format(title),
    }
    INDEX_PAGE = HTML_START.format(**page_fill)
    if len(otp_base_index_files) > 0:
        if use_tables == True:
            INDEX_PAGE = INDEX_PAGE + """
            <table border="1" style="font-family:monospace;font-size:1.5em;">
                <tr><th>base otp repo links</th></tr>\n
        """
            for html_file in otp_base_index_files:
                if not html_file.startswith("html_deps"):
                    INDEX_PAGE += '\n           <tr><td><a href="{}">{}</a></td></tr>'.format( html_file, html_file )
            INDEX_PAGE += "\n        </table>\n"
        else:
            INDEX_PAGE = INDEX_PAGE + """<b>base otp repo links:</b><br><br>\n"""
            for html_file in otp_base_index_files:
                if not html_file.startswith("html_deps"):
                    INDEX_PAGE += '\n           <a href="{}">{}</a><br>'.format( html_file, html_file )
        INDEX_PAGE += "\n        <br><br>\n"

    if len(otp_new_index_files) > 0:
        if use_tables == True:
            INDEX_PAGE = INDEX_PAGE + """
            <table border="1" style="font-family:monospace;font-size:1.5em;">
                <tr><th>new otp repo links</th></tr>\n
        """
            for html_file in otp_new_index_files:
                if not html_file.startswith("html_deps"):
                    INDEX_PAGE += '\n           <tr><td><a href="{}">{}</a></td></tr>'.format( html_file, html_file )
            INDEX_PAGE += "\n        </table>\n"
        else:
            INDEX_PAGE = INDEX_PAGE + """<b>new otp repo links:</b><br><br>\n
        """
            for html_file in otp_new_index_files:
                if not html_file.startswith("html_deps"):
                    INDEX_PAGE += '\n           <a href="{}">{}</a><br>'.format( html_file, html_file )
        INDEX_PAGE += "\n        <br><br>\n"
    html_folders, html_files = subdirs, index_files

    # index entries...
    if use_tables == True:
        INDEX_PAGE = INDEX_PAGE + """
        <table border="1" style="font-family:monospace;font-size:1.2em;">
            <tr><th>index links</th></tr>\n
        """
        for html_file in sorted(html_files):
            if not html_file.startswith("html_deps"):
                cmd_realname = 'echo "{}" | sed "s@\\(.*\\)/index.html@\\1@" | sed "s@_@/@g"'.format(html_file)
                ret_code, realname = launch_command(cmd_realname)
                if ret_code != 0:
                    print( "Error on {} command:\n{}".format(cmd_realname, realname))
                    sys.exit(1)
                INDEX_PAGE += '\n           <tr><td><a href="{}">{}</a></td></tr>'.format( html_file, realname )
        INDEX_PAGE += "\n        </table>\n"
    else:
        INDEX_PAGE = INDEX_PAGE + """<b>index links</b><br><br>\n"""
        for html_file in sorted(html_files):
            if not html_file.startswith("html_deps"):
                cmd_realname = 'echo "{}" | sed "s@\\(.*\\)/index.html@\\1@" | sed "s@_@/@g"'.format(html_file)
                ret_code, realname = launch_command(cmd_realname)
                realname = realname.strip()
                print(f"Realname before processing >{realname}<")
                if ret_code != 0:
                    print( "Error on {} command:\n{}".format(cmd_realname, realname))
                    sys.exit(1)
                # cut away the work area path...
                replace = False
                if realname.startswith("p1/package"):
                        reg_ex = r"^(p1/package/.*)/package/.*"
                        replace = True
                elif realname.startswith("p1/project"):
                        reg_ex = r"^(p1/project/.*)/(?:manifests|layers|tools|package)/.*"
                        replace = True
                elif realname.startswith("opensource"):
                        reg_ex = r"^(opensource/.*)/package/.*"
                        replace = True
                elif realname.startswith(project_name):
                        reg_ex = fr"^({project_name}/.*)/(?:package|layers)/.*"
                        replace = True
                if replace == True:
                    try:
                        realname = re.fullmatch(reg_ex,realname)[1]
                    except Exception as e:
                        print(f"Evaluating reg_ex {reg_ex} failed! Keeping full name {realname}!")
                        # keep the name as originally, if the regex fails...
                        pass
                print(f"Realname after processing >{realname}<")
                INDEX_PAGE += '\n           <a href="{}">{}</a><br>'.format( html_file, realname )
        INDEX_PAGE += "\n"
    INDEX_PAGE += "\n"
    INDEX_PAGE += HTML_END

    with open("{}/main_index.html".format(folder), "w") as index_file:
        index_file.write( INDEX_PAGE )
    print("Main index page successfully created!")

def is_executable(filepath):
    """check if a file is executable

    Args:
        filepath (str): full file path

    Returns:
        boolean: true if this is a file and it's executable
    """
    return os.path.isfile(filepath) and os.access(filepath, os.X_OK)

def check_to_skip(repo_name, skip_list):
    """check if the given repo is contained in the skip list

    Args:
        repo_name (str): repo name to check for
        skip_list (list): list of rppo names to skip

    Returns:
        boolean: true if the repo name was found in the skip list
    """
    skip_repo=False
    for repo_to_skip_compare in skip_list:
        if repo_to_skip_compare in repo_name:
            print_header("Repo {} is marked to skip!".format(repo_name))
            skip_repo=True
            break
    return skip_repo

def install_repo_tool():
    """install the 'repo' tool from internal server
    """
    repo_cmd = "mkdir -p ~/bin && cd ~/bin; wget https://confluence-iic.zone2.agileci.conti.de/download/attachments/96510342/repo; chmod +x repo;"
    launch_command(repo_cmd)

def get_sorted_subdir_list(searchpath):
    """get a alphabetically sorted list of subdirectories back for searchpath

    Args:
        searchpath (str): path to search for subdirs

    Returns:
        list: alphabetically sorted list of subdirectories
    """
    dir_list = [entry for entry in os.listdir(searchpath) if os.path.isdir(os.path.join(searchpath, entry))]
    dir_list.sort(key=lambda subdir: os.path.getmtime(os.path.join(searchpath, subdir)))
    return dir_list
