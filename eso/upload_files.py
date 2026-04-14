#!/usr/bin/env python3
"""
# *****************************************************************************
# *
# * (c) 2022 Continental Automotive Systems, Inc., all rights reserved
# *
# * All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# * Any reproduction of this material without written consent from
# * Continental Automotive Systems, Inc. is strictly forbidden.
# *
# * Filename:     upload_files.py
# *
# * Description:  Script to upload SDK content to ETF.
# *
# ************** ***************************************************************
"""

import sys
import lib_etf
import logging

import os
import glob
import shutil
from urllib.parse import urlparse
from argparse import ArgumentParser as ap
from cmlib import artifactory
import fnmatch

etf = None
logger = logging.getLogger(__name__)

# Parse command line arguments
def _parse_args():
    parser = ap(description="Script to download files from eSolutions for bundle generation.")

    parser.add_argument("-w", "--workspace",  required=True,
            help="Workspace of script.")
    parser.add_argument("-r", "--release_id",  required=True,
            help="Release id of sdk to upload.")
    parser.add_argument("-b", "--baseline_version",  required=True,
            help="Baseline version of sdk to upload.")
    parser.add_argument("-d", "--destination", required=True,
            help="Destination path on ETF share.")
    parser.add_argument("-f", "--file_list", required=True,
            help="List of files to upload.")

    return parser.parse_args()

# service function to get ID from url
def is_url_path(url):
    try:
        return urlparse(url).query.split("=")[1]
    except Exception as err:
        logger.info("Path {} is not proper etf url. Catched error".format(url, err))
    return None

# service function to get ID of destination folder
def extract_id(item_path, parent_id = 1):
    item_id = is_url_path(item_path)
    if item_id is not None:
        return item_id
    else:
        path_items = item_path.split("/")
        for folder_name in path_items:
            folder_content = etf.list(parent_id)["content"]
            found_folder = False
            logger.debug("Lookup of {} inside {}".format(folder_name, folder_content))
            for subfolder in folder_content:
                logger.debug("Compare {} with {}".format(folder_name, subfolder["title"].encode('utf-8')))
                if fnmatch.fnmatch(subfolder["title"], folder_name):
                    found_folder = True
                    parent_id = subfolder["id"]
                    break
            if not found_folder:
                logger.info("Folder with name not found {}. Create new one".format(folder_name))
                mkdir_etf_id = etf.mkdir(parent_id, folder_name)
                logger.info("ETF-ID of the new folder: " + str(mkdir_etf_id))
                parent_id = mkdir_etf_id
        logger.info("final_ID: {}".format(parent_id))
        return parent_id

# Initialization of network connection and ETF library
def init():
    try:
        os.environ["http_proxy"] = "http://cntlm:3128"
        os.environ["https_proxy"] = "http://cntlm:3128"
        lib_etf.root_logger_setup(False, True)
        credentials={"username" : "ConMod_Conti_SysInt", "password" : "T3l30p3ncm"}
        global etf
        etf = lib_etf.ETF("Continental", "upload_files_to_etf.py", "0.1.1", interactive=False, credentials=credentials,
                              verbose=3,
                              root_logger=False, beta_server=False, timeout = 2 * 60)
    except Exception as err:
        logger.critical("Unexpected {}".format(err))
        sys.exit(1)

def remove_prefix(uri, prefix):
    if uri.startswith(prefix):
        return uri[len(prefix):]
    return uri  # or whatever

def upload_file(workspace, file_pattern, release_id, parent_item, destination_folder):
  path_items = file_pattern.split("/")
  found_items = []
  for folder_name in path_items:
      logger.info("Lookup for {} inside {}".format(folder_name, parent_item))
      if found_items:
        parent_item += found_items[0]
      folder_info = artifactory.get_metainfo(parent_item, release_id=release_id)["children"]
      found_items = []

      for subfolder in folder_info:
        logger.debug("Compare {} with {}".format(folder_name, subfolder["uri"]))
        if fnmatch.fnmatch(remove_prefix(subfolder["uri"], "/"), folder_name):
          found_items.append(subfolder["uri"])

      if not found_items:
        logger.warning("Failed to find {} on artifactory folder: {}".format(folder_name, parent_item))
        return False
  for upload_item in found_items:
    file_in_workspace = workspace + upload_item
    downloadable_file = parent_item + upload_item
    logger.info("Download file from artifactory: {} and save as {}".format(downloadable_file, file_in_workspace))
    artifactory.download_artifact(downloadable_file, file_in_workspace, release_id=release_id)
    logger.info("Upload file to etf: {}".format(file_in_workspace))
    upload_etf_id = etf.upload(etf_id=destination_folder, input_file=file_in_workspace)
    logger.info("Saved as ETF-ID: " + str(upload_etf_id))
  return True

############ Main Execution ############
def main():
    ret = 0
    try:
        args = _parse_args()
        init()

        source_sdk_dir = artifactory.get_metainfo(args.baseline_version, release_id=args.release_id)
        if not source_sdk_dir:
            logger.error("Could not find sdk dir {}".format(source_sdk_dir))
            return 1

        destination_folder = extract_id(args.destination)
        logger.debug("Destination folder: {}".format(destination_folder))

        for pattern in args.file_list.split(";"):
          upload_file(args.workspace, pattern, args.release_id, args.baseline_version, destination_folder)

        with open(args.workspace + "/etf_id", "w+") as f:
          f.write(destination_folder)
    except Exception as err:
        logger.critical("Unexpected {}".format(err))
        ret = 1
    return ret

if __name__ == "__main__":
    sys.exit(main())
