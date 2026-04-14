#!/bin/bash
# ***************************************************************************************
# *   Copyright (c) 2022 Continental Automotive Systems, Inc., all rights reserved
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: populate-release.sh
# *
# *   Description: Script responsible for populating of release folder
# *
# ***************************************************************************************

source "${WORKSPACE}/.launchers/conmod-cm/sdk/sdk-common.inc"
source "${WORKSPACE}/.launchers/conmod-cm/utils/artifactory.lib"

main() {
  process_cli_parameters "$@"
  common_sdk_init
  
  header1 "Populate Images folder"

  local RELEASE_SUB_FOLDER="release"
  local IMAGE_DIR="images"
  local DOCS_DIR="docs"
  local METRICS_DIR="metrics"
  local tz_images="tz_images.tar.gz"
  local qshrink="modem_qshrink.tar.gz"

  copy_from_build "${RELEASE_SUB_FOLDER}/${IMAGE_DIR}" "${SDK_WORKSPACE}/${RELEASE_SUB_FOLDER}"
  copy_from_build "${RELEASE_SUB_FOLDER}/${DOCS_DIR}" "${SDK_WORKSPACE}/${RELEASE_SUB_FOLDER}"
  copy_from_build "${RELEASE_SUB_FOLDER}/${METRICS_DIR}" "${SDK_WORKSPACE}/${RELEASE_SUB_FOLDER}"
  copy_from_build "otp_versions.txt" "${SDK_WORKSPACE}/${RELEASE_SUB_FOLDER}/${DOCS_DIR}/"
  copy_from_build "xqcn_mcfg_versions.txt" "${SDK_WORKSPACE}/${RELEASE_SUB_FOLDER}/${DOCS_DIR}/"
  copy_from_build "${RELEASE_SUB_FOLDER}/${IMAGE_DIR}/devel/4K/SA515_HW_to_QCN_table.txt" "${SDK_WORKSPACE}/${RELEASE_SUB_FOLDER}/${DOCS_DIR}/"
  upload_artifacts "${SDK_WORKSPACE}/${RELEASE_SUB_FOLDER}/${DOCS_DIR}" "${RELEASE_ID}" "${BASELINE_VERSION}" "otp_versions.txt"
  download_artifacts "${SDK_WORKSPACE}/${RELEASE_SUB_FOLDER}" ${RELEASE_ID} "${BASELINE_VERSION}" ${qshrink}
  download_artifacts "${SDK_WORKSPACE}/${RELEASE_SUB_FOLDER}" ${RELEASE_ID} "${BASELINE_VERSION}" ${tz_images}
}

main "$@"
