# -*- coding: utf-8 -*-
#!/usr/bin/python3
# *****************************************************************************
# *
# *  (c) 2023 Continental Automotive Systems, Inc., all rights reserved
# *
# *  All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *  Any reproduction of this material without written consent from
# *  Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: check_qcn_files.py
# *
# *   Description:  Compare the xqcn files with the xqcn_table file
# *   and remove not neccessary xqcn files from manufacturing package.
# *
# *
# *****************************************************************************

import os
import argparse


def xqcn_diff_and_copy(path_for_xqcn_files):
    qcn_text_file = False

    # filter for all xqcn files in <source> dir
    all_files_of_path = os.listdir(path_for_xqcn_files)
    xqcn_files = []
    for file in all_files_of_path:
        if file.endswith(".txt") and "QCN_table" in file:
            qcn_text_file = file
        elif file.endswith(".xqcn"):
            xqcn_files.append(file)

    # read <qcn>.txt file
    if qcn_text_file:
        qcn_text_file_path = os.path.join(path_for_xqcn_files, qcn_text_file)
        print("The qcn_table file is => '{}'".format(qcn_text_file_path))
        with open(qcn_text_file_path, "r") as file:
            qcn_txt_content = file.readlines()
    else:
        print("No qcn table file was found in {}".format(path_for_xqcn_files))

    # Create a list of qcn files form qcn_table file
    list_of_xqcn_files_from_xqcn_table_file = []
    for element in qcn_txt_content:
        if not element.startswith("#"):
            list_of_xqcn_files_from_xqcn_table_file.append(element.strip().split(":")[1])

    # compare the xqcn files with the content of the xqcn_table file and remove these, which are not in the
    # xqcn_table file
    for file in xqcn_files:
        if file.split(".")[0] not in list_of_xqcn_files_from_xqcn_table_file:
            file_with_path = os.path.join(path_for_xqcn_files, file)
            print("Delete => '{}' from '{}'".format(file, path_for_xqcn_files))
            os.remove(file_with_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", dest="path", type=str,
                        help="The path for the used xqcn files", required=True)
    args = parser.parse_args()
    path_for_xqcn_files = args.path
    xqcn_diff_and_copy(path_for_xqcn_files)
