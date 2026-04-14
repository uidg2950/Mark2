import requests

from keyring_variables import *
from helper.credentials_keyring import get_password


class GetDataFromArtifactory:
    def __init__(self, server: str, user: str, token: str, path: str):
        """
        The __init__ function is called when an instance of the class is created.
        It initializes attributes that are common to all instances of the class.


        :param self: Refer to the object that is being created
        :param server: Store the server address
        :param user: Store the username of the user that is used to authenticate against artifactory
        :param token: Authenticate the user to artifactory
        :param path: Specify the path to the artifact in artifactory
        """
        self.server = server
        self.user = user
        self.token = token
        self.session = requests.Session()
        self.session.auth = (self.user, self.token)
        self.artifactory_url = "/".join([self.server, path])
        self.artifactory_api_url = "/".join([self.server, "api", "storage", path])

        print("The relative path is => " + path)
        print("The full artifactory url is => " + self.artifactory_url)
        print("The full artifactory api url is => " + self.artifactory_api_url)

    def get_metainfo(self, url: str) -> requests:
        """
        The get_metainfo function accepts an artifactury url as an argument and returns the metadata of the ressource.

        :param self: Access the instance attributes of the class
        :param url: Specify the url where to get the metainfo from
        :return: result object of the request
        """
        print("You are running => {}".format("get_metainfo"))
        print("Artifacotry URL => {}".format(url))
        res = self.session.get(url)
        return res

    def download_artifact(self, download_url: str, file2save: str):
        """
        The download_artifact function downloads a file from the artifactory repository.

        :param self: Reference the class instance
        :param download_url: Specify the file to download
        :param file2save: Save the artifact to this file ("path + file" or "file")
        """
        print("You will download '{}' to '{}'".format(download_url, file2save))

        res = self.session.get(download_url)
        if res.status_code != 200:
            raise Exception("Download failed!")
        with open(file2save, "wb") as f:
            f.write(res.content)

    @staticmethod
    def check_request_result(res_object) -> bool:
        """
        The check_request_result function checks the status code of a request and returns True if it is 201 or 200,
        otherwise it will return False.

        :param res_object: Store the response object of the request
        :return: A boolean value
        """
        if res_object.status_code == 201 or res_object.status_code == 200:
            print("The status code of the request is success => Status Code: {}".format(res_object.status_code))
            return True
        else:
            print("The status code of the request is failed => Status Code: {}".format(res_object.status_code))
            return False


def download_file_from_artifactory(path_on_artifactory, destination_path_file):
    """
    The download_file_from_artifactory function downloads a file from Artifactory.

    :param path_on_artifactory: Specify the path to the file on artifactory
    :param destination_path_file: Specify the path to the file that will be downloaded from artifactory
    :return: A file object
    """
    server = "https://us.artifactory.automotive.cloud/artifactory"
    user = get_password(SERVICE_NAME, ARTIFACTORY_USER)
    token = get_password(SERVICE_NAME, ARTIFACTORY_TOKEN)

    arti = GetDataFromArtifactory(server, user, token, path_on_artifactory)
    res = arti.get_metainfo(arti.artifactory_api_url)
    arti.check_request_result(res)
    arti.download_artifact(arti.artifactory_url, destination_path_file)


def download_file_from_artifactory_test_results(main_path_on_artifactory, second_part_of_artifactory_path, destination_path_file):
    """
    The download_file_from_artifactory_test_results function downloads a file from artifactory.
        Args:
            main_path_on_artifactory (str): The path to the folder on artifactory where the test results are stored.
            second_part_of_artifactory_path (str): The path to the file in question, relative to its parent folder.
            destination-path-file (str): The local path where you want your downloaded file saved.

    :param main_path_on_artifactory: Specify the main path on artifactory
    :param second_part_of_artifactory_path: Specify the path to the file on artifactory
    :param destination_path_file: Specify the path where the file will be downloaded
    :return: A file from artifactory, which is saved at the given destination_path_file
    """
    server = "https://us.artifactory.automotive.cloud/artifactory"
    user = get_password(SERVICE_NAME, ARTIFACTORY_USER)
    token = get_password(SERVICE_NAME, ARTIFACTORY_TOKEN)

    arti = GetDataFromArtifactory(server, user, token, main_path_on_artifactory)
    res = arti.get_metainfo(arti.artifactory_api_url)
    arti.check_request_result(res)
    res_json = res.json()
    print(res_json)
    for i, child in enumerate(res_json["children"]):
        act_count_of_plus = child["uri"].count("+")
        if i == 0:
            count_of_plus = act_count_of_plus
            nr_of_child = i
        elif count_of_plus < act_count_of_plus:
            count_of_plus = act_count_of_plus
            nr_of_child = i
    last_test_result = res_json["children"][nr_of_child]["uri"]
    # Workaround in case of full test results ( not smoke )
    test_results_type = "_smoke"        # defualt value
    if "_full" in last_test_result:
        test_results_type = "_full"     # in case of full tst executed
    version = last_test_result.split(test_results_type)[0]
    path_for_artifactory_file = "{}{}!{}/{}".format(arti.artifactory_url, last_test_result, version, second_part_of_artifactory_path)

    arti.download_artifact(path_for_artifactory_file, destination_path_file)
