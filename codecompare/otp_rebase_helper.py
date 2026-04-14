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

""" otp rebase helper for projects """

__author__ = "Kurt Hanauer"
__version__ = "0.2.0"
__date__ = "2023-11-16"
__credits__ = "Copyright (C) 2023 Continental Automotive GmbH"

#######################################################################
#
# Module-History
#  Date        Author               Reason
#  2020-12-16  Kurt Hanauer         Initial version
#######################################################################

import os
import sys
import argparse
import shutil
import re
import xml.etree.ElementTree as ET
from repo_versions_compare import compare_patched_repos, get_patched_repo_list, get_revision_from_remote_branch, load_repo, compare_repo_versions, create_index_page, launch_command, print_header, execute_patching, get_gerrit_rev, get_branch_from_revision, compare_projects, to_revision
from find_included_releases import ManifestRetreiver, OutputWriter, IncludedReleases
from code_compare_utils import GERRIT_REF_REGEX, PATCH_PATHS_REGEX_LIST, create_main_index_page, COMMIT_REV_LEN, COMMIT_REV_REGEX, check_to_skip, is_executable, OTP_MANIFEST_NAME

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
    parser = argparse.ArgumentParser(description="otp rebase helper for projects using two p1/project/otp/manifest versions")
    parser.add_argument('-b', '--base_version', action='store', help="Base (currently integrated) repo branch/version for compare")
    parser.add_argument('-n', '--new_version', action='store', help="New (otp integration) repo branch/version for compare")
    parser.add_argument('--host', action='store', dest="host_name", help="gerrit host name to connect to (for git commands and output links)", default="buic-scm-ias.contiwan.com")
    parser.add_argument('--port', action='store', dest="gerrit_port", help="gerrit port", default = "29418")
    parser.add_argument('--output_path', action='store', help="Output path for html pages (defaults to './html')", default="html")
    parser.add_argument('--verbose', action='store_true', help="verbose output")
    parser.add_argument('--exclude', action='store', help="repo names to exclude (comma seperated list)", default=None)
    #parser.add_argument('--merge', action="store_true", help="launch mergetool for 'main' repo changes")
    #parser.add_argument('--target', action='store', help="drt15 build target for this merge request (drt15-imx8-5g, drt15-imx8-xl, drt15-imx8, drt15-sa515m, drt15-sa415m", default="drt15-imx8-5g")
    #parser.add_argument('--mergetool', action='store', help="mergetool name to use", default='meld')
    #parser.add_argument('--compare_all', action='store_true', help="compare all different repos (slow)")
    parser.add_argument('--apply_patches', action='store_true', help="---------------------------------\napply project patches to OTP/FERMI repos\n---------------------------------")
    parser.add_argument('--cas_target_hw', action='store', help="needed to apply patches")
    parser.add_argument('--hw_variant', action='store', help="needed to apply patches")
    parser.add_argument('--additional_exports', action='store', help="additional exports as comma seperated list (project specific, as needed to apply patches")
    parser.add_argument('--project', action='store', help="Project name", default="drt15")
    parser.add_argument('--prj_manifest', action='store', help="Project name", default="drt15/manifest")
    parser.add_argument('--base_mfst_version', action='store', help="Base PROJECT version branch/tag for compare")
    parser.add_argument('--manifest_commit_ref', action='store', help="New PROJECT manifest commit ref (if required)")
    parser.add_argument('--main_commit_ref', action='store', help="New PROJECT main repo commit ref (if required)")
    parser.add_argument('--patches_commit_ref', action='store', help="New PROJECT patches repo commit ref (if required)")
    #parser.add_argument('--additional_repos', action='store', help="comma seperated list of additionally required project repos, for patching to succeed!")

    args=parser.parse_args()
    if (args.base_version==None) or (args.new_version==None):
        parser.print_help()
        sys.exit(1)
    if args.apply_patches and (not args.cas_target_hw or not args.hw_variant or not args.project or not args.prj_manifest or not args.base_mfst_version):
        print("Parameters --cas_target_hw --hw_variant --project -- prj_manifest and --base_mfst_version are needed for --apply_patches !")
        parser.print_help()
        sys.exit(1)
    if args.apply_patches and (not args.manifest_commit_ref and not args.main_commit_ref and not args.patches_commit_ref):
        print("You have to give at least one from --manifest_commit_ref --main_commit_ref --patches_commit_ref")
        parser.print_help()
        sys.exit(1)
    #print(args)
    return args

