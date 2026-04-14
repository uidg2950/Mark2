#!/bin/bash
# ******************************************************************************
# *   Copyright (c) 2024 Continental Automotive Systems, Inc., all rights reserved
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: get_all_swl_bundles.sh
# *
# *   Description: return list of all swl bundles for RELEASE_ID
# *                as the list is returned by the last 'echo' no other test output is allowed!!!
# *
# ******************************************************************************

WORKSPACE=${1?workspace is required}
RELEASE_ID=${2?release_id is required}

source "${WORKSPACE}/.launchers/conmod-cm/utils/platform-common.lib"
source "${WORKSPACE}/.launchers/conmod-cm/utils/artifactory.lib"

SWL_DOWNLOAD_BUNDLES=$(get_subfolder_list ${RELEASE_ID} "swl/test/")
[[ $? -ne 0 ]] && bail "Error getting SWL_DOWNLOAD_BUNDLES for 'all'!"

echo "${SWL_DOWNLOAD_BUNDLES[@]}"

