#!/usr/bin/env python3
"""
# *****************************************************************************
# *
# * (c) 2022-2025 Continental Automotive Systems, Inc., all rights reserved
# *
# * All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# * Any reproduction of this material without written consent from
# * Continental Automotive Systems, Inc. is strictly forbidden.
# *
# * Filename:     update_swl_pack.py
# *
# * Description:  Script to update SWL package.
# *               SWL package used for generation of N-1 bundle
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
import fnmatch
from datetime import date
import tempfile
import zipfile
from cmlib import artifactory
import tempfile
import zipfile
import json

etf = None
logger = logging.getLogger(__name__)

# Parse command line arguments
def _parse_args():
    parser = ap(description="Script to download files from eSolutions for bundle generation.")

    parser.add_argument("-w", "--workspace",  required=True,
            help="Workspace of script.")
    parser.add_argument("-s", "--source_bundle", required=True,
            help="Source path of whole harman bundle on ETF share.")
    parser.add_argument("-u", "--usb_bundle_path", required=True,
            help="Source path on ETF share for USB bundle used for generation SWDL test bundle files.")
    parser.add_argument("-e", "--external_packages_path", required=False,
            help="Source path on ETF share for External packages used for generation SWDL test bundle files.")
    parser.add_argument("-r", "--release_id", required=True,
            help="Release ID where file should be uploaded")
    parser.add_argument("-n", "--no_upload", required=False, action='store_true',
            help="Optional flag to configure is upload to artifactory is necessary or not. Typically provided for manufacturing packages")
    parser.add_argument("-p", "--password", required=False,
            help="Password required for Update bundle.")

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
                logger.debug("Compare {} with {}".format(folder_name, subfolder["title"]))
                if fnmatch.fnmatch(subfolder["title"], folder_name):
                    found_folder = True
                    parent_id = subfolder["id"]
                    break
            if not found_folder:
                logger.critical("Failed to found {} inside {} folder childrens. Abort".format(folder_name, parent_id))
                sys.exit(1)
        logger.info("final_ID: {}".format(parent_id))
        return parent_id

#Get folder ids for usb_bundle and external packages
def extract_etf_links(source_bundle, usb_bundle_path, external_packages_path):
    source_id = extract_id(source_bundle)
    usb_id = extract_id(usb_bundle_path, source_id)
    if usb_id is None:
        logger.critical("Mailformed usb_bundle path. Exit from script")
        sys.exit(1)
    external_id = None
    if external_packages_path is not None:
      external_id = extract_id(external_packages_path, source_id)
      if external_id is None:
          logger.critical("Mailformed external_id path. Exit from script")
          sys.exit(1)

    ret_value = {'usb_id': usb_id, 'usb_title': etf.list(usb_id)["title"], 
            'parent_name':  etf.list(source_id)["title"]}

    if (external_id is not None):
        ret_value['external_id'] = external_id
        ret_value['external_title'] = etf.list(external_id)["title"]

    return ret_value

# Initialization of network connection and ETF library
def init():
    try:
        os.environ["http_proxy"] = "http://cntlm:3128"
        os.environ["https_proxy"] = "https://cntlm:3128"
        lib_etf.root_logger_setup(False, True)
        credentials = {"username" : "ConMod_Conti_SysInt", "password" : "T3l30p3ncm"}
        script_name = "Update swl bundle"
        script_version = "1.0.0"
        global etf
        etf = lib_etf.ETF("Continental", script_name, script_version, interactive=False, credentials=credentials,
                              verbose=3,
                              root_logger=False, beta_server=False)
    except Exception as err:
        logger.critical("Unexpected {}".format(err))
        sys.exit(1)

def remove_password(file_name, output_archive, password, workspace = None):
  tempdir = tempfile.mkdtemp(dir=workspace)
  logger.debug("remove_password: [{}] [{}] [{}]".format(file_name, output_archive, tempdir))
  with zipfile.ZipFile(file_name, 'r') as zipObj:
    zipObj.extractall(tempdir, pwd=bytes(password, encoding='utf-8'))
  archive_name = shutil.make_archive(output_archive, "zip", tempdir)
  logger.debug("New created archive: {}".format(archive_name))
  shutil.rmtree(tempdir)
  return archive_name

# download file by lookup_pattern from id folder into workspace, then uploads it to artifactory
def download_and_push(id, workspace, lookup_pattern, destination, release_id = "conmod-sa515m-3.y/", pwd = "", no_artifactory = False):
    if release_id[-1] != '/':
        release_id += '/'
    if not etf.download(etf_id=id, output_folder=workspace, existing_file_check_md5=True):
        logger.error("Failed to download file: {}".format(id))
        return False

    source_files = sorted(glob.glob("{}/{}".format(workspace, lookup_pattern)), key=os.path.getmtime)
    if not source_files:
        logger.error("Failed to find file: {}/{}".format(workspace, lookup_pattern))
        sys.exit(1)
    file_name = os.path.basename(source_files[-1])
    source = os.path.join(workspace, file_name)

    if pwd:
      source = os.path.join(workspace, "swl-bundle")
      source = remove_password(source_files[-1], source, pwd, workspace)
    if not no_artifactory:
      return artifactory.upload_artifact(source, destination, release_id)
    else:
      return True

#### function to parse and extract bundle version from source folder name
def extract_bundle_version(folder_name):
  file_name = "UNDEFINED"
  parts = folder_name.split("_")
  if len(parts) >= 3:
        file_name = parts[2]
  return file_name


############ Main Execution ############
def main():
    ret = 0
    try:
        args = _parse_args()
        init()
        etf_links = extract_etf_links(args.source_bundle, args.usb_bundle_path, args.external_packages_path)
        logger.debug("etf_links: {}".format(etf_links))

        bundle_version = extract_bundle_version(etf_links["parent_name"])

        if args.external_packages_path:
          if not download_and_push(etf_links["external_id"], args.workspace, "*.tgz", "{}/external-packages.tgz".format(bundle_version), release_id='conmod-swl', no_artifactory = args.no_upload):
              logger.error("Failed to process external packages")
              ret = 1

        if not download_and_push(etf_links["usb_id"], args.workspace, "*.zip", "{}/swl-bundle.zip".format(bundle_version), pwd = "SWUP_CMOD_42", release_id='conmod-swl', no_artifactory = args.no_upload):
            logger.error("Failed to process usb bundle")
            ret = 1

    except Exception as err:
        logger.critical("Unexpected {}".format(err))
        ret = 1
    return ret

if __name__ == "__main__":
    sys.exit(main())
