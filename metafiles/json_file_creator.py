#!/usr/bin/python
"""
# ******************************************************************************
# *
# *   (c) 2024-2026 Continental Automotive Systems, Inc., all rights reserved
# *
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename:     json_file_creator.py
# *
# *   Description:  This python file generates metafiles for ConMod delivery.
# *                 This script needs to be nested into telematics-cm repository.
# *
# *****************************************************************************
"""
import subprocess
import sys
import json
import glob
import os
import re
import hashlib
from urllib import request

# This is requiered due python 3 doesn't support relative references
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from cmlib import artifactory, util

try:
    buidir = os.environ['BUIDIR']
    scrdir = os.environ['SCRDIR']
    docdir = os.environ['DOCDIR']
except KeyError:
    raise BaseException("ERROR: environment not set")

def map_additional_metafiles(pattern):
    """
    Check all available documents with provided pattern
    :param pattern: Lookup pattern for files e.g *.pdf
    :return: a dict with files
    """
    if pattern:
        additional_release_documents = {}
        artifactory_metadata = artifactory.get_metainfo(baseline_version, release_id=release_id)["children"]
        pattern = pattern.replace("*", "")  

        for item in artifactory_metadata:
            for file in pattern.split(";"):
                if item["uri"][1:] == file:
                    name = item["uri"][1:]
                    additional_release_documents[name] = item["uri"][1:]
                elif item["uri"].endswith(file):
                    name = item["uri"][1:].replace(file, "")
                    additional_release_documents[name] = item["uri"][1:]

        return additional_release_documents
    else:
        return None

def check_files(pattern, display, subfolder = ""):
    """
    Check for existing and gives metainformation for file by pattern
    :param pattern: Lookup pattern
    :param display: Displayed filename
    :return: a dict with file metainfo
    """

    print('-'*50)
    print("Consistency check: {}".format(display))
    folder_url="{}/{}".format(baseline_version, subfolder)
    try:
      raw_folder_content = artifactory.get_metainfo(folder_url, release_id=release_id)
      re_pattern = re.compile(pattern)
      file_name=""

      for index in range(len(raw_folder_content["children"])):
          if re_pattern.match(raw_folder_content["children"][index]["uri"][1:]):
              file_name = raw_folder_content["children"][index]["uri"][1:]

      if file_name:
          file_metadata = artifactory.get_metainfo("{}/{}".format(folder_url, file_name), release_id=release_id)
          if not os.path.exists(file_name):
              artifactory.download_artifact("{}/{}".format(folder_url, file_name), "{}/{}".format(workspace, file_name), release_id=release_id)

          print("Calculating hash for: {}".format(file_name))
          hash_md5 = hashlib.md5()
          with open(file_name, "rb") as f:
              for chunk in iter(lambda: f.read(4096), b""):
                  hash_md5.update(chunk)

          if file_metadata["checksums"]["md5"] == hash_md5.hexdigest():
              return {'name': file_name, 'hash': hash_md5.hexdigest()}
          else:
              print("Local checksum and Artifactory checksum are not equal!")
              return None
      else:
          print("Can't find file with pattern: " + pattern)
          return {}
    except Exception as error:
      print("Error: " + str(error))
      return {}

