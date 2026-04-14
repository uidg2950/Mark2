#!/usr/bin/python
"""
# ******************************************************************************
# *
# *   (c) 2023 Continental Automotive Systems, Inc., all rights reserved
# *
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename:     modem_bsw_delivery.py
# *
# *   Description:  This python file generates Modem_BSW_delivery_manifest_SWC.json for ConMod delivery.
# *
# *****************************************************************************
"""

import os
import sys
import json
from datetime import date

# This is requiered due python 3 doesn't support relative references
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from cmlib import artifactory, util

# **** Main Execution Start *** #
try:
    workspace = sys.argv[1]
    release_id = sys.argv[2]        # e.g. conmod-sa515m-3.y
    baseline_version = sys.argv[3]  # e.g. conmod-sa515m-3.4.0.0
except IndexError:
    util.warning("Wrong amount of Arguments")
    sys.exit()

# Environment Paths
templates_dir = os.path.join(parentdir, 'templates/delivery')
modem_bsw_template = os.path.join(templates_dir, 'Modem_BSW_delivery_manifest_SWC.template.json')
modem_bsw = os.path.join(parentdir, 'Modem_BSW_delivery_manifest_SWC.json')

util.header("Generating Modem_BSW_delivery_manifest_SWC JSON file for {}".format(baseline_version))

if os.path.exists(modem_bsw_template):
    template_data=dict()
    with open(modem_bsw_template) as template_file:
        template_data = json.load(template_file)

    template_data["metadata"]["version"] = baseline_version
    template_data["metadata"]["delivery"]["date"] = date.today().strftime("%d.%m.%Y")

    with open(modem_bsw, "w+") as modem_bsw_file:
        modem_bsw_file.write(json.dumps(template_data, indent=4))

    artifactory.upload_artifact(modem_bsw, "{}/Modem_BSW_delivery_manifest_SWC.json".format(baseline_version), release_id=release_id)
else:
    util.warning("Modem_BSW_delivery_manifest_SWC.json template not found", error=True)
    sys.exit()