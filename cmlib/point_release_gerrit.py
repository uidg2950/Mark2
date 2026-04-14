# *****************************************************************************
# *
# * (c) 2023 Continental Automotive Systems, Inc., all rights reserved
# *
# * All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# * Any reproduction of this material without written consent from
# * Continental Automotive Systems, Inc. is strictly forbidden.
# *
# * Filename:    point_release_gerrit.py
# *
# * Description: Creates a class for interacting with gerrit for the generate_point_release.py script
# *
# * Revision History:
# *
# *  CQ#    Author           Date          Description of Change(s)
# *  -----  -------------    ----------    ------------------------------------
# *         uidu3800         2023-01-25    Init version
# *
# *****************************************************************************


import json
import requests
from requests.auth import HTTPBasicAuth


class Gerrit:

    def __init__(self, api_url, user, api_key):
        """
        The __init__ function is called when a new instance of the class is created.
        It initializes all of the variables that are unique to each instance, such as
        the url and username/password.

        :param self: Refer to the object itself
        :return: The object of the class
        """
        self.__url = api_url
        self.__user = user
        self.__pass = api_key

        self.__session = requests.Session()
        self.set_session()
#        self.cherry_pick = self.get_cherry_pick()

    def set_session(self):
        """
        The set_session function sets the session variable to a requests.Session object,
        which is then used throughout the rest of this class.

        :param self: Allow a method to modify an attribute of the class
        :return: The session variable
        """
        self.__session = requests.Session()
        self.__header = {'Content-Type': 'application/json', 'charset': 'UTF-8', "Accept": "application/json"}
        self.__session.auth = requests.auth.HTTPDigestAuth(self.__user, self.__pass)
        self.__session.headers = self.__header
        self.__session.verify = False

    def transform_result_to_json(self, res_text):
        """
        The transform_result_to_json function takes the response text from a request to the API and returns
        a Python dictionary containing the data in that response. The function is used by all of our functions
        that make requests to the API.

        :param self: Access the attributes and methods of the class in python
        :param res_text: Get the text from the response
        :return: The result of the api call as a python dictionary
        """
        return json.loads(res_text.split(")]}'")[1])

    def get_change_information(self, change_id_number):
        """
        The get_change_information function takes a change_id number as an argument and returns a dictionary containing the following information:
            - id: The ID of the change.
            - project: The name of the project that this change is associated with.
            - branch: The branch that this change is associated with.
            - current_revision_url: A URL to fetch from in order to get more information about the current revision for this change (the &quot;fetch&quot; key in https://gerrit-review.googlesource.com/Documentation/rest-api-changes.html#change-detail). This URL

        :param self: Access the class attributes
        :param change_id_number: Specify the change id number of the change that should be fetched
        :return: A dictionary with the following keys:
        """
        api_url = "{}changes/{}/detail?o=CURRENT_REVISION".format(self.__url, change_id_number)
        print(api_url)
        res = self.__session.get(api_url)
        res_json = self.transform_result_to_json(res.text)
        result = {
            "id": res_json["id"],
            "project": res_json["project"],
            "branch": res_json["branch"],
            "change_id": res_json["change_id"],
            "current_revision_url": res_json["revisions"][res_json["current_revision"]]["fetch"]["ssh"]["url"],
            "current_revision_ref": res_json["revisions"][res_json["current_revision"]]["fetch"]["ssh"]["ref"]
        }
        result.update({"cherry_pick": "git fetch {} {} && git cherry-pick FETCH_HEAD".format(result["current_revision_url"], result["current_revision_ref"])})
        return result

    def get_latest_number_for_branch(self, project, previous_baseline):
        """
        The get_latest_number_for_branch function takes a project name and the previous baseline as parameters.
        It returns the next number for that branch, which is calculated by adding 1 to the highest minor version of all branches with that major version.


        :param self: Reference the class object
        :param project: Specify the project
        :param previous_baseline: Get the latest number for a branch
        :return: The highest number of the minor version
        """
        print(previous_baseline)
        previous_baseline_without_minor_version = "{}.".format(previous_baseline.rsplit(".", 1)[0])
        self_url = "https://buic-scm-rbg.contiwan.com:8443/"
        project = "%2F".join(project.split("/"))
        request_url = "{}projects/{}/branches?m={}".format(self.__url, project, previous_baseline_without_minor_version)

        print(request_url)
        res = self.__session.get(request_url)
        res_json = self.transform_result_to_json(res.text)
        refs = []
        # get all branches with previous_baseline_without_minor_version
        for element in res_json:
            refs.append(element["ref"])

        # get the highest number of minor version
        for i, ref in enumerate(refs):
            print(ref)
            if i == 0:
                highest = ref.rsplit(".", 1)[1]
            else:
                next_candidate = ref.rsplit(".", 1)[1]
                if highest < next_candidate:
                    highest = next_candidate
        print("The highest number is => {}".format(highest))
        next_version = int(highest) + 1
        return "{}{}".format(previous_baseline_without_minor_version, next_version)


if __name__ == "__main__":
    urls = ["https://buic-scm-rbg.contiwan.com:8443/#/c/2933582/", "https://buic-scm-rbg.contiwan.com:8443/#/c/2898096/", "https://buic-scm-sgp.contiwan.com:8443/#/c/2948388/"]
    ger_obj = Gerrit()
    for url in urls:
        print("\n" * 3)
        url_splitted = url.split("/")
        for x in range(len(url_splitted) - 1, 0, -1):
            if url_splitted[x].isnumeric():
                change_id = url_splitted[x]
                break
        print(change_id)
        data = ger_obj.get_change_information(change_id)
        for element in data:
            print("{} => {}".format(element, data[element]))

    project = "p1/project/otp-hal/manifest"
    previous_baseline = "conmod-hal-sa515m-3.147.0.13"
    result = ger_obj.get_latest_number_for_branch(project, previous_baseline)
    print(result)
