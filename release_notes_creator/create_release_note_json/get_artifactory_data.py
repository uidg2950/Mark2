from helper.credentials_keyring import get_password
from keyring_variables import *
from helper.artifactory_downloader import GetDataFromArtifactory


def download_kpi_data_xlsx_file_from_artifactory(baseline_version, release_id, filename_4_save):
    """
    The download_kpi_data_xlsx_file_from_artifactory function downloads the KPI data xlsx file from Artifactory.

    :param version: Get the right version of the kpi data
    :param filename_4_save: Save the downloaded file with a specific name
    :return: The path of the downloaded file
    """
    # base-version(version) is extracted from baseline_version,
    # i.e. conmod-sa515m-cl43-3.3.348.1 -> base-version(version) = cl43-3.3.348.1
    # base-version(version) is needed for ConMod_KPI_Data-{}.xlsx

    version = "-".join(baseline_version.split("-")[2:])
    repo = "vni_otp_generic_l"
    path = "/".join([repo, release_id, baseline_version, "Test_Results"])
    print(path)

    server = "https://us.artifactory.automotive.cloud/artifactory"
    user = get_password(SERVICE_NAME, ARTIFACTORY_USER)
    token = get_password(SERVICE_NAME, ARTIFACTORY_TOKEN)

    arti = GetDataFromArtifactory(server, user, token, path)
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

    path_for_kpi_xlsx_file = "{}{}!/{}/KPI_Report_for_System_Resources/ConMod_KPI_Data-{}.xlsx".format(arti.artifactory_url, last_test_result, baseline_version,
                                                                                                       version)
    arti.download_artifact(path_for_kpi_xlsx_file, filename_4_save)


if __name__ == '__main__':
    version = "CONMOD_5_G_Vcl43-3.3.323.2_CW23.22.5"
    version = "CONMOD_5_G_Vcl43-3.3.321.9_CW23.22.5"
    file = "kpi_data.xlsx"

    download_kpi_data_xlsx_file_from_artifactory(version, file)
