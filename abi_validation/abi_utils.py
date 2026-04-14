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
# *   Filename:     abi_utils.py
# *
# *   Description:  Definitions/Declarations for abi verification scripts
# *
# *****************************************************************************
"""
import subprocess

## Lists of files to Audit
# Toolchain libraries to search
toolchain_libs = [ "libc.so.6", "libm.so.6", "libpthread.so.0", "libgcc_s.so.1", "libstdc++.so.6" ]

# Telux Headers to look for (hash)
telux_headers = [ "CommonDefines.hpp", "Version.hpp", "DgnssListener.hpp",
                   "DgnssManager.hpp", "LocationConfigurator.hpp", "LocationDefines.hpp",
                   "LocationFactory.hpp", "LocationListener.hpp", "LocationManager.hpp" ]

# Libraries minimum required version reference
min_req_ver_ref = { "GLIBC": "2.28", "GLIBCXX": "3.4.22", "CXXABI": "1.3.11", "GCC": "3.5" }

# cmd exec
def cmd_exec(cmd):
    try:
        cmd_output = subprocess.check_output(cmd,shell=True, universal_newlines=True).strip()
    except:
        print("Not possible to execute {}".format(cmd))

    return cmd_output