def check_if_merge_tool_exists(mergetool):
    """check if the given mergetool exists in PATH

    Args:
        mergetool (_type_): _description_

    Returns:
        str|None: full path to existing merge tool or None
    """
    for path in os.environ["PATH"].split(os.pathsep):
        merge_executable = os.path.join(path, mergetool)
        if is_executable(merge_executable):
            return merge_executable
    return None

def merge_main_DRT15(args, new_default_otp_root, otp_main_repo, VERBOSE_OUTPUT=False):
    """merge otp main repo for project DO NOT USE!!!
    TODO: outdated!!! check if still useable and update first!!!

    Args:
        args (Namespace): command line argument list
        new_default_otp_root (Element): ET root element for otp manifest
        otp_main_repo (str): otp main repo name
        VERBOSE_OUTPUT (bool, optional): verbose output. Defaults to False.
    """
    """ merge functions are project specific! this one is for DRT15 project only """
    mergetool=check_if_merge_tool_exists(args.mergetool)
    if mergetool == None:
        print("Error: mergetool {} cannot be found!".format(args.mergetool))
        return
    drt15_main_repo="drt15/main"
    targets = [ "drt15-imx8-5g", "drt15-imx8-xl", "drt15-imx8", "drt15-sa515m", "drt15-sa515m-slim", "drt15-sa415m" ]
    if args.target not in targets:
        print("Sorry, but {} is no valid build target! Aborting...".format(args.target))
        return
    # first load latest version of drt15/main repo
    new_otp_main_revision = ''
    for project in new_default_otp_root.findall('project'):
        if project.get('name') == otp_main_repo:
            new_otp_main_revision = project.get('revision')
            break
    drt15_main_repo_path, drt15_main_repo=load_repo(args.host_name, args.gerrit_port, drt15_main_repo, "master", VERBOSE_OUTPUT)
    main_new_repo_path, new_otp_main_revision = load_repo(args.host_name, args.gerrit_port, otp_main_repo, new_otp_main_revision, VERBOSE_OUTPUT)
    temp_main_target_path = "{}_{}".format(drt15_main_repo_path, args.target)
    if os.path.exists(temp_main_target_path) and os.path.isdir(temp_main_target_path):
        shutil.rmtree(temp_main_target_path)
    os.rename(drt15_main_repo_path, temp_main_target_path)
    drt15_main_repo_path = temp_main_target_path
    drt15_merge_path = args.target
    # align otp path:
    otp_merge_path = ""
    if drt15_merge_path == "drt15-imx8-xl":
        otp_merge_path="imx8-xl-gm"
    elif drt15_merge_path == "drt15-imx8-5g":
        otp_merge_path="imx8-xl-gm"
    elif drt15_merge_path == "drt15-imx8":
        otp_merge_path="imx8-phantom-gm"
    elif drt15_merge_path == "drt15-sa415m":
        otp_merge_path="sa415m"
    elif drt15_merge_path == "drt15-sa515m":
        otp_merge_path="sa515m"

    drt15_merge_path = "{}/{}".format(drt15_main_repo_path, drt15_merge_path)
    otp_merge_path = "{}/{}".format(main_new_repo_path, otp_merge_path)
    compare_repo_versions(otp_merge_path, drt15_merge_path, "{}/{}/".format(args.output_path,"drt15_main_to_otp_main"))
    merge_cmd="{} {} {}".format(mergetool, otp_merge_path, drt15_merge_path)
    launch_command(merge_cmd, True)
    print("Merge done! Results can be found in {}".format(drt15_merge_path))
    #shutil.rmtree(drt15_main_repo_path)

