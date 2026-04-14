#!/bin/bash
# ***************************************************************************************
# *   Copyright (c) 2022-2024 Continental Automotive Systems, Inc., all rights reserved
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: sdk-common.inc
# *
# *   Description: library file of common function of sdk-creation
# *
# *
# ***************************************************************************************

source "${WORKSPACE}/.launchers/conmod-cm/utils/platform-common.lib"

cleanup() {
  header1 "Cleanup"
  echo "> rm -rf ${WORKSPACE}"
  rm -rf ${WORKSPACE}
}

help_info() {
    cat << HELP
./$(basename "$0") --workspace /path/to/workspace --baseline conmod-sa515m-3.2.27.0 [--release_id conmod-sa515m-3.y]
Script for population of sdk.

Options:
    -h|--help                   Display this information.
    -w|--workspace              Workspace directory.
    -b|--baseline               Baseline version.
    -r|--release_id             Release id.
    -f|--flavor                 Build flavor (prod/devel)
HELP
}

process_extra_cli_parameter() {
    local param="$1"
    local value="$2"
    echo -e "Invalid parameter: '$param'.\nUse -h|--help for more information."
    exit 1
}

process_cli_parameters() {
    # Verify the shell is set to bash
    if [[ ! $(readlink "$(which sh)") =~ bash ]]; then
      echo ""
      echo "### ERROR: Please Change your /bin/sh symlink to point to bash. ### "
      echo "### sudo ln -sf /bin/bash /bin/sh ### "
      echo ""
      exit 1
    fi

    if [[ $# -eq 0 ]]; then
        help_info
        exit 1
    fi

    RELEASE_ID="conmod-sa515m-3.y"

    while [[ $# -gt 0 ]]; do
        param="$1"
        shift
        case $param in
            -h|--help)
                help_info
                exit 0
                ;;
            -w|--workspace)
                WORKSPACE="$1"
                shift
                ;;
            -b|--baseline)
                BASELINE_VERSION="$1"
                shift
                ;;
            -r|--release_id)
                RELEASE_ID="$1"
                shift
                ;;
            -d|--delivery_type)
                DELIVERY_TYPE="$1"
                shift
                ;;
            -f|--flavor)
                FLAVOR="$1"
                shift
                ;;
            *)
                process_extra_cli_parameter "$param" "$1"
                ;;
        esac
    done
}

common_sdk_init() {
    echo "Import external libraries"
    if [[ ! -z ${WORKSPACE} ]]; then
        source "${WORKSPACE}/.launchers/conmod-cm/utils/platform-common.lib"
    else
        echo "Mandatory argument 'Workspace' is not provided."
        help_info
        exit 1
    fi

    if [[ -z ${FLAVOR} ]] && [ -f "${WORKSPACE}/.build/env-common" ]; then
        FLAVOR=$(cat "${WORKSPACE}/.build/env-common" | sed -n "s/^export CAS_BUILD_FLAVOR=\(.*\)$/\1/p")
    else
        # default
        FLAVOR='devel'
    fi
    PROD_STR=''
    [[ "${FLAVOR}" == "prod" ]] && PROD_STR='P=1'
    [[ "${FLAVOR}" == "devel" ]] && PROD_STR='P=0'

    if [[ ! -z ${BASELINE_VERSION} ]]; then
        SDK_PACKAGES_PATH="/u01/app/jenkins/documents/sdk_packages/${BASELINE_VERSION}"
        SDK_BUNDLE_DIR="tp_sdk_${RELEASE_ID}_pkg/"
        SDK_WORKSPACE="${WORKSPACE}/sdk-dir/${SDK_BUNDLE_DIR}/"

        DAILY_BUILD_DIR="/u01/app/jenkins/releases/${RELEASE_ID}/${BASELINE_VERSION}-devel/"
        DAILY_DOCS_DIR="/u01/app/jenkins/documents/${RELEASE_ID}/${BASELINE_VERSION}/"
    else
        echo "Mandatory argument 'Baseline' is not provided."
        help_info
        exit 1
    fi

    [[ ! -d ${DAILY_BUILD_DIR} ]] && bail "Daily build folder not found. Make sure 3Y-BUILD job finished successfully."
    [[ ! -d ${DAILY_DOCS_DIR} ]] && bail "Daily documents folder not found. Make sure 3Y-BUILD job finished successfully."

    if [[ ! -d ${SDK_WORKSPACE} ]]; then
       echo "SDK_BUNDLE DIR NOT EXISTED. Creating it".
       echo "> mkdir -p ${SDK_WORKSPACE}"
       mkdir -p ${SDK_WORKSPACE}

       [[ $? -ne 0 ]]  && bail "Failed to create ${SDK_WORKSPACE}"
    fi
}

general_sdk_copy() {
    local source="${1?source is required}"
    local destination="${2?destination is required}"
    local source_prefix="${3?prefix is required}"
    local destination_prefix="${4?destination prefix is required}"

    local source="${source_prefix}/${source}"
    local destination="${destination_prefix}/${destination}"

    [[ ! -e ${source} ]] && bail "Source file [${source}] not found. "

    if [[ ! -d ${destination} ]]; then
      echo "Destination folder not existed. Creating it"
      echo "> mkdir -p '${destination}'"
      mkdir -p "${destination}"
      [[ $? -ne 0 ]]  && bail "Failed to create ${destination} folder"
    fi

    echo "> rsync  --archive --verbose --human-readable --checksum --no-o --no-g '${source}' '${destination}'"
    rsync  --archive --verbose --human-readable --checksum --no-o --no-g "${source}" "${destination}"
    [[ $? -ne 0 ]]  && bail "Failed to copy file ${source} to ${destination}"

    return 0
}

copy_to_sdk() {
    general_sdk_copy "$1" "$2" "" "${SDK_WORKSPACE}"
}

copy_to_dpk() {
    general_sdk_copy "$1" "$2" "" "${SDK_PACKAGES_PATH}"
}

copy_from_build() {
    general_sdk_copy "$1" "$2" "${DAILY_BUILD_DIR}" ""
}

copy_from_documents() {
    general_sdk_copy "$1" "$2" "${DAILY_DOCS_DIR}" ""
}

