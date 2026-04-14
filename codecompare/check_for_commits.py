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

""" check a manifest for a commit list """

__author__ = "Kurt Hanauer"
__version__ = "0.1.0"
__date__ = "2023-10-12"
__credits__ = "Copyright (C) 2023 Continental Automotive GmbH"

#######################################################################
#
# Module-History
#  Date        Author               Reason
#  2023-10-23  Kurt Hanauer         Initial version
#######################################################################
import os
import sys
import argparse
import shutil
import xml.etree.ElementTree as ET
from repo_versions_compare import load_repo, launch_command, print_header, get_gerrit_rev
from find_included_releases import ManifestRetreiver, OutputWriter
import csv

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
    parser = argparse.ArgumentParser(description="check a manifest for a commit list")
    parser.add_argument('-p', '--project', action='store', help="Project name", default="otp")
    parser.add_argument('-b', '--branch', action='store', help="repo branch/version for compare")
    parser.add_argument('-f', '--file', action='store', help="file containing commits to check")
    parser.add_argument('--host', action='store', dest="host_name", help="gerrit host name to connect to (for git commands and output links)", default="buic-scm-ias.contiwan.com")
    parser.add_argument('--port', action='store', dest="gerrit_port", help="gerrit port", default = "29418")
    parser.add_argument('--output_path', action='store', help="Output path for reslut list (defaults to './output')", default="output")
    parser.add_argument('--verbose', action='store_true', help="verbose output")

    args=parser.parse_args()
    if (args.project==None) or (args.branch==None) or args.file==None:
        parser.print_help()
        sys.exit(1)
    #print(args)
    return args

def main():
    """check a manifest for a given commit list
    """
    # get input and output file
    args = parseargs()
    VERBOSE_OUTPUT = False
    if args.verbose:
        VERBOSE_OUTPUT = True
    project=args.project
    branch=args.branch
    file = args.file
    host = args.host_name
    port = args.gerrit_port
    output_path = args.output_path

    # get the manifest, where are entries to check
    manifestRetreiver = ManifestRetreiver(host, project)
    ouputWriter = OutputWriter("{}/{}".format(args.output_path,"included_in_version"), host)
    otp_branch = branch
    default_otp_root, otp_manifest_location, otp_rev = manifestRetreiver.get_otp_manifest_for_repo(otp_branch)
    ouputWriter.write_manifest_contents_html("included_releases_otp_{}.html".format(otp_branch), default_otp_root)
    otp_framework_revision, otp_framework_upstream = manifestRetreiver.get_otp_framework_revision_from_manifest(default_otp_root)
    otp_framework_root = manifestRetreiver.get_otp_framework_manifest_for_repo(otp_framework_upstream, otp_framework_revision)
    ouputWriter.write_manifest_contents_html("included_releases_otp_framework_{}_{}.html".format(otp_framework_upstream, otp_framework_revision), otp_framework_root )
    otp_hal_revision, otp_hal_upstream = manifestRetreiver.get_otp_hal_revision_from_manifest(default_otp_root)
    otp_hal_root = manifestRetreiver.get_otp_hal_manifest_for_repo(otp_hal_upstream, otp_hal_revision)
    ouputWriter.write_manifest_contents_html("included_releases_otp_hal_{}_{}.html".format(otp_hal_upstream, otp_hal_revision), otp_hal_root )

    # get all repo names from otp_root(s)
    projects = []
    projects.extend( default_otp_root.findall("include-project"))
    projects.extend( default_otp_root.findall("project"))
    projects.extend( otp_framework_root.findall("project"))
    projects.extend( otp_hal_root.findall("project"))

    commits_to_check = {}
    with open(file, 'r') as input_file:
        lines = input_file.readlines()

    ticket_url_tmpl = "https://jira.vni.agileci.conti.de/browse/{}"

    for line in lines:
        if ',' in line:
            commit_link = line.split(',')[0]
            commit = commit_link.rsplit('/')[-1]
            commit_link = ouputWriter.create_excel_link(commit_link, commit)
            ticket = line.split(',')[1].strip()
            revision, commit_branch, git_project = get_gerrit_rev(host, port, commit)
            revision_link = ouputWriter.create_excel_link(ouputWriter.create_url_for_revision(git_project, revision),revision)
            ticket_link = ouputWriter.create_excel_link(ticket_url_tmpl.format(ticket), ticket)

            print(f"Commit {commit} for ticket {ticket} is rev {revision} on branch {commit_branch}, project {git_project}!")
            entry = {'commit':f'{commit}','ticket':f'{ticket_link}','revision':f'{revision}','branch':f'{commit_branch}','project':f'{git_project}','referenced':'No','commit_link':f'{commit_link}','revision_link':f'{revision_link}'}
            commits_to_check[commit] = entry

    repos_to_check = []
    for commit_key in commits_to_check.keys():
        print(commit_key)
        repos_to_check.append(commits_to_check[commit_key]['project'])
    print(repos_to_check)
    repos_to_check = list(set(repos_to_check))
    print(f"Repos to check are: {repos_to_check}")

    repos_in_manifest = []
    repos_not_referenced = []
    for repo_to_check in repos_to_check:
        project_to_check = repo_to_check
        print(f"checking for {project_to_check}")
        bFound = False
        for manifest_repo in projects:
            project_in_manifest = manifest_repo.attrib["name"]
            print(f"comparing {project_to_check} to {project_in_manifest}")
            if project_to_check == project_in_manifest:
                print("Hit!")
                bFound = True
                break
        if bFound == True:
            repos_in_manifest.append(project_to_check)
        else:
            repos_not_referenced.append(project_to_check)

    print_header(f"repos in manifest: {repos_in_manifest}")
    print_header(f"repos not in manifest: {repos_not_referenced}")

    git_logs = []
    # load project repos
    for repo in repos_in_manifest:
        for manifest_repo in projects:
            if repo == manifest_repo.attrib["name"]:
                repo_path, revision = load_repo(host, port, repo, manifest_repo.attrib["revision"].rsplit('/')[-1], VERBOSE_OUTPUT, fetch=True)
                #searching git logs:
                get_logs_cmd = f"cd {repo_path}; git log --oneline --no-abbrev-commit --sparse --full-history"
                ret_code, log_contents = launch_command(get_logs_cmd, False)
                if ret_code == 0:
                    for commit_key in commits_to_check.keys():
                        if commits_to_check[commit_key]['revision'] in str(log_contents):
                            print_header(f"Hit for {commit_key}!")
                            commits_to_check[commit_key]['referenced'] = "Yes"

    with open(f"{output_path}/commit_info.csv","w") as output_file:
        field_names = [ "commit","ticket","revision","branch","project","referenced","commit_link","revision_link" ]
        csv_writer = csv.DictWriter(output_file, field_names, dialect="excel", delimiter=",")
        csv_writer.writeheader()
        #output_file.write("commit,ticket,revision,branch,project,referenced,commit_link,revision_link\n")
        for commit_key in commits_to_check.keys():
            #output_file.write(f"{commit_key},{commits_to_check[commit_key]['ticket']},{commits_to_check[commit_key]['revision']},{commits_to_check[commit_key]['branch']},{commits_to_check[commit_key]['project']},{commits_to_check[commit_key]['referenced']},{commits_to_check[commit_key]['commit_link']},{commits_to_check[commit_key]['revision_link']}\n")
            csv_writer.writerow(commits_to_check[commit_key])


if __name__ == '__main__':
    main()
