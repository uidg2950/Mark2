#!/usr/bin/python
"""
# ******************************************************************************
# *
# *   (c) 2026 Aumovio, Inc., all rights reserved
# *
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename:     abi_contract_generator.py
# *
# *   Description:  This python file detect changes that (potentially) could
# *                 cause PositioningProc failures.
# *                 Targets:
# *                       - Toolchain Libraries
# *                       - minimum required versions
# *                       - Telux Headers
# *
# *****************************************************************************
"""
# Imports
import datetime
import json
import os
import sys

# Adding new Path
currentdir =os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

# Conmod utils
from cmlib import util
from abi_utils import *

## Script Variables
workspace = sys.argv[1]

# Dicts
libs, libs_ver, headers, output_json, metadata = {}, {},{},{},{}
abi_contract_file = "abi_contract.json"
toolchain_manifest = workspace + "/release-toolchain/docs/manifest.xml"
snaptel_path= workspace + "/package/codeaurora/caf-snaptel-sdk/"

# Metadata - Date
metadata["generated"] = str(datetime.datetime.now())
# Metadata - Toolchain version
toolchain_version = cmd_exec('git --git-dir="release-toolchain/.git" log --pretty="%s"')
metadata["toolchain_version"] = toolchain_version.split(" ")[0]

# pushd -> workspace
os.chdir(workspace)
# Toolchain Paths
util.header2("Checking Toolchain library paths")
print("Looking for toolchain libraries in {}: \n".format(workspace))
for lib in toolchain_libs:
    try:
        lib_path = cmd_exec("find 'release-toolchain' -name {} | grep -E 'fs/devel/(usr|lib)/l'".format(lib))
        print("[x] {}".format(lib))
        libs[lib] = lib_path
    except:
        print("[] {}".format(lib))

# Library version verification
util.header2("Verifying  minimum required versions")
for tag in min_req_ver_ref.keys():
    lib_ref = "libc.so.6" if tag == "GLIBC" else "libstdc++.so.6"
    if lib_ref in libs.keys():
        tag_version = cmd_exec("readelf -V {} | grep -oP '{}_\\K[0-9.]+' | sort -V | tail -1".format(libs[lib_ref],tag))
        libs_ver[tag] = tag_version
# Printout
for k,i in libs_ver.items():
    # Version verification (only for logs )
    ok = "[OK]" if int(libs_ver[k].replace(".","")) >= int(min_req_ver_ref[k].replace(".","")) else "[]"
    print("{}: {} {}".format(k,i,ok))

# pushd -> caf-snaptel-skd
os.chdir(snaptel_path)
util.header2("Telux Headers - Hash")
print("Looking for Telux Headers in {}: \n".format(snaptel_path))
for header in telux_headers:
    try:
        header_path = cmd_exec("find . -name {}".format(header))
        header_hash = cmd_exec("git rev-list -1 HEAD -- {}".format(header_path))
        print("[x] {}".format(header_path))
        headers[header_path] = header_hash
    except:
        print("[] {}".format(header))
os.chdir(workspace)

# Populate dicts for finale json file
output_json["metadata"] = metadata
output_json["toolchain_libs"] = libs
output_json["min_required_versions"] = libs_ver
output_json["telux_headers"] = headers

# Generating json file
with open(abi_contract_file, 'w') as fp:
    json.dump(output_json, fp, indent=4)

# Final report
# comparison file will be generated in "workspace"
util.header2("ABI compatibility report")
print('"{}" file generated and stored in {}'.format(abi_contract_file,workspace))
util.header2("END OF EXECUTION")