def add_msm_to_release(msm_version, msm_file_pattern, subfolder=""):
    '''
    msm is now by default stored in artifactory/[project]/[release_id]/msn/[VERSION_MSM].
    The needed version is added here to artifactory release folder
    :param msm_version: msm version to be copied into the release. This version string is a substring of LINUX_VERSION in otp_file
    :param msm_file_pattern: Lookup pattern
    :param subfolder: subfolder to add to copy destination. Defaults to an empty string.
    :return: True if the msm file was successfully copied or is already contained in the release folder. False otherwise.
    '''
    res = False
    artifactory_msm_folder = "msm/{}".format(msm_version)
    artifactory_release_folder_url="{}/{}".format(baseline_version, subfolder)
    try:
      msm_folder_content = artifactory.get_metainfo(artifactory_msm_folder, release_id=release_id)
      re_pattern = re.compile(msm_file_pattern)
      file_name=""

      # check if a file matching msm_file_pattern exists in artifactory_msm_folder
      # iterating the 'children'
      for index in range(len(msm_folder_content["children"])):
          if re_pattern.match(msm_folder_content["children"][index]["uri"][1:]):
              # store match in 'file_name' and break iteration
              file_name = msm_folder_content["children"][index]["uri"][1:]
              break

      if file_name:
        # check, if the msm file was already added to this release...
        rel_folder_metadata = artifactory.get_metainfo(artifactory_release_folder_url, release_id=release_id, ret_as_text=True)
        if not file_name in rel_folder_metadata:
            # copy it in:
            print("Adding file {} to {}".format(file_name, artifactory_release_folder_url))
            msm_source_file = "{}/{}".format(artifactory_msm_folder, file_name)
            msm_dest_file   = "{}/{}".format(artifactory_release_folder_url, file_name)
            artifactory.copy_artifact(msm_source_file, msm_dest_file, release_id=release_id)
        else:
            print("MSM file {} is already present in the release folder! Nothing to do".format(file_name))
        res = True
    except Exception as error:
        print("Error: " + str(error))
    return res

def source_path_updater(release_id, target_file):
    '''
    "source" value into the target.json file depends on release_id.
    e.g "source": "/tp_sdk_conmod-sa515m-3.y_pkg/sdk"
    By default all the paths in the target.json template are
    "tp_sdk_conmo-sa515m-3.y_pkg" so that this should be updated depending on release_id value.
    '''

    tp_sdk_sdk_default="tp_sdk_conmod-sa515m-3.y_pkg"
    tp_sdk_sdk_to_replace="tp_sdk_{}_pkg".format(release_id)

    if tp_sdk_sdk_default != tp_sdk_sdk_to_replace:
        print("Updating path value in target.json file")
        with open(target_file, "r") as file:
            data = file.read()
            data = data.replace(tp_sdk_sdk_default,tp_sdk_sdk_to_replace)
        with open(target_file, 'w') as file:
            file.write(data)

# **** Main Execution Start *** #
try:
    workspace = sys.argv[1]
    baseline_version = sys.argv[2]     # conmod-sa515m-<clxx>-3.w.x.y
    release_id = sys.argv[3]       # conmod-sa515m-3.y / otp-sa515m-thick-3.y / conmod-sa515m-3.2.y
    delivery_type = sys.argv[4]    # "PreRelease"/"Engineering Drop"/"Continental Release"

except IndexError:
    util.warning("Wrong amount of Arguments")
    sys.exit()

# Sharedrive Paths
try:
    otp_file_metadata = artifactory.get_metainfo("{}/{}".format(baseline_version, "otp_versions.txt"), release_id=release_id)
    artifactory.download_artifact("{}/{}".format(baseline_version, "otp_versions.txt"), "{}/{}".format(workspace, "otp_versions.txt"), release_id=release_id)
    otp_file = os.path.join(workspace, 'otp_versions.txt')
except Exception as err:
    util.warning(str(err))
    util.warning("otp_versions.txt not found on Artifactory")
    sys.exit()

# Environment Paths
templates_dir = os.path.join(parentdir, 'templates/delivery')
ttemplate = "target.template.json"
dtemplate = "delivery.template.json" if release_id != "conmod-sa515m-cl43-3.y" else "delivery.template_cl43.json"
target_template = os.path.join(templates_dir, ttemplate)
delivery_template = os.path.join(templates_dir, dtemplate)

# Env Variables
base_version="-".join(baseline_version.split("-")[2:])
swc_rn_json="SWC_Release_Notes_{}_Continental.json".format(base_version)
bsw_json="Modem_BSW_delivery_manifest_SWC.json"
additional_release_documents_list = [ bsw_json, swc_rn_json ]

util.header("Generating JSON files for {}".format(baseline_version))
util.header2("Collecting file metadata")

