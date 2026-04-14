import argparse
import os

from atlassian import Confluence

from create_release_note_file import ReleaseNoteFileGenerator
from create_release_note_json.create_release_note_json import main as create_release_note_json
from doc_gen_gui import *
from helper.credentials_keyring import *
from helper.format_md2pdf import convert_md2html, write_html2pdf


class DocumentationGeneration:
    def __init__(self):
        """
        The __init__ function is called when the class is instantiated.
        It sets up the instance of the class, and defines all variables that are used in other functions within this class.

        :param self: Represent the instance of the class
        :return: None, but the class is returned
        """
        # keyring data
        self.release_version = self.evaluate_keyring_data(get_password(SERVICE_NAME, RELEASE_VERSION))
        self.baseline_version = self.evaluate_keyring_data(get_password(SERVICE_NAME, BASELINE_VERSION))
        self.release_id = self.evaluate_keyring_data(get_password(SERVICE_NAME, RELEASE_ID))
        self.confluence_page_pre_release = self.evaluate_keyring_data(get_password(SERVICE_NAME, CONFLUENCE_PAGE_PRE_RELEASE))
        self.uid = self.evaluate_keyring_data(get_password(SERVICE_NAME, UID))
        self.win_passwd = self.evaluate_keyring_data(get_password(SERVICE_NAME, WIN_PASSWD))
        self.box_pre_release_md = self.evaluate_keyring_data(get_password(SERVICE_NAME, BOX_PRE_RELEASE_MD))
        self.box_release_note_json = self.evaluate_keyring_data(get_password(SERVICE_NAME, BOX_RELEASE_NOTE_JSON))
        self.jazz_testplan_id = self.evaluate_keyring_data(get_password(SERVICE_NAME, TEST_PLAN_ID), False)
        if self.jazz_testplan_id == "None":
            self.jazz_testplan_id = None

        # confluence parameters
        tmp_confluence_page_splitted = self.confluence_page_pre_release.split("/")
        self.confluence_main_url = "https://{}".format(tmp_confluence_page_splitted[2])
        self.confluence_api_obj = Confluence(
            url=self.confluence_main_url,
            username=self.uid,
            password=self.win_passwd
        )
        if "pageId=" in tmp_confluence_page_splitted[-1]:
            self.confluence_page_id = tmp_confluence_page_splitted[-1].split("pageId=")[1]
            self.confluence_space = self.confluence_api_obj.get_page_space(self.confluence_page_id)
        else:
            # FIXME: New URL format
            # > Old -> ['https:', '', 'central.confluence.automotive.cloud', 'display', 'CMP', 'RRR+3.6.121.7+-+2025+cw31.4+Pre+Release+-+PROD-Signed']
            # > New -> ['https:', '', 'central.confluence.automotive.cloud', 'spaces', 'CMP', 'pages', '3400368607', 'RRR+cl46r3-3.6.144.7.0+-+2025+cw34.4+Pre+Release+-+PROD-Signed']
            # tmp_confluence_page_splitted[4] is now -> CMP, due "spaces" is now defined instead of "display" like in the past.
            self.confluence_space = tmp_confluence_page_splitted[4]
            tmp_page_name = " ".join(tmp_confluence_page_splitted[-1].split("+"))
            self.confluence_page_id = self.confluence_api_obj.get_page_id(self.confluence_space, tmp_page_name)

        self.confluence_page_content_as_list = self.read_confluence_page()

    @staticmethod
    def evaluate_keyring_data(value, evaluate=True):
        """
        The evaluate_keyring_data function is used to evaluate the data that was entered into the GUI.
        If all fields are filled out, then it will return the value of each field. If not, it will raise a ValueError.

        :param value: Pass in the values from the gui
        :param evaluate: True/False -> If False the missing value will not raise an error
        :return: The value of the data that is input into the gui
        """
        if value:
            return value
        else:
            if evaluate:
                raise ValueError("Please fill out all fields in the GUI")
            else:
                return value

    def read_confluence_page(self):
        """
        The read_confluence_page function reads the Confluence page with the ID specified in self.confluence_page_id,
        and returns a list of strings where each string is one line from the Confluence page.

        :param self: Bind the method to an object
        :return: A list of strings
        """
        content = self.confluence_api_obj.get_page_by_id(self.confluence_page_id, expand="body.storage")
        cont_body = content["body"]["storage"]["value"]
        view_content = self.confluence_api_obj.convert_storage_to_view(cont_body)
        return view_content["value"].split("\n")

    def get_jira_query_from_confluence(self, headline):
        """
        The get_jira_query_from_confluence function takes a headline as an argument and returns the JQL query
        and the table of issues that are returned by this query. The function searches for the headline in
        the confluence page content, then looks for a div with class &quot;jira-issues&quot; which contains both
        the JQL query and the table of issues. It returns these two elements.

        :param self: Bind the method to an object
        :param headline: Find the headline in the confluence page
        :return: The jql query and the jira table as a list
        """
        headline_found = False
        jira_div_found = False
        jql_query = False
        jira_table = []
        for element in self.confluence_page_content_as_list:

            if headline_found:
                if jira_div_found:
                    jira_table.append(element.strip())
                    if "jqlQuery&quot;&gt;" in element:
                        jql_query = element.split("jqlQuery&quot;&gt;")[1].split("&lt;/")[0]
                    if "</div>" in element and jql_query:
                        break
                if "<div" in element and 'class="jira-issues"' in element:
                    jira_div_found = True
                    jira_table.append(element)
                    continue
            if headline in element:
                headline_found = True

        return jql_query, jira_table

    @staticmethod
    def filter_table(table_with_more):
        """
        The filter_table function takes in a list of strings and returns a list of strings.
        The function filters out all the elements that are not part of the table, including
        the &lt;table&gt; tag itself. The function also removes any empty elements from the list.

        :param table_with_more: Pass in the table with more information
        :return: The table from the html
        """
        table_start = False
        table = []
        for element in table_with_more:
            if "<table" in element:
                table_start = True
            if table_start:
                table.append(element)
            if "</table>" in element:
                break
        return table

    def create_prerelease_doc(self, pre_release_doc, is_pre_release=True):
        """
        The create_prerelease_doc function creates a pre-release document for the release version.
        The pre-release document is created in the output folder and contains:
            - The implemented features table from Confluence, with JQL query to reproduce it.
            - The corrected defects table from Confluence, with JQL query to reproduce it.

        :param self: Reference the object that is calling the method
        :param pre_release_doc: Specify the folder and name for the pre-release document, to save
        :return: the jql query for corrected defects
        """
        implementd_features_jql_query, implementd_features_table_and_more = self.get_jira_query_from_confluence("Implemented Features")
        corrected_defects_jql_query, corrected_defects_and_more = self.get_jira_query_from_confluence("Corrected Defects")

        implementd_features_table = self.filter_table(implementd_features_table_and_more)
        corrected_defects = self.filter_table(corrected_defects_and_more)
        # implementd_features_table = implementd_features_table_and_more

        if is_pre_release:
            with open(pre_release_doc, "w") as pre_release_file:
                pre_release_file.writelines("# {}\n".format(self.release_version))
                pre_release_file.writelines("\n## Implemented Features\n")
                pre_release_file.writelines("\n`{}`\n".format(implementd_features_jql_query))
                pre_release_file.writelines("\n".join(implementd_features_table))
                pre_release_file.writelines("\n\n## Corrected Defects\n")
                pre_release_file.writelines("\n`{}`\n".format(corrected_defects_jql_query))
                pre_release_file.writelines("\n".join(corrected_defects))

            # create md -> html -> pdf doc
            convert_md2html(pre_release_doc)
            write_html2pdf(pre_release_doc, "document_theme")

        return corrected_defects_jql_query

    def create_release_doc(self, output_folder, defects_jql_query, delivery_type):
        """
        The create_release_doc function creates a release document for the specified release version.
            The function takes in the following parameters:
                - output_folder: The folder where all of the generated files will be stored.
                - defects_jql_query: A JQL query that is used to find all of the defects associated with this release.

        :param self: Represent the instance of the class
        :param output_folder: Specify the location of where the release note json file will be created
        :param defects_jql_query: Query for defects in the jira instance
        :return: A json file with the release notes
        """
        print("#" * 21)
        print("CREATE Release Doc")
        print("START: Create Release Note JSON")
        # create release note json file

        print("> release type & version = {}".format(self.release_version))
        print("> release_id = {}".format(self.release_id))
        print("> baseline_version = {}".format(self.baseline_version))

        create_release_note_json(self.baseline_version, self.release_id,
                                 self.release_version, self.jazz_testplan_id, output_folder, defects_jql_query)

        # FIXME: This is a workaround, in order to do a proper fix a big part of the script should be reworked.
        if delivery_type == "Continental Release":
            # create release note file
            template_version = "CONMOD_5_G_VbaselineVersion_cl43.md" if "cl43" in self.baseline_version else "CONMOD_5_G_VbaselineVersion.md"
            template_file = os.path.join(os.path.dirname(__file__), "templates", template_version)
            rel_note_file_obj = ReleaseNoteFileGenerator(self.release_id, template_file, self.release_version, self.confluence_page_content_as_list, output_folder)
            rel_note_file_obj.write_and_save_generated_release_note_file()