def use_patches(host, port, project_name, output_path, project_manifest_repo, base_mfst_version, base_otp_branch, new_otp_branch,
                     base_default_otp_root, base_otp_hal_root, base_otp_framework_root,
                     new_default_otp_root, new_otp_hal_root, new_otp_framework_root,
                     manifest_commit_ref, main_commit_ref, patches_commit_ref,
                     cas_target_hw, hw_variant, additional_exports, args,
                     base_version, new_version, new_projects, VERBOSE_OUTPUT):
    """use and apply patches

    Args:
        host (str): Gerrit host
        port (str): Gerrit prot
        project_name (str): project name
        output_path (str): path for html output files
        project_manifest_repo (str): project manifest repo name
        base_mfst_version (str): base project manifest version
        base_otp_branch (str): base otp branch
        new_otp_branch (str): new otp branch
        base_default_otp_root (Element): ET base otp manifest root element
        base_otp_hal_root (Element): ET base otp hal manifest root element
        base_otp_framework_root (Element): ET base otp framework manifest root element
        new_default_otp_root (Element): ET new otp manifest root element
        new_otp_hal_root (Element): ET new otp hal manifest root element
        new_otp_framework_root (Element): ET new otp framework anifest root element
        manifest_commit_ref (str|None): manifest commit reference of None
        main_commit_ref (str|None): main commit reference or None
        patches_commit_ref (str|None): patches commit reference or None
        cas_target_hw (str): CAS_TARGET_HW
        hw_variant (str): HW_VARIANT
        additional_exports (str): string with comma separated list of additionally needed exports for patching
        args (Namespace): command line arguments
        base_version (str): base version name for index page creation
        new_version (str): new version name for index page creation
        new_projects (list): if manifest is unchanged reuse existing list for new
        VERBOSE_OUTPUT (boolean): verbose output
    """
    # if apply_patches was selected in the input mask, apply the patches to all used repos (copied versions), then compare the patched versions:
    print_header("\nStarting patching...\n", 80)
    workarea = os.getcwd()
    path_patched_base_repos = "patched_base_repos"
    path_patched_new_repos = "patched_new_repos"
    manifest_project_template = """<project
      name="{}"
      path=".repo/manifests"
      revision="{}">
   </project>
"""

    def abort_patching():
        """abort patching. Create main index page before exiting
        """
        print_header("aborting patching!")
        create_main_index_page(output_path, "rebase from {} to {}".format(base_otp_branch, new_otp_branch))
        sys.exit(1)
        #return False

    projectManifestRetreiver = ManifestRetreiver(host, project_name, port, project_manifest_repo)
    projectOuputWriter = OutputWriter("{}/{}".format(output_path,"project_included_in_base_version"), host)

    # get informations for base repo version
    #check first if the given 'base_mfst_version contains a revision number:
    base_mfst_commit_ref = None
    regex = re.compile(COMMIT_REV_REGEX)
    hitlist = regex.findall(base_mfst_version)
    if len(base_mfst_version) == COMMIT_REV_LEN and len(hitlist) > 0:
        # get branch for revision and correct variable assignment:
        base_mfst_commit_ref = base_mfst_version
        base_mfst_version = get_branch_from_revision(host, port, project_manifest_repo, base_mfst_commit_ref )

    base_default_project_root, base_project_manifest_location, base_project_rev = projectManifestRetreiver.get_project_manifest_for_repo(base_mfst_version, consider_includes=True, manifest_commit_ref=base_mfst_commit_ref)
    projectOuputWriter.write_manifest_contents_html("patched__project_included_releases_{}_{}.html".format(base_mfst_version, "base"), base_default_project_root)
    base_otp_branch_cmp = projectManifestRetreiver.get_otp_revision_from_manifest(base_default_project_root)
    print_header("Checking if base otp repo is referenced from project manifest...")
    if to_revision(host, port, OTP_MANIFEST_NAME, base_otp_branch) != to_revision(host, port, OTP_MANIFEST_NAME, base_otp_branch_cmp):
        print_header(f"ERROR: your given project base manifest {project_name} {project_manifest_repo}, does not contain the branch {base_otp_branch}!")
        abort_patching()

    # preparing... loading missing repos
    base_project_manifest_repo_path, base_project_rev = load_repo(host, port, project_manifest_repo, base_project_rev, VERBOSE_OUTPUT, fetch=True)
    base_project_manifest_entry_txt = manifest_project_template.format(project_manifest_repo, base_project_rev)
    base_project_manifest_entry = ET.fromstring(base_project_manifest_entry_txt)
    base_repos = [base_project_manifest_entry]
    base_repos.extend(base_default_project_root.findall("project"))
    base_repos.extend(base_default_project_root.findall("include-project"))
    base_repos.extend( base_default_otp_root.findall("include-project"))
    base_repos.extend( base_default_otp_root.findall("project"))
    base_repos.extend( base_otp_framework_root.findall("project"))
    base_repos.extend( base_otp_hal_root.findall("project"))
    # remove and extend projects...
    base_repos_rm = base_default_project_root.findall("remove-project")
    base_repos_extd = base_default_project_root.findall("extend-project")
    projectManifestRetreiver.remove_and_extend_projects(base_repos, base_repos_rm, base_repos_extd)

    base_main_repo = ""
    for base_repo in base_repos:
        if f"{project_name}/main" in base_repo.attrib['name']:
            base_main_repo = base_repo.attrib['name']
            base_main_rev = base_repo.attrib['revision']
            break
    base_project_main_repo_path, base_main_rev = load_repo(host, port, base_main_repo, base_main_rev, VERBOSE_OUTPUT, fetch=True)
    print(f"got: {base_main_repo}, {base_main_rev}")
    #base_project_main_entry = {'name': base_main_repo, 'revision': base_main_rev, 'path': f'layers/project-{project_name}'}
    #base_repos.append(base_project_main_entry)

    base_patches_repo = ""
    for base_repo in base_repos:
        if f"{project_name}/patches" in base_repo.attrib['name']:
            base_patches_repo = base_repo.attrib['name']
            base_patches_rev = base_repo.attrib['revision']
            break
    base_project_patches_repo_path, base_patches_rev = load_repo(host, port, base_patches_repo, base_patches_rev, VERBOSE_OUTPUT, fetch=True)
    print(f"got: {base_patches_repo}, {base_patches_rev}")
    #base_project_patches_entry = {'name': base_patches_repo, 'revision': base_patches_rev, 'path': 'patches'}
    #base_repos.append(base_project_patches_entry)

    # getting settings for overrided repos
    if manifest_commit_ref != None and len(manifest_commit_ref) > 0:
        commit = manifest_commit_ref.split('/')[-2]
        patchset = manifest_commit_ref.split('/')[-1]
        new_manifest_rev, new_manifest_branch, git_project = get_gerrit_rev(host, port, commit, patchset)
        if new_manifest_rev != base_project_rev:
            new_project_manifest_repo_path, new_manifest_rev = load_repo(host, port, project_manifest_repo, new_manifest_rev, VERBOSE_OUTPUT, commit=commit, patchset=patchset)
        else:
            new_project_manifest_repo_path = base_project_manifest_repo_path
        print(f"got: {project_manifest_repo}, {new_manifest_rev}")
        new_default_project_root, new_project_manifest_location, new_project_rev = projectManifestRetreiver.get_project_manifest_for_repo(new_manifest_branch, new_manifest_rev, True, manifest_commit_ref)
        projectOuputWriterNew = OutputWriter("{}/{}".format(output_path,"project_included_in_new_version"), host)
        projectOuputWriterNew.write_manifest_contents_html("patched__project_included_releases_{}_{}.html".format(new_manifest_branch, "new"), new_default_project_root)
        new_otp_branch_cmp = projectManifestRetreiver.get_otp_revision_from_manifest(new_default_project_root)
        print_header("Checking if new otp repo is referenced from project manifest...")
        if to_revision(host, port, OTP_MANIFEST_NAME, new_otp_branch) != to_revision(host, port, OTP_MANIFEST_NAME, new_otp_branch_cmp):
            print_header(f"ERROR: your given manifest commit reference {project_name} {project_manifest_repo}, does not contain the branch {new_otp_branch}!")
            abort_patching()
        else:
            print("Yes, reference is correct!")
        # preparing... all new repos
        new_project_manifest_entry_txt = manifest_project_template.format(project_manifest_repo, new_manifest_rev)
        new_project_manifest_entry = ET.fromstring(new_project_manifest_entry_txt)
        new_repos = [new_project_manifest_entry]
        new_repos.extend(new_default_project_root.findall("project"))
        new_repos.extend(new_default_project_root.findall("include-project"))
        new_repos.extend( new_default_otp_root.findall("include-project"))
        new_repos.extend( new_default_otp_root.findall("project"))
        new_repos.extend( new_otp_framework_root.findall("project"))
        new_repos.extend( new_otp_hal_root.findall("project"))
        # correct new repos...
        new_repos_rm = new_default_project_root.findall("remove-project")
        new_repos_extd = new_default_project_root.findall("extend-project")
        projectManifestRetreiver.remove_and_extend_projects(new_repos, new_repos_rm, new_repos_extd)
    else:
        # new project manifest equals base project manifest
        new_repos = base_default_project_root.findall("project")
        new_repos.extend(base_default_project_root.findall("include-project"))
        new_repos.extend(new_projects)
        new_repos_rm = base_default_project_root.findall("remove-project")
        new_repos_extd = base_default_project_root.findall("extend-project")
        projectManifestRetreiver.remove_and_extend_projects(new_repos, new_repos_rm, new_repos_extd)

    def update_commit(commit_ref, repo, comp_rev, repo_list):
        """update repo_list entry for repo name with new revision

        Args:
            commit_ref (str): commit reference
            repo (str): repo name
            comp_rev (str): revision to compare to
            repo_list (list): repo list to search for repo
        """
        commit = commit_ref.split('/')[-2]
        patchset = commit_ref.split('/')[-1]
        new_rev, new_branch, git_project = get_gerrit_rev(host, port, commit, patchset)
        if new_rev != comp_rev:
            new_project_repo_path, new_rev = load_repo(host, port, repo, new_rev, VERBOSE_OUTPUT, commit=commit, patchset=patchset, fetch=True)
        #else:
        #    new_project_repo_path = base_project_repo_path
        print(f"got: {repo}, {new_rev}")
        elements = [e for i, e in enumerate(repo_list) if e.attrib['name'] == repo]
        for elem in elements:
            print(f"Elem  {elem}")
            elem.attrib["revision"] = new_rev

    if main_commit_ref != None and len(main_commit_ref) > 0:
        update_commit(main_commit_ref, base_main_repo, base_main_rev, new_repos)

    if patches_commit_ref != None and len(patches_commit_ref) > 0:
        update_commit(patches_commit_ref, base_patches_repo, base_patches_rev, new_repos)

    # ensure all needed repos are loaded, so:
    for repo_list in base_repos, new_repos:
        for repo in repo_list:
            repo_name = repo.get('name')
            repo_rev = repo.get('revision')
            repo_rev = to_revision(host, port, repo_name, repo_rev)
            load_repo(host, port, repo_name, repo_rev, VERBOSE_OUTPUT)

    execute_patching(path_patched_base_repos, base_repos, project_name, cas_target_hw, hw_variant, additional_exports, args, VERBOSE_OUTPUT)
    execute_patching(path_patched_new_repos, new_repos, project_name, cas_target_hw, hw_variant, additional_exports, args, VERBOSE_OUTPUT)

    patched_base_repos = get_patched_repo_list(path_patched_base_repos, cas_target_hw)
    patched_new_repos = get_patched_repo_list(path_patched_new_repos, cas_target_hw)

    compare_patched_repos(project_name, workarea, args, path_patched_base_repos, patched_base_repos, base_version, \
                            path_patched_new_repos, patched_new_repos, new_version, VERBOSE_OUTPUT)