rn = check_files("(TP_FERMI.*|CONMOD_5_G_.*)", "RELEASE_NOTE")
tst_results = check_files("Aumovio_ConMod_NAD_Test_Results_Rel.*","TEST_RESULTS")

# Release json Metafiles
ard = {}
for rel_doc in additional_release_documents_list:
    ard[rel_doc] = check_files(rel_doc, rel_doc)

kernel_amends = check_files("kernel_amend.tar.gz", "Kernel Amends")
if not kernel_amends:
    util.warning("Kernel Amends not found in artifactory")
    sys.exit()

if delivery_type != "Engineering Drop":
    sdk = check_files("tp_sdk.*.zip", "SDK", "otc")
else:
    sdk = check_files("tp_sdk.*.zip", "SDK", "sdk")
    if not sdk:
        util.warning("Failed to find SDK package")
        sys.exit()

msm_version = None
msm_file_pattern = "msm-4.14.*.tar.gz"
# Extraction of QCOM Version
with open(otp_file, "r") as otp:
    qcom_version = ""
    msm_line = ""
    otp_lines = otp.readlines()
    qcom_found = False
    msm_found = False
    for line in otp_lines:
        if "QCOM_BOOT_VERSION" in line:
            qcom_version = line
            qcom_found = True
            temp_version = qcom_version.split('=')
            if len(temp_version) < 2:
                util.warning("Malformed qcom_version string {}".format(qcom_version))
                sys.exit()
            temp_version = temp_version[1].split('-')
            if len(temp_version) < 1:
                util.warning("Malformed qcom_version string {}".format(qcom_version))
                sys.exit()
            qcom_version = temp_version[0]
        if "LINUX_VERSION" in line:
            # extract msm artifactory version string
            # e.g. LINUX_VERSION=LE.UM.4.1.1.c11-06200-sa515m-278-g626bf89
            # results in MSM_VERSION=LE.UM.4.1.1.c11-06200-sa515m
            msm_line = line
            msm_found = True
            temp_version = msm_line.split('=')
            if len(temp_version) != 2:
                util.warning("Malformed LINUX_VERSION line {}. Cannot extract MSM version string!".format(msm_line))
                sys.exit()
            split_word = "sa515m"
            LINUX_VERSION = temp_version[1]
            if split_word in LINUX_VERSION:
                msm_version = LINUX_VERSION[0:LINUX_VERSION.find(split_word)+len(split_word)]
            else:
                util.warning("Malformed LINUX_VERSION string {}. Cannot extract MSM version string!".format(LINUX_VERSION))
                sys.exit()
        if qcom_found == True and msm_found == True:
            break
    if qcom_version == "" or msm_version == None:
        util.warning("Failed to find QCOM_BOOT_VERSION or LINUX_VERSION")
        sys.exit()

# msm is now by default stored in artifactory/[project]/[release_id]/msn/[VERSION_MSM]. The needed version is added here to artifactory release
msm_ret = add_msm_to_release(msm_version, msm_file_pattern)
if msm_ret == False:
    util.warning("needed linux MSM release not found in artifactory msm folder!")
    sys.exit()
msm = check_files(msm_file_pattern, "MSM")
if not msm:
    util.warning("Linux MSM release not found in artifactory release folder!")
    sys.exit()

# Generating targe.json file
util.header2("Generating target.json")

