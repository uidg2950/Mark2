import os
import subprocess
import sys
import requests
import json
from .settings import *
from helper.credentials_keyring import get_password
from keyring_variables import *

# This is requiered due python 3 doesn't support relative references
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
cm_root_dir = os.path.dirname(parentdir)
sys.path.append(cm_root_dir)

from cmlib import artifactory

def create_token():
    """
    The create_token function creates a token for the user to use in order to access Klocwork.
    It does this by running the kwauth command from within the klocwork bin folder.

    :return: None
    """
    kwserver = "https://dpas007x.dp.us.conti.de:8092"
    # kwserver = "https://dpas007x.qh.us.conti.de:8092"
    kwpath = r"\\cw01.contiwan.com\wetp\did65022\SCCWin10\klocwork\User\21.4\bin"

    login_path = r"{}\kwauth --url {}".format(kwpath, kwserver)
    subprocess.run(login_path.split())

def get_builds(baseline_version, release_id):
    """
    check for existing klockworkresults in
    upload_artifacts "${WORKSPACE}" "${RELEASE_ID}" "${KLOCWORK_BUILD}/Test_Results" "kw_metrics.json"
    first. If there is nothing, gather the results from the kw server
    """
    result_json = get_builds_from_test_results(baseline_version, release_id)
    if result_json == {}:
        result_json = get_builds_from_kw_server()
    return result_json

def get_builds_from_test_results(baseline_version, release_id):
    result_json = {}
    server_file_path = "{}/Test_Results/kw_metrics.json".format(baseline_version)
    kw_file_meta = artifactory.get_metainfo(server_file_path, release_id = release_id)
    if kw_file_meta != None:
        work_area = os.environ['WORKSPACE']
        destination_path = os.path.join(work_area, "kw_metrics")
        os.makedirs(destination_path, exist_ok=True)
        destination_path = os.path.join(destination_path, "kw_metrics.json")
        artifactory.download_artifact(server_file_path, destination_path, release_id = release_id)
        with open(destination_path, "r") as infile:
            result_json = json.load(infile)
            print(result_json)
    return result_json

def get_builds_from_kw_server():
    """
    The get_builds function returns a dictionary of build IDs and their associated data.
    The function takes no arguments, but requires that the user has already configured
    the Klocwork server URL, user name, project name and token in the settings.py file.

    :return: A dictionary of the builds
    """
    data = {
        "user": get_password(SERVICE_NAME, klocwork["user"]),
        "project": klocwork["project"],
        "ltoken": get_password(SERVICE_NAME, klocwork["token"]),
        "action": "builds"
    }

    result = requests.post(klocwork["url"], headers=klocwork["header"], data=data, verify=False)
    result_text = result.text.split("\n")
    result_json = {}
    for element in result_text:
        if element != "":
            element_json = json.loads(element)
            result_json.update({element_json["id"]: element_json})

    ids = []
    for id_tmp in result_json.keys():
        ids.append(int(id_tmp))
    return result_json


def get_query(query):
    """
    The get_query function takes a query as an argument and returns a dictionary of the results.
    The get_query function is used to search for issues in Klocwork.

    :param query: Search for a specific string in the database
    :return: A dictionary of dictionaries
    """
    data = {
        "user": get_password(SERVICE_NAME, klocwork["user"]),
        "project": klocwork["project"],
        "ltoken": get_password(SERVICE_NAME, klocwork["token"]),
        "action": "search",
        "query": query
    }

    result = requests.post(klocwork["url"], headers=klocwork["header"], data=data, verify=False)

    result_dict = {}
    for element in result.text.split("\n"):
        if element != "":
            element_dict = json.loads(element)
            result_dict.update({element_dict["id"]: element_dict})

    return result_dict

#file_metadata = artifactory.get_metainfo("{}/{}".format(folder_url, file_name), release_id=release_id)
def main(search_build, baseline_version, release_id):
    """
    The main function will get the build number and return the severity results.

    :param search_build: Search for the build name in klocwork
    :return: A dictionary with the severity as key, and the number of defects as value
    """
    print("START -> GET KLOCWORK FINDINGS")
    result_json = get_builds_from_test_results(baseline_version, release_id)
    if result_json == {}:
        builds = get_builds_from_kw_server()

        build_of_version = False
        for build in builds:
            if builds[build]["name"] == search_build:
                build_of_version = builds[build]["name"]

        if build_of_version:
            severity_results = {}
            for i in range(1, 4):
                query_result = get_query("build:{} status:+Analyze,+Fix,+Defer severity:{}".format(build_of_version, str(i)))
                severity_results.update({"{}".format(i): len(query_result)})
        else:
            raise Exception("Klocwork build is not available => {}".format(search_build))
    else:
        severity_results = result_json
    print("FINISHED -> GET KLOCWORK FINDINGS")
    return severity_results


if __name__ == "__main__":
    search_build = "CONMOD-SA515M-CL43-3.3.300.0"
    severity_results = main(search_build)
    print("#" * 30)
    for element in range(1, 4):
        print(element, severity_results[element])
