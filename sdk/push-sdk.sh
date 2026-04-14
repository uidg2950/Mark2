#!/bin/bash
# ***************************************************************************************
# *   Copyright (c) 2022 Continental Automotive Systems, Inc., all rights reserved
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: push-sdk.sh
# *
# *   Description: Script responsible for creating zip archive of sdk and push to dpk and artifactory
# *
# ***************************************************************************************

source "${WORKSPACE}/.launchers/conmod-cm/sdk/sdk-common.inc"
source "${WORKSPACE}/.launchers/conmod-cm/utils/archive-tools.lib"
source "${WORKSPACE}/.launchers/conmod-cm/utils/artifactory.lib"

main() {
  process_cli_parameters "$@"
  common_sdk_init

  local zip_filename="tp_sdk_${BASELINE_VERSION}_pkg.zip"
  header1 "Create sdk Zip"
  pushd "${WORKSPACE}/sdk-dir"  >/dev/null
    create_zip_archive "${SDK_BUNDLE_DIR}" "${zip_filename}"
  popd

  header1 "Push SDK zip to Artifactory"

  upload_artifacts "${WORKSPACE}/sdk-dir" "${RELEASE_ID}" "${BASELINE_VERSION}/sdk" "${zip_filename}"

  if [[ $? -ne 0 ]]; then
    bail "Failed to upload artifacts"
  else
    echo "SDK Uploaded sucesfully"
  fi

  return 0
}

main "$@"
