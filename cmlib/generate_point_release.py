# *****************************************************************************
# *
# * (c) 2023 Continental Automotive Systems, Inc., all rights reserved
# *
# * All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# * Any reproduction of this material without written consent from
# * Continental Automotive Systems, Inc. is strictly forbidden.
# *
# * Filename:    generate_point_release.py
# *
# * Description: Main script for generate a point release
# *
# * Revision History:
# *
# *  CQ#    Author           Date          Description of Change(s)
# *  -----  -------------    ----------    ------------------------------------
# *         uidu3800         2023-01-25    Init version
# *
# *****************************************************************************


import shutil
import os
import argparse

from manifest import Manifest
from point_release_gerrit import Gerrit

DEFAULT_GERRIT_API_URL = "https://buic-scm-dpk.contiwan.com:8443/a/"


def get_gerrit_credentials_from_gtoken_file(url):
    """
    The get_gerrit_credentials_from_gtoken_file function is used to retrieve the credentials from a gtoken file.
    The function takes one argument, which is the url of the gerrit api server with port. E.g -> "https://buic-scm-fr.contiwan.com:8443/a/".
    The function then opens and reads the gtoken file located in ~/.gerrit/gtoken, and splits each line into tokens separated by semicolons (;).
    It then searches for a token that contains the url of our gerrit server, and returns it as a dictionary with keys: user, key.

    :param url: gerrit api url
    :return: A dict with the following keys: user; user_required; key; key_required
    """
    gtoken_file_path = os.path.join(os.path.expanduser("~"), ".gerrit", "gtoken")
    with open(gtoken_file_path, "r") as gtoken_file:
        gtoken_content = gtoken_file.readlines()
    gtoken_url = url.split(":")[1].split("/")[-1]
    for token in gtoken_content:
        if gtoken_url in token:
            token_splitted = token.strip().split(";")
            return {
                "user": token_splitted[2],
                "user_required": False,
                "key": token_splitted[3],
                "key_required": False
            }
    else:
        return {"user": None, "user_required": True, "key": None, "key_required": True}


user_key_dict = get_gerrit_credentials_from_gtoken_file(DEFAULT_GERRIT_API_URL)

# get arguments
parser = argparse.ArgumentParser()
parser.add_argument("--gerrit_api_url", dest="gerrit_api_url", type=str, default=DEFAULT_GERRIT_API_URL,
                    help="The main api url of gerrit => e.g: https://buic-scm-rbg.contiwan.com:8443/a/", required=False)
parser.add_argument("--gerrit_user", dest="gerrit_user", type=str, default=user_key_dict["user"],
                    help="The user to authenticate against gerrit", required=user_key_dict["user_required"])
parser.add_argument("--gerrit_api_key", dest="gerrit_api_key", type=str, default=user_key_dict["key"],
                    help="The api key to authenticate against gerrit", required=user_key_dict["key_required"])
parser.add_argument("--baseline_version", dest="baseline_version", type=str,
                    help="The repo url for the base repo init (e.g.: 'conmod-sa515m-3.3.265.1'", required=True)
parser.add_argument("--new_baseline", dest="new_baseline", type=str,
                    help="The new release branch", required=True)
parser.add_argument("--workspace", dest="workspace", type=str,
                    help="The working directory for the script", required=True)
parser.add_argument("--list_of_patches", dest="list_of_patches", type=list,
                    help="A list of patches => e.g. => ['https://buic-scm-rbg.contiwan.com:8443/#/c/2933582/', 'https://buic-scm-rbg.contiwan.com:8443/#/c/2898096/', 'https://buic-scm-sgp.contiwan.com:8443/#/c/2948388/']'",
                    required=True)

args = parser.parse_args()

# gerrit_args
gerrit_url = args.gerrit_api_url
gerrit_user = args.gerrit_user
gerrit_api_key = args.gerrit_api_key
BASELINE_VERSION = args.baseline_version
NEW_BASELINE = args.new_baseline
LIST_OF_PATCHES = args.list_of_patches


