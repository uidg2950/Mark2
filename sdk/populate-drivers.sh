#!/bin/bash
# ***************************************************************************************
# *   Copyright (c) 2022 Continental Automotive Systems, Inc., all rights reserved
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: populate-drivers.sh
# *
# *   Description: Script responsible for populating of sdk folder
# *                Just empty Drivers folder. Backward compatibility
# *
# ***************************************************************************************

source "${WORKSPACE}/.launchers/conmod-cm/sdk/sdk-common.inc"

main() {
  process_cli_parameters "$@"
  common_sdk_init
  
  header1 "Populate Drivers"

  local DRIVERS_DIR="Drivers"
  local destination_folder="${SDK_WORKSPACE}/${DRIVERS_DIR}"

  if [[ ! -d ${destination_folder} ]]; then
      echo "Destination sdk dir not existed. Creating it"
      echo "> mkdir -p '${destination_folder}'"
      mkdir -p "${destination_folder}"
      if [[ $? -ne 0 ]]; then
         bail "Failed to create ${destination_folder} folder"
      fi
   fi
}

main "$@"
