#!/bin/bash
# ***************************************************************************************
# *   Copyright (c) 2022 Continental Automotive Systems, Inc., all rights reserved
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: validate_archives.sh
# *
# *   Description: Script responsible for validation of tp_sdk_*_pkg.zip
# *
# ***************************************************************************************

source "${WORKSPACE}/.launchers/conmod-cm/sdk/sdk-common.inc"

main() {
  process_cli_parameters "$@"

  header1 "Install SDK"
  local INSTALL_PRODFS_SDK_FILE="${WORKSPACE}/.launchers/linux/sdk/install-prodfs-sdk"

  echo ". $INSTALL_PRODFS_SDK_FILE --workspace ${WORKSPACE} --image_size 4K"
  . $INSTALL_PRODFS_SDK_FILE --workspace "${WORKSPACE}" --image_size '4K'
  [[ $? -ne 0 ]] && bail "Image creation failed at install-prodfs-sdk"
  
}

main "$@"
echo "END of: $(basename $0)"