MAIN_MANIFEST_REPO_URL = "buic-scm:p1/project/otp/manifest"
OOC_SW_TOOLS_REPO_URL = "buic-scm:IIC_SW_Tools/git-repo"
MAIN_WORKING_DIR = args.workspace
#Main_Manifest_file = os.path.join(".repo", "manifests", "default.xml")
MAIN_MANIFEST_FILE = os.path.join(".repo", "manifests", "default.xml")
MAIN_MANIFEST_FILE_WITH_PATH = os.path.join(MAIN_WORKING_DIR, MAIN_MANIFEST_FILE)


def run_cmd(cmd, in_path=None, popen=False, read_lines=False):
    """
    The run_cmd function runs a command in the shell.

    :param cmd: Execute the command
    :param in_path=None: Specify the path of the command
    :param popen=False: Specify that the command is executed in a shell
    :param read_lines=False: Read the result as a string instead of an array
    :return: The status code of the command
    """
    if in_path:
        cmd = "cd {} && {}".format(in_path, cmd)

    print("Command => {}".format(cmd))
    if popen:
        res = os.popen(cmd)
        if read_lines:
            res_content = res.readlines()
        else:
            res_content = res.read()
        status = res.close()
        if status:
            raise Exception("The status code of '{}' is {}".format(cmd, status))
        else:
            return res_content
    else:
        status_code = os.system(cmd)
        if status_code != 0:
            raise Exception("The status code of the cmd => {} != 0".format(cmd))
        return status_code


def manifest_init_sync():
    """
    The manifest_init_sync function removes the current manifest directory, creates a new one and syncs it.
    It is used to initialize the manifest repository for a new build.

    :return: None
    """
    # remove "manifest" folder, if exists
    if os.path.exists(MAIN_WORKING_DIR):
        shutil.rmtree(MAIN_WORKING_DIR)

    # create working directory
    run_cmd("mkdir {}".format(MAIN_WORKING_DIR))

    # repo init
    run_cmd("repo init -u {} -b {} -g all --repo-branch=stable-conti --repo-url={} --no-repo-verify".format(MAIN_MANIFEST_REPO_URL,
                                                                                                            BASELINE_VERSION,
                                                                                                            OOC_SW_TOOLS_REPO_URL),
            MAIN_WORKING_DIR)

    # repo sync (2x times)
    for x in range(2):
        run_cmd("repo sync --force-sync --detach --force-broken -j 8", MAIN_WORKING_DIR)

def get_patch_data(gerrit_obj):
    """
    The get_patch_data function takes a list of URLs and returns a list of dictionaries containing the data for each patch.
    The function uses the Gerrit object to get the change_id from each URL, then uses that ID to get information about that specific
    patch. The function then appends this information into a list of dictionaries, which is returned.

    :param gerrit_obj: Pass the gerrit object to the function
    :return: A list of dictionaries
    """
    patches = []
    for url in LIST_OF_PATCHES:
        print("\n" * 3)
        url_splitted = url.split("/")
        for x in range(len(url_splitted) - 1, 0, -1):
            if url_splitted[x].isnumeric():
                change_id = url_splitted[x]
                break
        print(change_id)
        data = gerrit_obj.get_change_information(change_id)
        patches.append(data)
        for element in data:
            print("{} => {}".format(element, data[element]))
    return patches


def get_act_revision_id(project_path):
    """
    The get_act_revision_id function returns the revision ID of the current project.
    The function takes one argument, which is a string containing the path to your project.
    It then runs a git command that returns only the SHA-ID of HEAD in your repository, and prints it out.

    :param project_path: Specify the path to the project
    :return: The revision id of the current branch
    """
    # get revision ID
    revision_cmd = "git rev-parse HEAD"
    print("#\n" * 3)
    revision_id_list = run_cmd(revision_cmd, project_path, popen=True, read_lines=True)
    if len(revision_id_list) != 1:
        raise Exception("There is no explicit revision id in Project => {}".format(revision_id_list))
    else:
        revision_id = revision_id_list[0].strip()
        print(revision_id)
        return revision_id


