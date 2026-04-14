#!/bin/bash
# ***************************************************************************************
# *   Copyright (c) 2022 Continental Automotive Systems, Inc., all rights reserved
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: generate-toolchain.sh
# *
# *   Description: Script responsible for generating toolchain.tar.gz
# *
# ***************************************************************************************

source "${WORKSPACE}/.launchers/conmod-cm/sdk/sdk-common.inc"
source "${WORKSPACE}/.launchers/conmod-cm/utils/archive-tools.lib"

main() {
  process_cli_parameters "$@"
  common_sdk_init
  
  header1 "Generate Toolchain"

  local LOCAL_TOOLCHAIN_DIR="${WORKSPACE}/toolchain"
  local final_filename="tp_toolchain_${BASELINE_VERSION}_pkg.zip"
  local src_otp_host="otp-host.tar.gz"
  local src_toolchain="toolchain.tar.gz"

  echo "mkdir ${LOCAL_TOOLCHAIN_DIR}"
  mkdir ${LOCAL_TOOLCHAIN_DIR}

  copy_from_build "sdk/${src_otp_host}" "${LOCAL_TOOLCHAIN_DIR}"
  copy_from_build "sdk/${src_toolchain}" "${LOCAL_TOOLCHAIN_DIR}"

  pushd "${LOCAL_TOOLCHAIN_DIR}" > /dev/null
    echo "zip -r ${final_filename} ./*"
    zip -r ${final_filename} ./*
  popd
}

main "$@"
