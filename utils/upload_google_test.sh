#!/bin/bash
# ******************************************************************************
# *   Copyright (c) 2022 Continental Automotive Systems, Inc., all rights reserved
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: upload_google_test.sh
# *
# *   Description: Upload google test results to Artifactory
# *
# ******************************************************************************

source "${WORKSPACE}/.launchers/conmod-cm/sdk/sdk-common.inc"
source "${WORKSPACE}/.launchers/conmod-cm/utils/artifactory.lib"

main() {

  process_cli_parameters "$@"
  common_sdk_init

  GOOGLE_SUMMARY_FILE="google_test.properties"

  header1 "Download Google Test results from Build"
  copy_from_build "${GOOGLE_SUMMARY_FILE}" "${WORKSPACE}/"

  header1 "Upload Google Test results to Artifactory"
  upload_artifacts "${WORKSPACE}" "${RELEASE_ID}" "${BASELINE_VERSION}" "${GOOGLE_SUMMARY_FILE}"

  return 0
}

main "$@"
