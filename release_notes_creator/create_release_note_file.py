import datetime
import json
import os
import shutil
from pprint import pprint
from html.parser import HTMLParser

import keyring

from openpyxl import load_workbook
from keyring_variables import *
from helper.artifactory_downloader import download_file_from_artifactory, download_file_from_artifactory_test_results
from helper.excel_helper import check_sheetname_in_excel
from helper.format_md2pdf import convert_md2html, write_html2pdf


def read_file(template_file):
    """
    The read_file function reads the template file and returns a list of lines.

    :param template_file: Open the file and read it
    :return: A list of strings
    """
    with open(template_file, "r", encoding="utf-8") as templ_file:
        content = templ_file.readlines()
    return content


class MyHTMLParser(HTMLParser):
    def __init__(self):
        """
        The __init__ function is called when the class is instantiated.
        It sets up the instance of the class, and defines any variables that will be used by other functions in this class.
        In this case, it creates a list to store all of our data (self.content), an integer to keep track of where we are in that list (self.i),
        and a string variable for temporary storage.

        :param self: Represent the instance of the class
        :return: Nothing
        """
        super().__init__()
        self.content = []
        self.i = 0
        self.tmp = ""

    def handle_starttag(self, tag, attrs) -> None:
        """
        The handle_starttag function is called when the parser encounters an opening tag.
        The arguments are the tag name and a list of attributes, exactly as in starttag().
        This method should be overridden to handle tags that need special attention.

        :param self: Represent the instance of the class
        :param tag: Store the tag name
        :param attrs: Get the attributes of a tag
        :return: A string with the tag name and a greater than sign
        """
        if attrs:
            attrs_new_list = []
            for element in attrs:
                if "class" not in element[0] and "id" not in element[0] and element[1]:
                    attrs_new_list.append('{}="{}"'.format(element[0], element[1]))
            if attrs_new_list:
                attrs_str = " ".join(attrs_new_list)

                print("ATTR =", attrs_str)

                self.tmp += "<{} {}>".format(tag, attrs_str)
                self.i += 1
            else:
                self.tmp += "<{}>".format(tag)
                self.i += 1
        else:
            self.tmp += "<{}>".format(tag)
            self.i += 1

    def handle_endtag(self, tag: str) -> None:
        """
        The handle_endtag function is called when the parser encounters an end tag.
        It takes in a string representing the name of the tag and appends it to self.tmp,
        along with its closing angle bracket. It then decrements self.i by 1.

        :param self: Access the attributes and methods of the class
        :param tag: str: Store the tag that is being closed
        :return: A string of the end tag
        """
        self.tmp += "</{}>".format(tag)
        self.i -= 1
        if self.i == 0:
            self.content.append(self.tmp)
            self.tmp = ""

    def handle_data(self, data: str) -> None:
        """
        The handle_data function is called when the parser encounters a string of text.
        The data argument contains the text that was found.

        :param self: Represent the instance of the class
        :param data: str: Pass the data from the client to the server
        :return: None
        """
        self.tmp += "{}".format(data)


