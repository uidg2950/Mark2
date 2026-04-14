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

""" project code compare
compares two FIXED repo revisions of two different project manifest versions (branch/tag)
"""

__author__ = "Kurt Hanauer"
__version__ = "0.1.0"
__date__ = "2023-09-27"
__credits__ = "Copyright (C) 2023 Continental Automotive GmbH"

#######################################################################
#
# Module-History
#  Date        Author               Reason
#  2023-09-27  Kurt Hanauer         Initial version --> based on otp_rebase_helper.py
#######################################################################

import re
import os
import sys
import argparse
import shutil
from repo_versions_compare import compare_patched_repos, compare_repo_versions, create_index_page, get_patched_repo_list, print_header, execute_patching, compare_projects
from find_included_releases import ManifestRetreiver, OutputWriter, IncludedReleases
from code_compare_utils import GERRIT_REF_REGEX, PATCH_PATHS_REGEX_LIST, create_main_index_page, install_repo_tool, print_header, OTP_PROJECT, OTP_MANIFEST_NAME

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
    parser = argparse.ArgumentParser(description="project code compare using two tagged project manifest versions")
    parser.add_argument('-p', '--project', action='store', help="Project name", default="drt15")
    parser.add_argument('-m', '--manifest_repo', action='store', help="Project name", default="drt15/manifest")
    parser.add_argument('-b', '--base_version', action='store', help="Base version tag or commit reference for compare")
    parser.add_argument('-n', '--new_version', action='store', help="New version tag or commit reference for compare")
    parser.add_argument('-x', '--base_branch', action='store', help="Base branch for compare")
    parser.add_argument('-y', '--new_branch', action='store', help="New branch for compare")
    parser.add_argument('--host', action='store', dest="host_name", help="gerrit host name to connect to (for git commands and output links)", default="buic-scm-ias.contiwan.com")
    parser.add_argument('--port', action='store', dest="gerrit_port", help="gerrit port", default = "29418")
    parser.add_argument('--output_path', action='store', help="Output path for html pages (defaults to './html')", default="html")
    parser.add_argument('--verbose', action='store_true', help="verbose output")
    parser.add_argument('--exclude', action='store', help="repo names to exclude (comma seperated list)", default=None)
    parser.add_argument('--apply_patches', action='store_true', help="apply project patches to OTP/FERMI repos")
    parser.add_argument('--cas_target_hw', action='store', help="needed to apply patches")
    parser.add_argument('--hw_variant', action='store', help="needed to apply patches")
    parser.add_argument('--additional_exports', action='store', help="additional exports as comma seperated list (project specific, as needed to apply patches")

    args=parser.parse_args()
    if (args.base_version==None) or (args.new_version==None) or (args.base_branch==None) or (args.new_branch==None):
        parser.print_help()
        sys.exit(1)
    if args.apply_patches and not args.cas_target_hw:
        print("Parameter --cas_target_hw is needed for --apply_patches !")
        parser.print_help()
        sys.exit(1)
    #print(args)
    return args

def check_for_commit_reference(version_tag):
    """check if the given tag is a commit reference and set needed parameters accordingly

    Args:
        version_tag (str): version tag or commit reference

    Returns:
        str|None: version tag or None
        str|none: commit reference or None
        boolean: needed to consider included manifests (needed for commit ref)
    """
    consider_included_mfsts = False
    commit_ref = None
    tag_re = re.compile(GERRIT_REF_REGEX)
    if tag_re.fullmatch(version_tag) != None:
        print("tag for base_version is a commit reference! Considering the commit!")
        commit_ref = version_tag
        version_tag = None
        consider_included_mfsts = True
    return version_tag, commit_ref, consider_included_mfsts