def get_release_version_from_confluence_url(url):
    """
    The get_release_version_from_confluence_url function takes a confluence url as input and returns the release version
    of that confluence page. The function is used to get the release version of a new CONMOD from its Confluence URL.

    :param url: Get the last part of the url
    :return: The release version of a confluence url
    """
    last_part_of_url = url.split("/")[-1]
    splittet_add_plus = last_part_of_url.split("+")
    version = splittet_add_plus[1]
    year_short = splittet_add_plus[3][2:4]
    cw = splittet_add_plus[4].split("cw")[1]
    result = "CONMOD_5_G_V{}_CW{}.{}".format(version, year_short, cw)

    return result


if __name__ == '__main__':
    # Parse Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--gui", dest="gui_arg", default=False, help="If you will run the script in 'GUI' mode => True", required=False)
    parser.add_argument("--output_folder", dest="output_folder", type=str, default="output", help="Folder for all outputs", required=True)
    # parser.add_argument("--release_version", dest="release_version", type=str, help="HELP STRING", required=False)
    # Adding baseline_version & release_id 
    parser.add_argument("--baseline_version", dest="baseline_version", type=str, help="baseline version", required=False)
    parser.add_argument("--release_id", dest="release_id", type=str, help="release_id version", required=False)
    parser.add_argument("--rrr_confluence_link", dest="rrr_confluence_link", type=str, default=None,
                        help="The Confluence URL to the RRR-(Pre)-Release_Version. It should looks like "
                             "'https://confluence.auto.continental.cloud/display/CMP/RRR+cl43-3.3.323.3+-+2023+cw23.1+Release+-+PROD-Signed'", required=False)
    parser.add_argument("--delivery_type", dest="delivery_type", type=str, default=None, help="Set 'Continental Release' or 'Pre Release'", required=False)
    parser.add_argument("--jazz_test_plan_id", dest="test_plan_id", type=str, default=None, help="The Testplan ID from IBM Jazz", required=False)
    parser.add_argument("--win_uid", dest="win_uid", type=str, default=None, help="Your Windows User ID", required=False)
    parser.add_argument("--win_passwd", dest="win_passwd", type=str, default=None, help="Your Windows User Password", required=False)
    parser.add_argument("--klocwork_user", dest="klocwork_user", type=str, default=None, help="Your Klocwork User name", required=False)
    parser.add_argument("--klocwork_token", dest="klocwork_token", type=str, default=None, help="Your Klocwork token", required=False)
    parser.add_argument("--artifactory_user", dest="artifactory_user", type=str, default=None, help="Your Artifactory user", required=False)
    parser.add_argument("--artifactory_token", dest="artifactory_token", type=str, default=None, help="Your Artifactory token", required=False)

    args = parser.parse_args()

    gui_arg = args.gui_arg
    output_folder = args.output_folder
    baseline_version = args.baseline_version
    release_id = args.release_id
    release_version = None

    if gui_arg:
        set_source_for_keyring_varialbes(True)
        ft.app(target=gui)
    else:
        set_source_for_keyring_varialbes(False)
        if args.delivery_type == "Continental Release":
            box_release_note_json = "true"
            release_version = get_release_version_from_confluence_url(args.rrr_confluence_link)
        else:
            box_release_note_json = "false"

        if args.delivery_type == "Pre Release":
            box_release_note_json = "true"
            box_pre_release_md = "true"
            if not release_version:
                release_version = get_release_version_from_confluence_url(args.rrr_confluence_link)
        else:
            box_pre_release_md = "false"

        # set artifactory user and token
        if str(args.artifactory_user) == "None":
            with open(os.path.join(os.environ["HOME"], '.credentials/artifactory')) as CREDENTIALS_FILE:
                artifactory_token = CREDENTIALS_FILE.read()

            artifactory_user = artifactory_token.split(':')[0]
            artifactory_password = artifactory_token.split(':')[1]
            if artifactory_password[-1] == '\n':
                artifactory_password = artifactory_password[:-1]

            set_password(SERVICE_NAME, ARTIFACTORY_USER, artifactory_user)
            set_password(SERVICE_NAME, ARTIFACTORY_TOKEN, artifactory_password)
        else:
            set_password(SERVICE_NAME, ARTIFACTORY_USER, args.artifactory_user)
            set_password(SERVICE_NAME, ARTIFACTORY_TOKEN, args.artifactory_token)

        # set klocwork user and token
        if str(args.klocwork_user) == "None":
            print(os.environ["HOME"])
            with open(os.path.join(os.environ["HOME"], '.klocwork/ltoken')) as klocwork_credential_file:
                klocwork_tokens_list = klocwork_credential_file.readlines()
            for element in klocwork_tokens_list:
                if "dpas007x.qh.us.conti.de" in element:
                    # Fill out the logic to get the ltoken from file
                    # But actually the "dpas007x.dp.us.conti.de:8092" is not available in the file
                    element_splitted = element.split(";")
                    set_password(SERVICE_NAME, KLOCWORK_USER, element_splitted[2])
                    set_password(SERVICE_NAME, KLOCWORK_TOKEN, element_splitted[3].rstrip())
        else:
            set_password(SERVICE_NAME, KLOCWORK_USER, args.klocwork_user)
            set_password(SERVICE_NAME, KLOCWORK_TOKEN, args.klocwork_token)

        set_password(SERVICE_NAME, RELEASE_VERSION, release_version)
        set_password(SERVICE_NAME, BASELINE_VERSION, baseline_version)
        set_password(SERVICE_NAME, RELEASE_ID, release_id)
        set_password(SERVICE_NAME, BOX_PRE_RELEASE_MD, box_pre_release_md)
        set_password(SERVICE_NAME, BOX_RELEASE_NOTE_JSON, box_release_note_json)

        set_password(SERVICE_NAME, CONFLUENCE_PAGE_PRE_RELEASE, args.rrr_confluence_link)
        set_password(SERVICE_NAME, CONFLUENCE_PAGE_RELEASE, args.rrr_confluence_link)
        set_password(SERVICE_NAME, TEST_PLAN_ID, args.test_plan_id)
        set_password(SERVICE_NAME, UID, args.win_uid)
        set_password(SERVICE_NAME, WIN_PASSWD, args.win_passwd)

    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    if gui_arg:
        doc_gen = DocumentationGeneration()
    else:
        doc_gen = DocumentationGeneration()
    print(doc_gen.baseline_version)
    print(doc_gen.release_version)
    print(doc_gen.confluence_page_pre_release)
    print(doc_gen.confluence_main_url)
    print(doc_gen.confluence_space)
    print(doc_gen.confluence_page_id)
    pre_release_file_name = "{}__PREREL.md".format(doc_gen.release_version)
    pre_release_doc = os.path.join(output_folder, pre_release_file_name)

    if doc_gen.box_pre_release_md == "true":
        print("START: Pre Release Documentation")
        defects_jql_query = doc_gen.create_prerelease_doc(pre_release_doc)
    if doc_gen.box_release_note_json == "true":
        defects_jql_query = doc_gen.create_prerelease_doc(pre_release_doc, False)
    # FIXME: This is a workaround, in order to do a proper fix a big part of the script should be reworked.
    if args.delivery_type != "Engineering Drop":
        doc_gen.create_release_doc(output_folder, defects_jql_query, args.delivery_type)
