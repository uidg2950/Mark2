# *****************************************************************************
# *
# * (c) 2023 Continental Automotive Systems, Inc., all rights reserved
# *
# * All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# * Any reproduction of this material without written consent from
# * Continental Automotive Systems, Inc. is strictly forbidden.
# *
# * Filename:    manifest.py
# *
# * Description: Interacts with the manifest files
# *
# * Revision History:
# *
# *  CQ#    Author           Date          Description of Change(s)
# *  -----  -------------    ----------    ------------------------------------
# *         uidu3800         2023-01-25    Init version
# *
# *****************************************************************************


import os
import xml.etree.ElementTree as ET


class Manifest:
    PROJ_NAME_SEPARATOR = "__"
    PROJ_MANIFEST_FILE_KEY_NAME = "manifest_file"

    def __init__(self, workdir, main_manifest_file):
        """
        The __init__ function is called when the class is instantiated.
        It takes two arguments: workdir and main_manifest_file.
        The workdir argument specifies the directory where all of the manifest files are located, and main_manifest_file specifies which file to use as a reference for reading in other manifest files.

        :param self: Access variables that belongs to the class
        :param workdir: Set the working directory
        :param main_manifest_file: Store the path to the main manifest file
        :return: The workdir, main_manifest_file and manifest_files variables
        """
        self.workdir = workdir
        self.main_manifest_file = os.path.join(workdir, main_manifest_file)
        self.manifest_files = [self.main_manifest_file]
        self.main_manifest_inclue_projects_data = {}
        self.projects = {}

        for element in self.manifest_files:
            self.fill_manifest_files_and_projects(element)

    def fill_manifest_files_and_projects(self, manifest_file):
        """
        The fill_manifest_files_and_projects function fills the manifest_files and projects attributes of the Manifest class.
        It does this by parsing a manifest file (manifest_file) and looking for include-projects tags in it.
        If found, it will look for those projects in other included manifests (recursively). If not found, it will look for them
        in the main manifest file itself. It then adds all project data to self.projects as well as adding all included manifests
        to self.manifest_files.

        :param self: Access the class attributes
        :param manifest_file: Store the path to the manifest file
        :return: None
        """
        main_tree = ET.parse(manifest_file)
        root = main_tree.getroot()

        for incl_proj in root.iter("include-project"):
            manifest_file_with_path = os.path.join(self.workdir, incl_proj.attrib["path"], incl_proj.attrib["manifest-file"])
            self.manifest_files.append(manifest_file_with_path)

            self.main_manifest_inclue_projects_data.update({manifest_file_with_path: incl_proj.attrib})

        for proj in root.iter("project"):
            proj_name = proj.attrib["name"]
            try:
                proj_branch = proj.attrib["upstream"].rsplit("/")[-1]
            except:
                proj_branch = "None"
            project_key = "{}{}{}".format(proj_name, Manifest.PROJ_NAME_SEPARATOR, proj_branch)
            if project_key in self.projects:
                raise Exception("The project key '{}' are double in the manifests \n({} ==>\n{})".format(project_key,
                                                                                                     self.projects[project_key],
                                                                                                     proj.attrib))
            else:
                self.projects.update({project_key: proj.attrib})
                self.projects[project_key].update({Manifest.PROJ_MANIFEST_FILE_KEY_NAME: manifest_file})

    def change_revision_and_upstream_of_manifest(self, manifest_file, project_data, new_revision, new_upstream):
        """
        The change_revision_and_upstream_of_manifest function takes a manifest file and project data,
        and changes the revision and upstream attributes of the project in that manifest.


        :param self: Allow the function to access the class attributes
        :param manifest_file: Specify the path to the manifest file
        :param project_data: Store the name and path of the project
        :param new_revision: Set the new revision of the project
        :param new_upstream: Set the upstream of a project
        :return: The new revision and upstream of the project
        """
        main_tree = ET.parse(manifest_file)
        root = main_tree.getroot()
        proj_name = project_data["name"]
        proj_path = project_data["path"]
        for proj in root.iter("project"):
            if proj.attrib["name"] == proj_name and proj.attrib["path"] == proj_path:
                print("name of the project => '{}'".format(proj.attrib["name"]))
                print("old revision => '{}'".format(proj.attrib["revision"]))
                print("old upstream => '{}'".format(proj.attrib["upstream"]))
                proj.attrib["revision"] = new_revision
                proj.attrib["upstream"] = new_upstream
                print("new revision => '{}'".format(proj.attrib["revision"]))
                print("new upstream => '{}'".format(proj.attrib["upstream"]))
        main_tree.write(manifest_file, encoding="UTF-8", xml_declaration=True)

    def change_revision_and_upstream_of_included_manifest_files_in_main_manifest_file(self, main_manifest_file_with_path, sub_manifest_file, new_revision, new_upstream):
        """
        The change_revision_and_upstream_of_included_manifest_files_in_main_manifest_file function :
            - takes a path to the main manifest file as an argument, and
            - changes the revision and upstream attributes of all include-project tags in that main manifest file to match those of their corresponding sub-manifest files.

        :param self: Reference the class instance
        :param main_manifest_file_with_path: Specify the path to the main manifest file
        :param sub_manifest_file: Specify the name of the sub-manifest file which is included in the main manifest file
        :param new_revision: Set the new revision of the sub_manifest_file
        :param new_upstream: Set the new upstream of the sub-manifest file
        :return: The revision and upstream of the included manifest files in the main manifest file
        """
        main_tree = ET.parse(main_manifest_file_with_path)
        root = main_tree.getroot()
        for include_project in root.iter("include-project"):
            if include_project.attrib["manifest-file"] == sub_manifest_file:
                print("name of the manifest-file => '{}'".format(include_project.attrib["manifest-file"]))
                print("old revision => '{}'".format(include_project.attrib["revision"]))
                print("old upstream => '{}'".format(include_project.attrib["upstream"]))
                include_project.attrib["revision"] = new_revision
                include_project.attrib["upstream"] = new_upstream
                print("new revision => '{}'".format(include_project.attrib["revision"]))
                print("new upstream => '{}'".format(include_project.attrib["upstream"]))
            main_tree.write(main_manifest_file_with_path, encoding="UTF-8", xml_declaration=True)

if __name__ == "__main__":
    manifest_file = os.path.join(".repo", "manifests", "default.xml")
    manifest_obj = Manifest("workdir", manifest_file)
    print("nnnn")
    print(manifest_obj.manifest_files)
    print("#####")
    #print(manifest_obj.projects)
    for element in manifest_obj.projects:
        print("{} => {}".format(element, manifest_obj.projects[element]))
    for element in manifest_obj.manifest_files:
        print(element)


    print("\n"*7)
    manifest_file = "workdir/.repo/manifests/default.xml"
    project_name = "p1/project/otp/main"
    new_revision = "asdfwqer"
    upstream = "refs/heads/robs_test"
    manifest_obj.change_revision_and_upstream_of_manifest(manifest_file, project_name, new_revision, upstream)