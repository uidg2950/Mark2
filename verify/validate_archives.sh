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
source "${WORKSPACE}/.launchers/conmod-cm/utils/archive-tools.lib"
source "${WORKSPACE}/.launchers/conmod-cm/utils/artifactory.lib"

main() {
  process_cli_parameters "$@"
  common_sdk_init

  header1 "Validate tp_sdk_${BASELINE_VERSION}_pkg.zip"

  local PKG="tp_sdk_${RELEASE_ID}_pkg"
  local PKG_ZIP="tp_sdk_${BASELINE_VERSION}_pkg.zip"
  local sdk_dir="sdk"
  local sdk_constructor="sdk-constructor.tar.gz"
  local sdk="sdk.tar.gz"
  local otp_host="otp-host.tar.gz"
  local toolchain="toolchain.tar.gz"

  pushd "${WORKSPACE}" > /dev/null
    if [[ "${DELIVERY_TYPE}" != "Engineering Drop" ]];
    then
      get_metainfo ${RELEASE_ID} "${BASELINE_VERSION}/otc" ${PKG_ZIP}
      local artifactory_checksum=$(echo "${artifactory_metadata}" | python3 -c "import sys, json; print(json.load(sys.stdin)['checksums']['sha256'])")
      download_artifacts ${WORKSPACE} ${RELEASE_ID} "${BASELINE_VERSION}/otc" ${PKG_ZIP}
    else
      get_metainfo ${RELEASE_ID} "${BASELINE_VERSION}/sdk" ${PKG_ZIP}
      local artifactory_checksum=$(echo "${artifactory_metadata}" | python3 -c "import sys, json; print(json.load(sys.stdin)['checksums']['sha256'])")
      download_artifacts ${WORKSPACE} ${RELEASE_ID} "${BASELINE_VERSION}/sdk" ${PKG_ZIP}
    fi
    local local_checksum=($(sha256sum ${WORKSPACE}/${PKG_ZIP}))

    if [[ "${artifactory_checksum}" == "${local_checksum}" ]];
    then
      echo "Download of ${PKG_ZIP} successful!"
      unzip -j "${WORKSPACE}/${PKG_ZIP}" "${PKG}/${sdk_dir}/${sdk_constructor}" -d "${WORKSPACE}"
      unzip -j "${WORKSPACE}/${PKG_ZIP}" "${PKG}/${sdk_dir}/${sdk}" -d "${WORKSPACE}"
      copy_from_build "${sdk_dir}/${otp_host}" "${WORKSPACE}"
      copy_from_build "${sdk_dir}/${toolchain}" "${WORKSPACE}"
    else
      bail "Failed to download ${PKG_ZIP}! Checksum is not equal!"
    fi

    # Searching Files
    header2 "Looking for files"
    regex_to_search=( "CONMOD_5_G_" "Aumovio_ConMod_NAD_Test_Results_Rel" "Modem_BSW_delivery_manifest_SWC.json" "SWC_Release_Notes_" )

    get_metainfo ${RELEASE_ID} ${BASELINE_VERSION} ""
    folder_content=$(echo "${artifactory_metadata}" | python3 -c "import sys, json; print(json.load(sys.stdin)['children'])")

    # removing []{}''
    # replacing "," -> ":"
    folder_content=$(echo "${folder_content}" | sed "s/[]{''}[]//g" | sed 's/,/:/g')

    # Split by ":"
    IFS=':' read -ra FILE_LIST <<< ${folder_content}

    # if u want to create  an array with the names for example
    FILES=()
    for item in "${FILE_LIST[@]}"; do
        if [[ ${item} =~ \/ ]]; then              # strings that starts with “/”
            FILES+=("${item///}")
        fi
    done

    for doc_regex in "${regex_to_search[@]}"; do
      for file in "${FILES[@]}"; do
        if [[ "${file}" =~ "$doc_regex" ]]; then
          download_artifacts ${WORKSPACE} ${RELEASE_ID} ${BASELINE_VERSION} ${file}
          [[ $? -ne 0 ]] && echo "WARNING: Downloading ${file} failed"
        fi
      done
    done

  popd

}

main "$@"