class ReleaseNoteFileGenerator:
    def __init__(self, release_id, template_file, version, confluence_content, output_folder):
        """
        The __init__ function is called when the class is instantiated.
        It sets up the object with all of its attributes and methods.

        :param self: Refer to the instance of the class
        :param template_file: Read the template file and store it in self
        :param version: Create the name of the output file
        :param confluence_content: Create the self
        :param output_folder: Store the files downloaded from artifactory

        :return: Nothing
        """
        self.release_id = release_id
        self.version_full = version
        self.output_folder = output_folder
        self.artifactory_repo = "vni_otp_generic_l"
        self.result_file_with_path = "{}.md".format(os.path.join(self.output_folder, version))
        self.result_file_with_path_pdf = "{}.pdf".format(os.path.join(self.output_folder, version))
        self.version = version.split("G_V")[1].split("_CW")[0]
        self.sw_version = "conmod-sa515m-{}".format(self.version)
        self.confluence_content = self.transform_confluence_content(confluence_content)
        self.content_tmpl_file = read_file(template_file)
        self.key_start_str = "[("
        self.key_end_str = ")]"
        self.keys_from_template_file = self.get_all_keys()
        self.create_set_type_of_keys()
        self.values_for_keys = self.create_dict_with_none_as_value()
        # download and create otp_versionss dict
        self.otp_versions_file = "otp_versions.txt"
        self.otp_version_file_with_path = os.path.join(output_folder, self.otp_versions_file)
        self.download_otp_versions_file_from_artifactory()
        self.google_test_file = "google_test.properties"
        self.google_test_file_with_path = os.path.join(output_folder, self.google_test_file)
        self.at_gmr_file = "ati_output.txt"
        self.at_gmr_file_with_path = os.path.join(output_folder, self.at_gmr_file)
        self.otp_versions_dict = self.create_otp_versiosn_dict()
        baseline_short_v = self.otp_versions_dict["OTP_VERSION"].split("sa515m-")[-1]
        self.otp_versions_dict.update({"BASELINE_SHORT_VERSION": baseline_short_v})
        self.fill_values_for_all_keys()

    @staticmethod
    def transform_confluence_content(content):
        """
        The transform_confluence_content function takes in a list of strings and returns a string.
        The function is used to transform the content from Confluence into something that can be parsed by MyHTMLParser.
        It does this by concatenating all the elements in the list, then feeding it to MyHTMLParser.

        :param content: Pass in the content from the confluence page
        :return: The content of the page
        """
        full_string = ""
        for element in content:
            full_string += element
        my_parse = MyHTMLParser()
        my_parse.feed(full_string)
        return my_parse.content

    def fill_values_for_all_keys(self):
        """
        The fill_values_for_all_keys function fills the values for all keys in self.values_for_keys dictionary.
        The function uses other functions to get the values for some of the keys:
            - get_klocwork_findings(self) -> returns a dictionary with klockwork findings (lv1, lv2, lv3) from SWC json file
            - get_google_test_properties(self) -> returns a dictionary with google test properties from artifactory file google-test.properties
            - get__test__results__banner(self) -> returns banner string from xlsx report kpi

        :param self: Make the method callable from an instance of the class
        :return: A dictionary with the keys and values for the confluence page
        """
        def get_klocwork_findings(self):
            """
            The get_klocwork_findings function is used to extract the Klocwork findings from the JSON file.
            The function returns a dictionary with three keys: lv1, lv2 and lv3. The values of these keys are integers representing
            the number of findings for each level.

            :param self: Represent the instance of the class
            :return: A dictionary with the following keys:
            """
            json_input_file = os.path.join(self.output_folder, "SWC_Release_Notes_{}_Continental.json".format(self.version))
            with open(json_input_file, "r") as file:
                json_dict = json.load(file)
            klocwork_findings = {
                "lv1": json_dict["kpis"]["serious_difference"],
                "lv2": json_dict["kpis"]["considerable_difference"],
                "lv3": json_dict["kpis"]["marginal_difference"],
            }
            return klocwork_findings

        def get_google_test_properties(self):
            """
            The get_google_test_properties function downloads the google_test.properties file from artifactory,
                and parses it to return a dictionary of test names as keys and their pass/fail percentage as values.

            :param self: Represent the instance of the class
            :return: A dictionary with the following structure:
            """
            file_path_for_download = "/".join([self.artifactory_repo, self.release_id, self.sw_version, self.google_test_file])
            print(file_path_for_download)
            print(self.google_test_file_with_path)
            download_file_from_artifactory(file_path_for_download, self.google_test_file_with_path)
            with open(self.google_test_file_with_path, "r") as file:
                google_test_prop = file.readlines()
            result_dict = {}
            for line in google_test_prop:
                line_splitted = line.split()
                for element in line_splitted:
                    if "%" in element:
                        result_dict.update({line_splitted[0]: element})
                        break
            return result_dict

        def get_test_results_banner(self):
            """
            The get_test_results_banner function returns the banner of the test results.

            :param self: Represent the instance of the class
            :return: The value of the cell b2 in the sw+data sheet
            """
            xlsx_file = os.path.join(self.output_folder, "kpi_report.xlsx")
            wb = load_workbook(xlsx_file, data_only=True)

            # get ressource_cpu_measure_release
            sheetname = "SW+Data"
            check_sheetname_in_excel(wb, sheetname, xlsx_file)
            sheet = wb[sheetname]
            banner = sheet["B2"].value
            return banner

        def get_at_gmr(self):
            """
            The get_at_gmr function is used to get the GMR from the ati_output.txt file in Artifactory.
            The function takes no arguments and returns a string containing the GMR.

            :param self: Represent the instance of the class
            :return: The gmr of the ati_output
            """
            main_file_path = "/".join([self.artifactory_repo, self.release_id, self.sw_version, "Test_Results"])
            second_part_of_artifactory_path = "LOGS/ati_output.txt"
            download_file_from_artifactory_test_results(main_file_path, second_part_of_artifactory_path, self.at_gmr_file_with_path)
            with open(self.at_gmr_file_with_path, "r") as file:
                content = file.readlines()
            search_str = "Revision: "
            for line in content:
                if search_str in line:
                    return_value = line.split(search_str)[1]
                    return return_value

        def get_rrr_confluence_pate_content(self, key):
            """
            The get_rrr_confluence_pate_content function takes a key as an argument and returns the content of that key.
            The function first splits the key into its parts, which are separated by "--". The first part is used to find
            the starting point in self.confluence_content (which is a list of all lines from the confluence page). Then,
            the last part of the key is used to find where in self.confluence_content that line starts with "<h" and contains
            that last part of the key. Once found, it will return everything between this line and either another <h> or <p>Jira

            :param self: Refer to the instance of the class
            :param key: Find the line in the confluence_content list where we want to start looking for
            :return: The content of a confluence page
            """
            def filter_code_and_table(content):
                """
                The filter_code_and_table function takes in a string of HTML content and returns the following:
                    - If the string contains both <code> tags and <table> tags, it will return only the table.
                    - If there are no tables, but there is code, it will return False.
                    - Otherwise (if there is neither code nor tables), it will return the original input.

                :param content: Pass the content of a single element in the list
                :return: Either a table, false or the original content
                """
                if "<code>" in content or ("Loading..." in content and "Refresh" in content):
                    if "<table>" in content:
                        table_from_element = content.split("<table>")[1].split("</table>")[0]
                        table_from_element_str = "<table>{}</table>".format(table_from_element)
                        result_str = table_from_element_str
                    else:
                        result_str = False
                else:
                    result_str = content
                return result_str

            key_parts = key.split("--")[1:]

            # get starting point at self.confluence_content
            if len(key_parts) > 1:
                for i, element in enumerate(self.confluence_content):
                    if key_parts[0] in element:
                        line_in_confluence_for_key_one = i
                        break
            else:
                line_in_confluence_for_key_one = 0

            for i, element in enumerate(self.confluence_content[line_in_confluence_for_key_one:]):
                if key_parts[-1] in element:
                    found_line = line_in_confluence_for_key_one + i
                    break
            result_str = ""
            for i, element in enumerate(self.confluence_content[found_line + 1:]):
                if i == 0:
                    result = filter_code_and_table(element)
                    if result:
                        result_str = result
                else:
                    if not element.startswith("<h") and not element.startswith("<p>Jira Issues"):
                        result = filter_code_and_table(element)
                        if result:
                            result_str += result
                    else:
                        break
            return result_str

        klocwork_findings = get_klocwork_findings(self)
        google_test_prop = get_google_test_properties(self)
        for key in self.values_for_keys:
            if "otp_versions.txt" in key:
                key_part = key.split("--")[1]
                self.values_for_keys[key] = self.otp_versions_dict[key_part]
            elif key == "ReleaseDay--YY.WW.D":
                self.values_for_keys[key] = self.version_full.split("CW")[1]
            elif "SWC_json--Klockwork" in key:
                self.values_for_keys[key] = klocwork_findings[key.split("-")[-1]]
            elif key == "Test_Results--BANNER":
                self.values_for_keys[key] = get_test_results_banner(self)
            elif "google_test.properties" in key:
                self.values_for_keys[key] = google_test_prop[key.split("--")[1]]
            elif "Test_Results--at+gmr" in key:
                self.values_for_keys[key] = get_at_gmr(self)
            elif "ReleaseDate" in key:
                self.values_for_keys[key] = str(datetime.date.today())
            elif "RRR" in key:
                self.values_for_keys[key] = get_rrr_confluence_pate_content(self, key)

    def create_otp_versiosn_dict(self):
        """
        The create_otp_versiosn_dict function creates a dictionary of OTP versions and their corresponding
            download links. The function takes the path to the otp_versions.txt file as an argument, opens it,
            reads each line in the file and splits it into two parts: key (OTP version) and value (download link).
            Then it adds these key-value pairs to a dictionary which is returned by this function.

        :param self: Represent the instance of the class
        :return: A dictionary with the otp versions
        """
        otp_dict = {}
        with open(self.otp_version_file_with_path, "r") as otp_file:
            for line in otp_file.readlines():
                line_splitted = line.split("=")
                otp_dict.update({line_splitted[0]: line_splitted[1].strip()})
        return otp_dict

    def download_otp_versions_file_from_artifactory(self):
        """
        The download_otp_versions_file_from_artifactory function downloads the otp_versions.txt file from Artifactory
            and saves it to a local directory.

        :param self: Represent the instance of the class
        :return: The path to the file
        """
        repo = self.artifactory_repo
        path = "/".join([repo, self.release_id, self.sw_version, self.otp_versions_file])
        download_file_from_artifactory(path, self.otp_version_file_with_path)

    def get_all_keys(self):
        """
        The get_all_keys function returns a list of all keys in the template file.
            The function iterates over each line in the template file and checks if it contains a key_start_str.
            If so, it splits the line at this point and adds every element to a new list except for the first one (which is before
            key_start_str). Then, every element is split again at key_end_str and only its first part (before) is added to another
            list which will be returned by get all keys.

        :param self: Bind the method to an object
        :return: A list of all keys in the template file
        """
        list_of_keys = []
        for line in self.content_tmpl_file:
            if self.key_start_str in line:
                splittet = line.split(self.key_start_str)
                for i, element in enumerate(splittet):
                    if i == 0:
                        continue
                    else:
                        new_list_of_key_element = element.split(self.key_end_str)[0]
                        list_of_keys.append(new_list_of_key_element)
        return list_of_keys

    def create_dict_with_none_as_value(self):
        """
        The create_dict_with_none_as_value function creates a dictionary with the keys from the template file and None as
        the value for each key. This is used to create a dictionary that can be passed into the write_to_file function.

        :param self: Access the class attributes
        :return: A dictionary with the keys from the template file and none as values
        """
        return_dict = {}
        for element in self.keys_from_template_file:
            return_dict.update({element: None})
        return return_dict

    def create_set_type_of_keys(self):
        """
        The create_set_type_of_keys function creates a set of the keys from the template file.
            This is done to ensure that there are no duplicate keys in the template file.

        :param self: Represent the instance of the object itself
        :return: A set of the keys from the template file
        """
        self.keys_from_template_file = set(self.keys_from_template_file)

    def print_keys_from_template_file(self):
        """
        The print_keys_from_template_file function prints the keys from the template file.

        :param self: Refer toimages the object itself
        :return: A list of the keys from the template file
        """
        for element in self.keys_from_template_file:
            print(element)

    def write_and_save_generated_release_note_file(self):
        """
        The write_and_save_generated_release_note_file function is used to write the generated release note file.
        The function copies the Conti image file from templates/images/Aumovio.jpg to output/images/.
        Then it generates a markdown file with the content of self.content_tmpl_file and writes it into self.result_file_with_path.

        :param self: Make the method belong to the class
        :return: None
        """
        output_images_dir = os.path.join(self.output_folder, "images")
        if not os.path.exists(output_images_dir):
            os.mkdir(output_images_dir)
        shutil.copyfile(os.path.join(os.path.dirname(__file__), "templates", "images", "Aumovio.jpg"), os.path.join(output_images_dir, "Aumovio.jpg"))

        # generate markdown file
        with open(self.result_file_with_path, "w", encoding="utf-8") as output_file:
            for line in self.content_tmpl_file:
                if "<img_path>" in line:
                    line_splittet = line.split("<img_path>")
                    new_line = "{}{}{}".format(line_splittet[0], self.output_folder, line_splittet[1])
                    output_file.writelines(new_line)
                elif self.key_start_str in line:
                    output = ""
                    splittet = line.split(self.key_start_str)
                    for i, element in enumerate(splittet):
                        if i == 0:
                            output += element
                        else:
                            splittet_2 = element.split(self.key_end_str)
                            if self.values_for_keys[splittet_2[0]] is None:
                                print("WANRING! -> The following key was not set => {}".format(splittet_2[0]))
                                output += "{}{}{}".format(self.key_start_str, splittet_2[0], self.key_end_str)
                            else:
                                output += str(self.values_for_keys[splittet_2[0]])
                            output += splittet_2[1]
                    output_file.writelines(output)
                else:
                    output_file.writelines(line)

        # PDF Generation
        convert_md2html(self.result_file_with_path)
        write_html2pdf(self.result_file_with_path, "document_theme")

        # Convert kpi_report.xlsx file to kpi_report.pdf
        kpi_report_xlsx_file = os.path.join(self.output_folder, "kpi_report.xlsx")
        kpi_report_pdf_file = os.path.join(self.output_folder, "kpi_report.pdf")
        cmd = "libreoffice --headless --convert-to pdf --outdir {} {}".format(self.output_folder, kpi_report_xlsx_file)
        print(cmd)
        os.system(cmd)

        # merge Release Note file with kpi report
        result_file = os.path.join(self.output_folder, self.result_file_with_path_pdf)
        tmp_result_file = os.path.join(self.output_folder, "CONMOD_5_G_TMP.pdf")
        os.rename(result_file, tmp_result_file)
        cmd = "pdfunite {} {} {}".format(tmp_result_file,
                                         kpi_report_pdf_file,
                                         result_file)
        print(cmd)
        os.system(cmd)

        # remove kpi_report.pdf and tmp_result_file
        os.remove(tmp_result_file)
        os.remove(kpi_report_pdf_file)


if __name__ == '__main__':
    document_version = "CONMOD_5_G_VbaselineVersion_cl43.md" if "cl43" in RELEASE_VERSION else "CONMOD_5_G_VbaselineVersion.md"
    file = os.path.join("/u01/app/jenkins/workspace/Conmod/Release/CONMOD-METAFILES-UPDATER/.launchers/conmod-cm/release_notes_creator/templates", document_version)
    version = keyring.get_password(SERVICE_NAME, RELEASE_VERSION)
    print(version)
    x = ReleaseNoteFileGenerator(RELEASE_ID, file, version, "output")
    pprint(x.values_for_keys, indent=2)
    pprint(x.otp_versions_dict)
    pprint(x.values_for_keys, indent=2)
    x.write_and_save_generated_release_note_file()
