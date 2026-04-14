#!/usr/bin/python
"""
# ******************************************************************************
# *
# *   (c) 2020 Continental Automotive Systems, Inc., all rights reserved
# *
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename:     delivery-verification.py
# *
# *   Description:  This python file verify integraty of delivery files
# *
# *****************************************************************************
"""
import sys
import json
import glob
import os
import hashlib
import zipfile

# This is requiered due python 3 doesn't support relative references
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from cmlib import notification, util

try:
    buidir = os.environ['BUIDIR']
    scrdir = os.environ['SCRDIR']
    docdir = os.environ['DOCDIR']
except KeyError:
    raise BaseException("ERROR: environment not set")

# **** Main Execution Start *** #
try:
    workspace = sys.argv[1]
    release_id = sys.argv[2]
    baseline = sys.argv[3]    # otp-sa515m-thick-3.1.6.4.2
except IndexError:
    util.warning("Wrong amount of arguments", error=True)
    sys.exit()

# Sharedrive Paths
target_file = 'target.json'
sdk_zip_bundle = glob.glob(os.path.join(workspace, "tp_sdk_{}_pkg.zip".format(baseline)))
zip_path_pattern = "tp_sdk_{}_pkg".format(release_id)

sdk_zip_abspath = [os.path.abspath(glob_path) for glob_path in sdk_zip_bundle][0]
zip_file = zipfile.ZipFile(sdk_zip_abspath, "r")

# Verification of target.json file
util.header2("Verification integrity of delivery package")

if not os.path.exists(target_file):
    util.warning("target.json file not found", error=True)
    sys.exit()

util.header("Verification files base on target.json")
with open(target_file, "r") as target:
    target_json = json.load(target)
    for meta in target_json['METADATA']:
        print('Checking {}'.format(meta['source']))
        filepath = meta['source'].rstrip("/").lstrip("/")
        # check that filepath contains pattern of zip file if yes then check inside zip bundle otherwise inside staging directory
        if filepath.startswith(zip_path_pattern):
            if not any(filename.startswith("%s" % filepath) for filename in zip_file.namelist()):
                util.warning("File with name {} Not present inside zip filenames {}".format(meta['source'], zip_file.namelist()), error=True)
                sys.exit()
        else:
            if not os.path.exists(os.path.join(workspace, filepath)):
                util.warning("File with name {} Not present on staging folder".format(meta['source']), error=True)
                sys.exit()

util.header("END OF EXECUTION")