def apply_patches(gerrit_obj, manifest_obj):
    """
    The apply_patches function :
        1. Creates a Manifest object and prints the needed project from the manifest
        2. Runs cherry-pick cmd
        3. Runs git push cmd


    :param gerrit_obj: Get the data from gerrit
    :param manifest_obj: Get the project data from the manifest
    :return: The manifest object with the new revision and upstream
    """
    # Get all data from the LIST_OF_PATCHES (id, project, branch, change_id, cherry_pick)
    patches_list = get_patch_data(gerrit_obj)

    for patch in patches_list:
        print("#\n"*2)
        print(patch)

        # create a Manifest object and print the needed project from the manifest
        project_key = "{}{}{}".format(patch["project"], Manifest.PROJ_NAME_SEPARATOR, patch["branch"])
        manifest_project_data = manifest_obj.projects[project_key]
        manifest_print_data = "{} => {}".format(project_key, manifest_project_data)
        print("{} {} {}".format("#" * 2, "manifest_data =>", manifest_print_data))

        # run cherry-pick cmd
        project_path = os.path.join(MAIN_WORKING_DIR, manifest_project_data["path"])
        print("{} {} {}".format("#"*2, "project_path =>", project_path))
        print("#"*140)
        run_cmd(patch["cherry_pick"], project_path)

        # run git push
        push_cmd = "git push origin HEAD:refs/heads/{}".format(NEW_BASELINE)
        run_cmd(push_cmd, project_path)

        # get revision ID
        revision_id = get_act_revision_id(project_path)

        # Change 'revision_id' and 'upstream' in Manifest
        print("Change manifest")
        print(manifest_project_data)
        manifest_file = manifest_project_data["manifest_file"]
        new_revision = revision_id
        new_upstream = "refs/heads/{}".format(NEW_BASELINE)
        manifest_obj.change_revision_and_upstream_of_manifest(manifest_file, manifest_project_data, new_revision, new_upstream)

    return manifest_obj


