#!/bin/bash
# ***************************************************************************************
# *   Copyright (c) 2022 - 2024 Continental Automotive Systems, Inc., all rights reserved
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: populate-documents.sh
# *
# *   Description: Script responsible for populating of documents folder
# *
# ***************************************************************************************

source "${WORKSPACE}/.launchers/conmod-cm/sdk/sdk-common.inc"

main() {
  process_cli_parameters "$@"
  common_sdk_init

  header1 "Populate Documents"

  local DOCUMENTS_DIR="Documents"
  local destination_folder="${SDK_WORKSPACE}/${DOCUMENTS_DIR}"

  local path_to_documents="${WORKSPACE}/.launchers/conmod-cm/sdk/Documents"

  copy_to_sdk "${path_to_documents}/" "${DOCUMENTS_DIR}"

# Workaround due multiple documents versions ( depending on the dev line )
  echo "Replacing specific documents versions (if needed)"
  if [[ "${RELEASE_ID}" =~ conmod-sa515m-cl43 ]]; then
      cp -v "${path_to_documents}/../Documents_cl43/"* "${SDK_WORKSPACE}/${DOCUMENTS_DIR}"
      echo "Documents updated for ${RELEASE_ID} line"
  elif [[ "${RELEASE_ID}" =~ conmod-sa515m-cl46 ]]; then
      cp -v "${path_to_documents}/../Documents_cl46/"* "${SDK_WORKSPACE}/${DOCUMENTS_DIR}"
      echo "Documents updated for ${RELEASE_ID} line"
  fi

  local document_versions="${destination_folder}/document_versions.csv"

  [[ ! -e "${document_versions}" ]] || rm "${document_versions}"

}

main "$@"
