#!/bin/bash
# ***************************************************************************************
# *   Copyright (c) 2021-2022 Continental Automotive Systems, Inc., all rights reserved
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: prepare_etf.sh
# *
# *   Description: The main purposes of this script are:
# *    - Extract etf lib into workspace
# *
# ***************************************************************************************
SCRIPT_NAME=$(basename "${0}")
LOGFILE=$(dirname $0)/"${SCRIPT_NAME%.*}.log"
echo "LOGGING to ${LOGFILE}"
exec > >(tee "${LOGFILE}");

# ----------------------------------------------------------- #
# All output from commands in this block sent to file $LOGFILE.
echo "START: ${SCRIPT_NAME} $(date)"

WORKSPACE=${1?workspace is required}

echo "Import external libraries"
source "${WORKSPACE}/.launchers/conmod-cm/utils/platform-common.lib"

ETF_VERSION="2.6.7"
ESO_LIB_PATH="${WORKSPACE}/.launchers/conmod-cm/eso/lib_etf-${ETF_VERSION}.tar.gz"

header2 "Installation of lib_etf into workarea"

echo "> tar --extract --ungzip --file "${ESO_LIB_PATH}" --directory ${WORKSPACE}"
tar --extract --ungzip --file "${ESO_LIB_PATH}" --directory ${WORKSPACE}
[[ $? -ne 0 ]] && bail "unable to extract lib_etf to workspace"

echo "> cp ${WORKSPACE}/.launchers/conmod-cm/eso/update_swl_pack.py ${WORKSPACE}/lib_etf-${ETF_VERSION}"
cp ${WORKSPACE}/.launchers/conmod-cm/eso/update_swl_pack.py ${WORKSPACE}/lib_etf-${ETF_VERSION}
[[ $? -ne 0 ]] && bail "unable to copy update swl script to etf workspace"

echo "> cp ${WORKSPACE}/.launchers/conmod-cm/eso/upload_files.py ${WORKSPACE}/lib_etf-${ETF_VERSION}"
cp ${WORKSPACE}/.launchers/conmod-cm/eso/upload_files.py ${WORKSPACE}/lib_etf-${ETF_VERSION}
[[ $? -ne 0 ]] && bail "unable to copy upload bundle script to etf workspace"

echo "> cp -ar ${WORKSPACE}/.launchers/conmod-cm/cmlib/ ${WORKSPACE}/lib_etf-${ETF_VERSION}"
cp -ar ${WORKSPACE}/.launchers/conmod-cm/cmlib/ ${WORKSPACE}/lib_etf-${ETF_VERSION}
[[ $? -ne 0 ]] && bail "unable to copy cmlib to etf workspace"

exit 0