if os.path.exists(target_template):
    with open(target_template, "r") as target:
        target_json = json.load(target)
        if "Engineering Drop" not in delivery_type:
            if rn:
                if rn['hash']:
                    print("Appending Release Notes")
                    target_json['METADATA'].append({
                        "destination": "/${releasenotes}/CONTINENTAL",
                        "variants": ["AU_ROW_NONE_DEV_UNIT", "AU_ROW_NONE_PROD_UNIT", "PO_ROW_NONE_DEV_UNIT", "PO_ROW_NONE_PROD_UNIT", "VW_ROW_MEB_DEV_UNIT", "VW_ROW_MEB_PROD_UNIT", "VWN_ROW_MEB_DEV_UNIT", "VWN_ROW_MEB_PROD_UNIT" ],
                        "source": '/' + rn['name'],
                        "type": "file"
                    })
            if tst_results:
                if tst_results['hash']:
                    print("Appending Test Results")
                    target_json['METADATA'].append({
                        "destination": "/${releasenotes}/CONTINENTAL",
                        "variants": ["AU_ROW_NONE_DEV_UNIT", "AU_ROW_NONE_PROD_UNIT", "PO_ROW_NONE_DEV_UNIT", "PO_ROW_NONE_PROD_UNIT", "VW_ROW_MEB_DEV_UNIT", "VW_ROW_MEB_PROD_UNIT", "VWN_ROW_MEB_DEV_UNIT", "VWN_ROW_MEB_PROD_UNIT" ],
                        "source": '/' + tst_results['name'],
                        "type": "file"
                    })
            if ard:
                for item in ard:
                    print("Appending {}".format(item))
                    if ard[item]['hash']:
                        target_json['METADATA'].append({
                        "destination": "/${releasenotes}/CONTINENTAL",
                        "variants": ["AU_ROW_NONE_DEV_UNIT", "AU_ROW_NONE_PROD_UNIT", "PO_ROW_NONE_DEV_UNIT", "PO_ROW_NONE_PROD_UNIT", "VW_ROW_MEB_DEV_UNIT", "VW_ROW_MEB_PROD_UNIT", "VWN_ROW_MEB_DEV_UNIT", "VWN_ROW_MEB_PROD_UNIT" ],
                        "source": '/' + ard[item]['name'],
                        "type": "file"
                })

        with open("{}/target.json".format(workspace), 'w+') as toutfile:
            json.dump(target_json, toutfile, indent=2)

        # Updating "source"  value in target.json file
        source_path_updater(release_id,"{}/target.json".format(workspace))

        artifactory.upload_artifact("{}/target.json".format(workspace), "{}/target.json".format(baseline_version), release_id=release_id)
        target_meta = check_files("target.json", "target.json")
else:
    util.warning("target.json template not found", error=True)
    sys.exit()

# Generating delivery.json file
util.header2("Generating delivery.json")

if os.path.exists(delivery_template):
    print("template file: {}".format(delivery_template))
    with open(delivery_template, "r") as delivery:
        delivery_json = json.load(delivery)

        delivery_json['versions']['delivery'] = baseline_version
        delivery_json['Fileset'][msm['name']] = msm['hash']
        delivery_json['Fileset'][sdk['name']] = sdk['hash']
        delivery_json['Fileset'][target_meta['name']] = target_meta['hash']
        if "Engineering Drop" not in delivery_type:
            if rn:
                if rn['hash']:
                    delivery_json['Fileset'][rn['name']] = rn['hash']
            if tst_results:
                if tst_results['hash']:
                    delivery_json['Fileset'][tst_results['name']] = tst_results['hash']
            if ard:
                for item in ard:
                    if ard[item]['hash']:
                        item_name = ard[item]['name']
                        item_hash = ard[item]['hash']
                        delivery_json['Fileset'][item_name] = item_hash
        delivery_json['Fileset'][kernel_amends['name']] = kernel_amends['hash']
        delivery_json['unpack'].append(sdk['name'])

        delivery_json['versions']['Qualcomm'] = qcom_version

        with open("{}/delivery.json".format(workspace), 'w+') as doutfile:
            json.dump(delivery_json, doutfile, indent=2)

        artifactory.upload_artifact("{}/delivery.json".format(workspace), "{}/delivery.json".format(baseline_version), release_id=release_id)

else:
    util.warning("delivery.json template not found", error=True)
    sys.exit()

# Resume
util.header2("Output files")
print("target.json = {}{}{}/{}/{}".format(artifactory.artifactory_server, artifactory.repository_path, release_id, baseline_version, "target.json"))
print("delivery.json = {}{}{}/{}/{}".format(artifactory.artifactory_server, artifactory.repository_path, release_id, baseline_version, "delivery.json"))

util.header("END OF EXECUTION")