def commit_and_push_manifest_files_changes_worker(manifest_obj, manifest_file, gerrit_obj=False, main_manifest=False):
    """
    The commit_and_push_manifest_files_changes_worker function :
        - Takes a manifest object and the path to the manifest file as arguments.
        - Checks if there are any modified files in the given manifest directory. If so, it creates a commit message for each of them and commits them with git.
        - Pushes all changes to gerrit using git push command.

    :param manifest_obj: Get the data from the main manifest file
    :param manifest_file: Get the revision and upstream of this manifest on the main_manifest_file
    :param gerrit_obj=False: Run the function in a thread
    :param main_manifest=False: Commit the manifest files changes
    :return: None
    """
    print("Manifest file => {}".format(manifest_file))
    manifest_path = manifest_file.rsplit("/", 1)[0]
    print("Manifest path => {}".format(manifest_path))
    return_string = run_cmd("git status", manifest_path, popen=True)
    if "modified:" in return_string:
        print("\nThere are modified files for commit\n")
        print("The git status string => {}".format(return_string))

        if main_manifest:
            # Create commit message
            print("#" * 14)
            print("### Create the commit message")
            print("#" * 14)
            print("The manifest path => {}".format(manifest_path))
            print("\n" * 3)
            print("Commit Message")

            # Set the release version
            new_release = NEW_BASELINE
            print("new release version => {}".format(new_release))

            # Create commit message
            commit_msg = "{} baseline".format(new_release)
            print("#" * 3)
            print("Commit Message => \n{}".format(commit_msg))
            print("#" * 3)
        else:
            # get next version number for the manifest
            print(manifest_obj.manifest_files)
            print(manifest_obj.main_manifest_inclue_projects_data[manifest_file])
            previous_baseline = manifest_obj.main_manifest_inclue_projects_data[manifest_file]["upstream"]
            project = manifest_obj.main_manifest_inclue_projects_data[manifest_file]["name"]
            print("previous baseline => {}".format(previous_baseline))

            # Create commit message
            print("#" * 14)
            print("### Create the commit message")
            print("#" * 14)
            print("The manifest path => {}".format(manifest_path))
            print("\n" * 3)
            print("Commit Message")

            # Get next release number
            new_release = gerrit_obj.get_latest_number_for_branch(project, previous_baseline)
            print("new release version => {}".format(new_release))

            commit_msg = "{} baseline".format(new_release)
            last_commit_msg_cmd_online = "git log -1 --pretty=%B"
            last_commit_msg = run_cmd(last_commit_msg_cmd_online, manifest_path, popen=True, read_lines=True)
            print(last_commit_msg)
            commit_msg += "\n\n"
            commit_msg += "STARTED_BY: {}\n".format(NEW_BASELINE)
            commit_msg += "PREVIOUS_BASELINE: {}\n".format(previous_baseline)

            print("#" * 3)
            print("Commit Message => \n{}".format(commit_msg))
            print("#" * 3)

        # git commit with the commit message
        run_cmd("git commit -a -m '{}'".format(commit_msg), manifest_path)

        # git push changes
        new_upstream = "refs/heads/{}".format(new_release)
        push_cmd = "git push origin HEAD:{}".format(new_upstream)
        run_cmd(push_cmd, manifest_path)

        if not main_manifest:
            # update the revision and upstream of this manifest on the MAIN_MANIFEST_FILE
            new_revision = get_act_revision_id(manifest_path)
            manifest_file_name = manifest_file.rsplit("/", 1)[1]
            print(manifest_file_name)
            manifest_obj.change_revision_and_upstream_of_included_manifest_files_in_main_manifest_file(MAIN_MANIFEST_FILE_WITH_PATH,
                                                                                                       manifest_file_name,
                                                                                                       new_revision,
                                                                                                       new_upstream)
    else:
        print("There are no changes on {}".format(manifest_path))
    print("#" * 7)


def commit_and_push_manifest_files_changes(manifest_obj, gerrit_obj):
    """
    The commit_and_push_manifest_files_changes function :
        1. repo sync in workdir
        2. Commit & Push Changes in manifest files to gerrit

    :param manifest_obj: Get the manifest_files list
    :param gerrit_obj: Push the changes to gerrit
    :return: :
    """
    # Commit and push Changes in manifest files to gerrit
    # 1. repo sync in workdir
    run_cmd("repo sync --force-sync --detach -j 8", MAIN_WORKING_DIR)

    # 2. Commit & Push
    print("#"*21)
    print("### Commit & Push")
    print("#" * 21)

    for manifest_file in manifest_obj.manifest_files:
        if manifest_file != MAIN_MANIFEST_FILE_WITH_PATH:
            commit_and_push_manifest_files_changes_worker(manifest_obj, manifest_file, gerrit_obj)

    commit_and_push_manifest_files_changes_worker(manifest_obj, MAIN_MANIFEST_FILE_WITH_PATH, main_manifest=True)


if __name__ == "__main__":
    manifest_init_sync()
    print("\n"*7)

    # Create a gerrit api communication object
    gerrit_obj = Gerrit(gerrit_url, gerrit_user, gerrit_api_key)
    # create manifest_obj
    manifest_obj = Manifest(MAIN_WORKING_DIR, MAIN_MANIFEST_FILE)

    # Apply all patches
    apply_patches(gerrit_obj, manifest_obj)

    # Commit and push alle changes in all manifest files, which are modified
    commit_and_push_manifest_files_changes(manifest_obj, gerrit_obj)