def main():
    """main function for project code compare
    compares two FIXED repo revisions of two different project manifest versions (branch/tag)
    A commit reference can also be given as 'tag' parameter. This manifest content does not need to be fixed then
    """
    # get input and output file
    args = parseargs()
    VERBOSE_OUTPUT = False
    if args.verbose:
        VERBOSE_OUTPUT = True
    project_name=args.project
    project_manifest_repo=args.manifest_repo
    # force repo name if 'otp'  was selected:
    if project_name == OTP_PROJECT:
        project_manifest_repo = OTP_MANIFEST_NAME
    base_version_tag=args.base_version
    base_version_branch=args.base_branch
    new_version_tag=args.new_version
    new_version_branch=args.new_branch
    apply_patches = False
    cas_target_hw = None
    hw_variant = None
    additional_exports = None
    if args.apply_patches:
        apply_patches = True
        cas_target_hw = args.cas_target_hw
        hw_variant = args.hw_variant
        if args.additional_exports:
            additional_exports = args.additional_exports

    # TEMPORARY setting. This will skip the basic full repo compare to safe some time...
    debug_patches = False

    repos_to_skip_compare = []
    if args.exclude:
        repos_to_skip_compare = [repo.strip() for repo in args.exclude.split(',')]
        print_header("Skipping: {}".format(repos_to_skip_compare))

    #install repo tool
    install_repo_tool()

    #clean output dir from old results:
    if os.path.exists(args.output_path):
        shutil.rmtree(args.output_path)

    #check, if base_version_tag and/or new_version_tag are tags or commit refs:
    base_version_tag, base_commit_ref, base_consider_included_mfsts = check_for_commit_reference(base_version_tag)
    new_version_tag, new_commit_ref, new_consider_included_mfsts = check_for_commit_reference(new_version_tag)
    # consider hal and framework manifests in case this is an 'otp' project:
    if project_name == OTP_PROJECT:
        base_consider_included_mfsts = True
        new_consider_included_mfsts = True

    # get informations for base repo version
    manifestRetreiver = ManifestRetreiver(args.host_name, project_name, args.gerrit_port, project_manifest_repo)
    base_ouputWriter = OutputWriter("{}/{}".format(args.output_path,"included_in_base_version"), args.host_name)
    base_includedReleases = IncludedReleases(manifestRetreiver, base_ouputWriter, project_name, base_version_branch, base_version_tag, base_consider_included_mfsts, base_commit_ref)
    base_projects = base_includedReleases.processProjectManifest("base")
    base_project_rev = base_includedReleases.getProjectRev()
    base_project_manifest_location = base_includedReleases.getProjectManifestLocation()
    if project_name != OTP_PROJECT:
        base_otp_rev = base_includedReleases.getOtpRev()
        base_otp_manifest_location = base_includedReleases.getOtpManifestLocation()

    # get informations for new repo version
    new_ManifestRetreiver = ManifestRetreiver(args.host_name, project_name, args.gerrit_port, project_manifest_repo)
    new_ouputWriter = OutputWriter("{}/{}".format(args.output_path,"included_in_new_version"), args.host_name)
    new_includedReleases = IncludedReleases(new_ManifestRetreiver, new_ouputWriter, project_name, new_version_branch, new_version_tag, new_consider_included_mfsts, new_commit_ref)
    new_projects = new_includedReleases.processProjectManifest("new")
    new_project_rev = new_includedReleases.getProjectRev()
    new_project_manifest_location = new_includedReleases.getProjectManifestLocation()
    if project_name != OTP_PROJECT:
        new_otp_rev = new_includedReleases.getOtpRev()
        new_otp_manifest_location = new_includedReleases.getOtpManifestLocation()

    # first of all make the comparison the the project manifest repo:
    pure_project_manifest_name = project_manifest_repo.replace('/', '_') #[base_project_name.rfind('/')+1:]
    if base_project_rev !=  new_project_rev:
        print(f"Comparing project {project_name} manifest repos for {pure_project_manifest_name}")
        files_only_in_base_list, files_only_in_modified_list = compare_repo_versions(base_project_manifest_location, new_project_manifest_location, "{}/{}/".format(args.output_path, pure_project_manifest_name))
        create_index_page("{}/{}/".format(args.output_path, pure_project_manifest_name), pure_project_manifest_name, base_project_rev, new_project_rev, files_only_in_base_list, files_only_in_modified_list, new_project_manifest_location)
    else:
        print(f"No differences found for project {project_name} manifest repos for {pure_project_manifest_name}")

    # next make the comparison the the otp manifest repo:
    if project_name != OTP_PROJECT:
        otp_manifest_name = OTP_MANIFEST_NAME
        pure_otp_manifest_name = otp_manifest_name.replace('/', '_') #[base_project_name.rfind('/')+1:]
        if base_otp_rev != new_otp_rev:
            print(f"Comparing otp manifest repos for {pure_otp_manifest_name}")
            files_only_in_otp_base_list, files_only_in_otp_modified_list = compare_repo_versions(base_otp_manifest_location, new_otp_manifest_location, "{}/{}/".format(args.output_path,pure_otp_manifest_name))
            create_index_page("{}/{}/".format(args.output_path, pure_otp_manifest_name), otp_manifest_name, base_otp_rev, new_otp_rev, files_only_in_otp_base_list, files_only_in_otp_modified_list, new_otp_manifest_location)
        else:
            print(f"No differences found for otp manifest repos for {pure_otp_manifest_name}")

    # print duplicates
    base_includedReleases.printDuplicates()
    new_includedReleases.printDuplicates()

    # compare the whole project lists...
    if debug_patches == False:
        compare_projects(base_projects, new_projects, repos_to_skip_compare, args, apply_patches, VERBOSE_OUTPUT)

    # if apply_patches was selected in the input mask, apply the patches to all used repos (copied versions), then compare the patched versions:
    if apply_patches == True:
        print_header("\nStarting patching...\n", 50)
        workarea = os.getcwd()
        path_patched_base_repos = "patched_base_repos"
        path_patched_new_repos = "patched_new_repos"
        execute_patching(path_patched_base_repos, base_projects, project_name, cas_target_hw, hw_variant, additional_exports, args, VERBOSE_OUTPUT)
        execute_patching(path_patched_new_repos, new_projects, project_name, cas_target_hw, hw_variant, additional_exports, args, VERBOSE_OUTPUT)

        patched_base_repos = get_patched_repo_list(path_patched_base_repos, cas_target_hw)
        patched_new_repos = get_patched_repo_list(path_patched_new_repos, cas_target_hw)

        compare_patched_repos(project_name, workarea, args, path_patched_base_repos, patched_base_repos, base_version_tag, \
                              path_patched_new_repos, patched_new_repos, new_version_tag, VERBOSE_OUTPUT)

    # create main_index.html
    print_header("\nCreating MAIN INDEX PAGE...\n", 50)
    create_main_index_page(args.output_path, "{} code compare from {}:{} to {}:{}".format(project_name, base_version_branch, base_version_tag, new_version_branch, new_version_tag))

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
