#!/bin/bash
# ***************************************************************************************
# *   Copyright (c) 2022 Continental Automotive Systems, Inc., all rights reserved
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: populate-doxy.sh
# *
# *   Description: Script responsible for populating of sdk Doxygen folder
# *
# ***************************************************************************************

source "${WORKSPACE}/.launchers/conmod-cm/sdk/sdk-common.inc"

main() {
  process_cli_parameters "$@"
  common_sdk_init
  
  header1 "Populate Doxygen folder"

  local DOXY_DIR="Doxygen"
  local DOXY_FILENAME="${BASELINE_VERSION}_doxygen.tar.gz"

  copy_from_documents "${DOXY_FILENAME}" "${SDK_WORKSPACE}/${DOXY_DIR}/"
}

main "$@"
