#!/bin/bash
# ***************************************************************************************
# *   Copyright (c) 2022 Continental Automotive Systems, Inc., all rights reserved
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: populate-doxy.sh
# *
# *   Description: Script responsible for generating readme file
# *
# ***************************************************************************************

source "${WORKSPACE}/.launchers/conmod-cm/sdk/sdk-common.inc"

main() {
  process_cli_parameters "$@"
  common_sdk_init
  
  header1 "Generate Readme file"

  local README_TEMPLATE="${WORKSPACE}/.launchers/conmod-cm/templates/delivery/readme.template.txt"
  local README_FILENAME="Readme.txt"
  local SDK_README="${SDK_WORKSPACE}/${README_FILENAME}"

  echo "> cp ${README_TEMPLATE} ${SDK_README}"
  cp ${README_TEMPLATE} ${SDK_README}
  echo "* SDK Version: ${BASELINE_VERSION}" >> ${SDK_README}
  pushd ${WORKSPACE}/sdk-dir
      find "." -maxdepth 3 | sed -e "s/[^-][^\/]*\// |/g" -e "s/|\([^ ]\)/|-\1/" >> ${SDK_README}
  popd
  echo " =================================================================================================*/" >> ${SDK_README}
}

main "$@"
