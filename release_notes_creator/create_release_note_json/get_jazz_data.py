import requests
from .settings import *
from helper.credentials_keyring import get_password


def get_number_of_software_tests_faulty(test_plan_id):
    """
    The get_number_of_software_tests_faulty function returns the number of tests that have not passed in a given test plan.
    The function takes one argument, which is the ID of the test plan for which we want to know how many tests are faulty.


    :param test_plan_id: Specify the test plan in which we want to get the number of tests
    :return: The number of failed tests for the given test plan id
    """
    base_url = jazz["base_url"]
    project_area = jazz["project_area"]
    oslc_config_context = jazz["oslc_config_context"]

    # create session
    sess = requests.session()
    sess.headers = jazz["headers"]
    sess.auth = (get_password(SERVICE_NAME, jazz["user"]), get_password(SERVICE_NAME, jazz["passwd"]))
    sess.verify = False
    server_url = jazz["auth_url"]
    login_res = sess.get(server_url)

    if login_res.status_code != 200:
        raise Exception("The login to jazz server failed!!!")

    # get vID of test plan
    url_get_test_plan_vid = "{}/service/com.ibm.rqm.web.common.service.rest.ICompositeWebRestService/artifact?processArea={}&artifactType=TestPlan&oslc_config.context={}&id={}&gcConfigValue={}/oslc_config/resources/com.ibm.team.vvc.Configuration/{}&webContext.projectArea={}".format(base_url,
                                                                                                                                                                                                                                                                         project_area,
                                                                                                                                                                                                                                                                         oslc_config_context,
                                                                                                                                                                                                                                                                         test_plan_id,
                                                                                                                                                                                                                                                                         base_url,
                                                                                                                                                                                                                                                                         oslc_config_context,
                                                                                                                                                                                                                                                                         project_area)
    payload_get_test_plan_vid = {
        "processArea": project_area,
        "artifactType": "TestPlan",
        "oslc_config.context": oslc_config_context,
        "id": test_plan_id,
        "gcConfigValue": "{}/oslc_config/resources/com.ibm.team.vvc.Configuration/{}".format(base_url, oslc_config_context),
        "webContext.projectArea": project_area
    }
    additional_headers = {"Accept": "text/json"}
    res = sess.get(url_get_test_plan_vid, headers=additional_headers, params=payload_get_test_plan_vid)
    if login_res.status_code != 200:
        raise Exception("The query against jazz server failed!!!")
    res_json = res.json()
    v_test_plan_item_ids = res_json['soapenv:Body']['response']['returnValue']['value']['testplan']['versionableItemId']
#    print("#{}#".format(v_test_plan_item_ids))

    # Get all test case execution records
    url_get_test_case_execution_records = "{}/service/com.ibm.rqm.execution.common.service.rest.ITestcaseExecutionRecordRestService/pagedSearchResult?oslc_config.context={}&webContext.projectArea={}".format(base_url, oslc_config_context, project_area)
    payload_get_test_case_execution_records = {
        'includeCustomAttributes': 'true',
        'includeArchived': 'false',
        'processArea': project_area,
        'gcConfigValue': '{}/oslc_config/resources/com.ibm.team.vvc.Configuration/{}'.format(base_url, oslc_config_context),
        'vTestPlanItemIds': v_test_plan_item_ids,
        'traceabilityViewType': 'false',
        'esolveTSERs': 'false',
        'resolveRequirements': 'false',
        'resolveParentAttributes': 'true',
        'resolveCategories': 'false',
        'resolveCustomAttributes': 'false',
        'resolveDefects': 'false',
        'resolveCopiedArtifactInfo': 'false',
        'page': '0',
        'sortColumns': 'modified:DESCENDING',
        'pageSize': '-1',
        'resultLimit': '-1',
        #          'totalSize': '75',
        'oslc_config.context': oslc_config_context
    }
    res = sess.get(url_get_test_case_execution_records, headers=additional_headers, params=payload_get_test_case_execution_records)
    if login_res.status_code != 200:
        raise Exception("The query against jazz server failed!!!")
    resp_json = res.json()
    results = resp_json["soapenv:Body"]["response"]["returnValue"]["value"]["results"]
    no_of_passed_tests = 0
    no_of_not_passed_tests = 0
    for n, element in enumerate(results):
        if element["currentResultStateName"] == "Passed":
            no_of_passed_tests += 1
        else:
            no_of_not_passed_tests += 1

    return no_of_not_passed_tests


if __name__ == "__main__":
    get_number_of_software_tests_faulty("3724")