def main():
    """otp rebase helper for projects using two p1/project/otp/manifest versions
    """
    # get input and output file
    args = parseargs()
    VERBOSE_OUTPUT = False
    if args.verbose:
        VERBOSE_OUTPUT = True
    base_version=args.base_version
    #base_version_branch=args.base_branch
    new_version=args.new_version
    #new_version_branch=args.new_branch
    apply_patches = False
    cas_target_hw = None
    hw_variant = None
    additional_exports = None
    host = args.host_name
    port = args.gerrit_port
    if args.apply_patches:
        apply_patches = True
        cas_target_hw = args.cas_target_hw
        hw_variant = args.hw_variant
        if args.additional_exports:
            additional_exports = args.additional_exports
        #if args.additional_repos:
        #    additional_repos = [repo.strip() for repo in args.additional_repos.split(',')]
        project_name=args.project
        project_manifest_repo=args.prj_manifest
        base_mfst_version=args.base_mfst_version
        manifest_commit_ref=args.manifest_commit_ref
        main_commit_ref=args.main_commit_ref
        patches_commit_ref=args.patches_commit_ref

    repos_to_skip_compare = []
    if args.exclude:
        repos_to_skip_compare = [repo.strip() for repo in args.exclude.split(',')]
        print_header("Skipping: {}".format(repos_to_skip_compare))

    #clean output dir from old results:
    if os.path.exists(args.output_path):
        shutil.rmtree(args.output_path)

    # get informations for base repo version
    base_otp_branch = args.base_version
    manifestRetreiver = ManifestRetreiver(host, 'otp')
    base_ouputWriter = OutputWriter("{}/{}".format(args.output_path,"included_in_base_version"), host)
    base_includedReleases = IncludedReleases(manifestRetreiver, base_ouputWriter, 'otp', base_otp_branch, consider_included_mfsts=True)
    base_projects = base_includedReleases.processProjectManifest("base")
    base_otp_rev = base_includedReleases.getOtpRev()
    base_otp_manifest_location = base_includedReleases.getOtpManifestLocation()

    # get informations for new repo version
    new_otp_branch = args.new_version
    new_manifestRetreiver = ManifestRetreiver(host, 'otp')
    new_ouputWriter = OutputWriter("{}/{}".format(args.output_path,"included_in_new_version"), host)
    new_includedReleases = IncludedReleases(new_manifestRetreiver, new_ouputWriter, 'otp', new_otp_branch, consider_included_mfsts=True)
    new_projects = new_includedReleases.processProjectManifest("new")
    new_otp_rev = new_includedReleases.getOtpRev()
    new_otp_manifest_location = new_includedReleases.getOtpManifestLocation()

    # first of all make the comparison the the otp manifest repo:
    #otp_manifest_name = "p1/project/otp/manifest"
    pure_otp_manifest_name = OTP_MANIFEST_NAME.replace('/', '_') #[base_project_name.rfind('/')+1:]
    files_only_in_base_list, files_only_in_modified_list = compare_repo_versions(base_otp_manifest_location, new_otp_manifest_location, "{}/{}/".format(args.output_path,pure_otp_manifest_name))
    create_index_page("{}/{}/".format(args.output_path,pure_otp_manifest_name), OTP_MANIFEST_NAME, base_otp_rev, new_otp_rev, files_only_in_base_list, files_only_in_modified_list, new_otp_manifest_location)

    # print duplicates
    base_includedReleases.printDuplicates()
    new_includedReleases.printDuplicates()

    # compare content of project lists: compare repos which are in both, create lists for added or removed projects...
    compare_projects(base_projects, new_projects, repos_to_skip_compare, args, apply_patches, VERBOSE_OUTPUT)

    # if apply_patches was selected in the input mask, apply the patches to all used repos (copied versions), then compare the patched versions:
    if apply_patches == True:
        use_patches(host, port, project_name, args.output_path, project_manifest_repo, base_mfst_version, base_otp_branch, new_otp_branch,
                     base_includedReleases.getDefaultOtpRoot(), base_includedReleases.getOtpHalRoot(), base_includedReleases.getOtpFrameworkRoot(),
                     new_includedReleases.getDefaultOtpRoot(), new_includedReleases.getOtpHalRoot(), new_includedReleases.getOtpFrameworkRoot(),
                     manifest_commit_ref, main_commit_ref, patches_commit_ref,
                     cas_target_hw, hw_variant, additional_exports, args,
                     base_version, new_version, new_projects, VERBOSE_OUTPUT)

    # create main_index.html
    print_header("\nCreating MAIN INDEX PAGE...\n", 50)
    create_main_index_page(args.output_path, "rebase from {} to {}".format(base_otp_branch, new_otp_branch))

    # for local builds only: call merge tool to merge otp main with drt15 main branch
    # this code is the only DRt15 specific!
    #if args.merge:
    #    if 'drt15' in args.target:
    #        merge_main_DRT15(args, new_default_otp_root, otp_main_repo)
    #    else:
    #        print("Sorry merge for {} is not implemented!".format(args.target))
    #
    # TODO: cleanup WA!
    # clean input dirs remark: not cleaning up will increase the speed for the next run very much!
    """
    shutil.rmtree(main_base_repo_path)
    if main_base_repo_path != main_new_repo_path:
        shutil.rmtree(main_new_repo_path)
    shutil.rmtree(build_base_repo_path)
    if build_base_repo_path != build_new_repo_path:
        shutil.rmtree(build_new_repo_path)
    shutil.rmtree(specs_base_repo_path)
    if specs_base_repo_path != specs_new_repo_path:
        shutil.rmtree(specs_new_repo_path)
    """


if __name__ == '__main__':
    main()
