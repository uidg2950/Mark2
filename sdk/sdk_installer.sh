#!/bin/bash
# ******************************************************************************
# *   Copyright (c) 2019 Continental Automotive Systems, Inc., all rights reserved
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: sdk_installer
# *
# *   Description:
# *              1) Unpacking sdk-constructor
# *              2) Installing Artifacts
# *
# ******************************************************************************

# Workarea Path
WORKSPACE=$(dirname $(readlink -f $(basename $0)))
echo "###### Installing SDK in ${WORKSPACE}"

# Artifacts
SDK_CONSTRUCTOR="sdk-constructor.tar.gz"
SDK_SUITE_ARTIFACTS=("sdk.tar.gz" "otp-host.tar.gz" "toolchain.tar.gz")
SDK_ARTIFACTS_PATHS=( "${WORKSPACE}/release/fs/devel" "${WORKSPACE}/release-host/fs/host" "${WORKSPACE}/release-toolchain/fs/devel" )
ENV_FILES=( "env-common" "env-target" "env-buildsys-static" )
RET_CODE=0

# 1) Unpacking sdk-constructor
echo "##### Unpacking ${SDK_CONSTRUCTOR}"
echo "tar -zxf ${WORKSPACE}/${SDK_CONSTRUCTOR} -C ${WORKSPACE}"
tar -zxf "${WORKSPACE}/${SDK_CONSTRUCTOR}" -C "${WORKSPACE}"
RET_CODE=$((RET_CODE + $?))
[ ${RET_CODE} -ne 0 ] && echo "Unable to unpacking ${SDK_CONSTRUCTOR}" && exit 1

# 2) Installing Artifacts
echo "##### Unpacking artifacts"
SSACOUNT=${#SDK_SUITE_ARTIFACTS[@]}
for (( c=0;c<$SSACOUNT;c++ )); do
    [ ! -d ${SDK_ARTIFACTS_PATHS[${c}]} ] && echo "Unable to locate ${SDK_ARTIFACTS_PATHS[${c}]}" && exit 1
    echo "tar -zxf "${WORKSPACE}/${SDK_SUITE_ARTIFACTS[${c}]}" -C ${SDK_ARTIFACTS_PATHS[${c}]}"
    tar -zxf "${WORKSPACE}/${SDK_SUITE_ARTIFACTS[${c}]}" -C ${SDK_ARTIFACTS_PATHS[${c}]}
    RET_CODE=$((RET_CODE + $?))
    [ ${RET_CODE} -ne 0 ] && echo "Unable to unpacking ${SDK_SUITE_ARTIFACTS[${c}]}" && exit 1
done

echo "The SDK Suite Environment was successfully installed"
#echo "END: $(basename $0) [${RET_CODE}]: $(date)"
# ----------------------------------------------------------- #

