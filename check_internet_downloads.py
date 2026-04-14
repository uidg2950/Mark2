#!/usr/bin/python
"""
# *****************************************************************************
# *
# * (c) 2022 Continental Automotive Systems, Inc., all rights reserved
# *
# * All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# * Any reproduction of this material without written consent from
# * Continental Automotive Systems, Inc. is strictly forbidden.
# *
# * Filename:       check_internet_downloads.py
# *
# * Description:    Search for all downloads from the internet inside the workarea.
# *
# ******************************************************************************
"""

import sys
import re
import os
import subprocess

# This is requiered due python 3 doesn't support relative references
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import cmlib

# Directories
try:
    buidir = os.environ['BUIDIR']
    scrdir = os.environ['SCRDIR']
    docdir = os.environ['DOCDIR']
except KeyError:
    raise BaseException("ERROR: environment not set")

class __Filter(object):
    """
    Search for specified commands executed from all files of a specified path (downloads from the internet).
    Filter the result for specified file endings.
    Create a csv file for all types (opensource-, conti-package- or local- downloads).
    Save the files in a specified path.
    """
    __header = "Package Name; Gerrit Path; Version (Revision); Full Gerrit Path; Executed Command\n"
    __re_commands = r"(^|\s+|\"|\')((wget|curl)|(?=git\s+(?=clone|fetch|submodule))).*\s+(git(\:\/\/|@)|https?:\/\/).*"
    __re_files = r"(.*\.(c|h|cpp|txt|md|info|log)\:.*)"
    __re_file_path = r"^\.(.*?)\:\d+\:(.*)"
    __search_path = None
    __result = None
    __conti = ""
    __opensource = ""
    __local = ""

    def __init__(self, search):
        """
        Contructor
        search: search path
        save: save path
        """
        self.__search_path = search
        pass

    def apply_filter(self):
        """
        Apply filter for specified search path and save the result in a local var
        """
        __byte_output = subprocess.check_output('grep -Ern "' + self.__re_commands + '" ' + self.__search_path +
                                                ' | grep -Ev "' + self.__re_files + '"', shell=True)
        self.__result = __byte_output.decode("utf-8")
        self._to_csv()

    def _to_csv(self):
        """
        Bring the filtered results into a csv format
        """
        __conti_tmp = ""
        __opensource_tmp = ""
        __local_tmp = ""

        # Create manifest with specific gerrit revisions
        os.chdir(self.__search_path)
        os.system("repo manifest -r -o tmp-manifest")

        # Go trough all lines and filter for binary files, packages and local files
        for line in self.__result.split("\n"):
            line = line.replace(";", ":")
            if "Binary file" in line:
                __local_tmp += line + "\n"
            elif "/package/" in line:
                try:
                    __path_to_file = re.search(self.__re_file_path, line).group(1)
                except AttributeError:
                    __path_to_file = re.search(self.__re_file_path, line)
                try:
                    __download_command = re.search(self.__re_file_path, line).group(2)
                except AttributeError:
                    __download_command = re.search(self.__re_file_path, line)
                
                if __path_to_file is not None:
                    __split_path_name = __path_to_file.split("/", 4)
                    __project_path = __split_path_name[1] + "/" + __split_path_name[2] + "/" + __split_path_name[3]
                    __package_name = __split_path_name[3]
                    __revision = re.search(r'path=\"' + __project_path +
                                '\"\srevision=\"([a-zA-Z0-9])*\"', open("tmp-manifest", "r").read())
                    if __revision and __download_command:
                        if "conti" in line:
                            __conti_tmp += __package_name + "; p1/" + __project_path + "; " +\
                                __revision.group(1) + "; p1" + __path_to_file + "; " + __download_command + "\n"
                        else:
                            __opensource_tmp += __package_name + "; p1/" + __project_path + "; " + __revision.group(1) +\
                                        "; p1" + __path_to_file + "; " + __download_command + "\n"
            else:
                __local_tmp += line + "\n"

        # Save the csv generated output to local vars
        self.__conti = __conti_tmp
        self.__opensource = __opensource_tmp
        self.__local = __local_tmp

    def save_files(self, save_path):
        """
        Put content of local vars to specified path + file.
        The files will only be created if the script has found something.
        """
        if self.__opensource != "":
            with open(save_path + "/internet-downloads-opensource.csv", "w+") as __file:
                __file.write(self.__header)
                __file.write(self.__opensource)
                print("Internet downloads (" + str(len(self.__opensource.splitlines())-2) + ") inside opensource packages found!")
        if self.__conti != "":
            with open(save_path + "/internet-downloads-conti.csv", "w+") as __file:
                __file.write(self.__header)
                __file.write(self.__conti)
                print("Internet downloads (" + str(len(self.__conti.splitlines())-2) + ") inside Continental packages found!")
        if self.__local != "":
            with open(save_path + "/internet-downloads-local.csv", "w+") as __file:
                __file.write(self.__local)
                print("Internet downloads (" + str(len(self.__local.splitlines())-1) + ") inside local files found!")

if __name__ == "__main__":
    try:
        if len(sys.argv) == 3:
            __search_path = sys.argv[1]                               # workspace
            __baseline_name = sys.argv[2]                             # baseline name

            # Path Definition
            __release_id = __baseline_name.split('.')[0]+'.y'         # release_id can be used instead
            __reldir = os.path.abspath(os.path.join(docdir, "..", "releases"))
            __path_to_save_output = os.path.join(__reldir, __release_id + "/" + __baseline_name + "-devel")

            if os.path.isdir(__path_to_save_output):
                __path_to_save_output = os.path.join(__path_to_save_output, "FOSS-download") # creating output directory
                if not os.path.isdir(__path_to_save_output):
                    os.mkdir(__path_to_save_output)
                download_filter = __Filter(__search_path)
                download_filter.apply_filter()
                download_filter.save_files(__path_to_save_output)
                exit(0)
            else:
                print("Baseline Directory not found")
                exit(1)
        else:
            raise IndexError
    except IndexError:
        print("Use the following Syntax:")
        print("python3 check_internet_downloads.py [search path] [baseline version]")
        exit(1)
