#!/bin/bash
# ***************************************************************************************
# *   Copyright (c) 2022 Continental Automotive Systems, Inc., all rights reserved
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: populate-sdk.sh
# *
# *   Description: Script responsible for populating of sdk folder
# *
# ***************************************************************************************

source "${WORKSPACE}/.launchers/conmod-cm/sdk/sdk-common.inc"
header2 "Update sdk sbl1 files"

move_sbl () {
  echo "Move SBL"
  local INPUT=${1?Inputdir or file is required}
  echo "Input: ${INPUT}"
  local SBL_PATH=${2-}
  echo "Sbl path: ${SBL_PATH}"

  if [[ -d ${INPUT} ]]; then
    echo "cp ${INPUT}/sbl1.mbn ${INPUT}/sbl1-qcom.mbn"
    cp "${INPUT}/sbl1.mbn" "${INPUT}/sbl1-qcom.mbn"
    [[ $? -ne 0 ]]  && bail "Failed to backup original sbl"

    echo "cp ${INPUT}/sbl1-audi-conmod.mbn ${INPUT}/sbl1.mbn"
    cp "${INPUT}/sbl1-audi-conmod.mbn" "${INPUT}/sbl1.mbn"
    [[ $? -ne 0 ]]  && bail "Failed to replace sbl1 with sbl1-audi-conmod"

  elif [[ -f ${INPUT} ]]; then
    echo "> mktemp -d ${WORKSPACE}/move_sbl.XXXXXXXXX"
    local SBL_WORKDIR=$(mktemp -d ${WORKSPACE}/move_sbl.XXXXXXXXX)

    pushd ${SBL_WORKDIR}
      echo "> tar --extract --ungzip --file ${INPUT} --directory ."
      tar --extract --ungzip --file "${INPUT}" --directory .
      [[ $? -ne 0 ]]  && bail "Unable to extract tar.archive to working folder"

      if [ -z ${SBL_PATH} ]; then
        echo "cp sbl1.mbn sbl1-qcom.mbn"
        cp "sbl1.mbn" "sbl1-qcom.mbn"
        [[ $? -ne 0 ]]  && bail "Failed to backup original sbl"

        echo "cp sbl1-audi-conmod.mbn sbl1.mbn"
        cp "sbl1-audi-conmod.mbn" "sbl1.mbn"
        [[ $? -ne 0 ]]  && bail "Failed to replace sbl1 with sbl1-audi-conmod"
      else
        echo "cp ${SBL_PATH}/sbl1.mbn ${SBL_PATH}/sbl1-qcom.mbn"
        cp "${SBL_PATH}/sbl1.mbn" "${SBL_PATH}/sbl1-qcom.mbn"
        [[ $? -ne 0 ]]  && bail "Failed to backup original sbl"

        echo "cp ${SBL_PATH}/sbl1-audi-conmod.mbn ${SBL_PATH}/sbl1.mbn"
        cp "${SBL_PATH}/sbl1-audi-conmod.mbn" "${SBL_PATH}/sbl1.mbn"
        [[ $? -ne 0 ]]  && bail "Failed to replace sbl1 with sbl1-audi-conmod"
      fi
      local TAR_FILES=$(ls -A)
      echo "tar --create --gzip --file ${INPUT} ${TAR_FILES}"
      tar --create --gzip --file "${INPUT}" ${TAR_FILES}
      [[ $? -ne 0 ]] && bail "Unable to updated ${INPUT}"
    popd

    rm -rf ${SBL_WORKDIR}
  else
    bail "${INPUT} not available"
  fi
}

main() {
  process_cli_parameters "$@"
  common_sdk_init
  
  header1 "Populate SDK"

  local SDK_DIR="sdk"
  local RELEASE_DIR="release/images/devel/4K"

  # Update sbl inside 4K
  move_sbl "${SDK_WORKSPACE}/${RELEASE_DIR}"
  
  local SOURCE_SDK_FILENAME="sdk_signed.tar.gz"
  local SDK_FILENAME="sdk.tar.gz"

  # Update sbl inside sdk.tar.gz
  copy_from_build "${SDK_DIR}/${SOURCE_SDK_FILENAME}" "${SDK_WORKSPACE}/${SDK_DIR}"
  move_sbl "${SDK_WORKSPACE}/${SDK_DIR}/${SOURCE_SDK_FILENAME}" "boot"

  echo "mv '${SDK_WORKSPACE}/${SDK_DIR}/${SOURCE_SDK_FILENAME}' '${SDK_WORKSPACE}/${SDK_DIR}/${SDK_FILENAME}'"
  mv "${SDK_WORKSPACE}/${SDK_DIR}/${SOURCE_SDK_FILENAME}" "${SDK_WORKSPACE}/${SDK_DIR}/${SDK_FILENAME}"

  local SOURCE_IMAGES_FILENAME="conti-signed-images.tar.gz"

  # Update sbl inside conti-signed-images.tar.gz
  copy_from_build "${SDK_DIR}/${SOURCE_IMAGES_FILENAME}" "${SDK_WORKSPACE}/${SDK_DIR}"
  move_sbl "${SDK_WORKSPACE}/${SDK_DIR}/${SOURCE_IMAGES_FILENAME}"
}

main "$@"
