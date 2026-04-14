#!/bin/bash
# ***************************************************************************************
# *   Copyright (c) 2024 Continental Automotive Systems, Inc., all rights reserved
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: artifacts-common.inc
# *
# *   Description: library file of common function of artifacts-creation
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
./$(basename "$0") --workspace /path/to/workspace [ --output-dir /output/dir/path ] [--cas-arch arm64] [--linux-path /relative/path/to/linux]
Script for manual testing of esim.

Options:
    -h|--help                   Display this information.
    -w|--workspace              Workspace directory.
    -o|--output-dir             Artifact output directory.
    -c|--cas-arch               Target CAS-ARCH. By default arm64
    -l|--linux-path             Relative linux path. By default /package/opensource/linux
    -i|--release_id             Release-id as used in calling pipeline
    -b|--baseline_name          Baseline name as used in calling pipeline

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

    if [ $# -eq 0 ]; then
        help_info
        exit 1
    fi

    while [ $# -gt 0 ]; do
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
            -o|--output-dir)			# This needs to be generated
                OUTPUT_DIR="$1"
                shift
                ;;
            -c|--cas-arch)
                CAS_ARCH="$1"
                shift
                ;;
            -l|--linux-path)			# package/opensource/linux
                LINUX_PATH="$1"
                shift
                ;;
            -i|--release_id)            # Release-id as used in calling pipeline
                RELEASE_ID="$1"
                shift
                ;;
            -b|--baseline_name)          # Baseline name as used in calling pipeline
                BASELINE_NAME="$1"
                shift
                ;;
            *)
                process_extra_cli_parameter "$param" "$1"
                ;;
        esac
    done
}

check_parameters() {
    LINUX_DIR="${WORKSPACE}/${LINUX_PATH}"
    DTS_DIR="${LINUX_DIR}/arch/${CAS_ARCH}/boot/dts/qcom/"
    CONFIG_PATH="${LINUX_DIR}/.config"

    # default output directory is WORKSPACE
    if [ -z "${OUTPUT_DIR}" ]; then
        OUTPUT_DIR="${WORKSPACE}"
    else
        if [ ! -d "${WORKSPACE}/${OUTPUT_DIR}" ]; then
            echo "Creating output folder: ${OUTPUT_DIR}"
            mkdir -p "${OUTPUT_DIR}"
            OUTPUT_DIR="${WORKSPACE}/${OUTPUT_DIR}"
        fi
    fi

    if [ ! -d "${LINUX_DIR}" ]; then
        # Take action if $DIR exists. #
        bail "${LINUX_DIR} not found"
    fi

    if [ ! -f "${CONFIG_PATH}" ]; then
        bail "${CONFIG_PATH} not found inside ${LINUX_DIR}"
    fi

    if [ -z "${RELEASE_ID}" ]; then
        # Take action if $DIR exists. #
        bail "--release_id RELEASE_ID is needed!"
    fi

    if [ -z "${BASELINE_NAME}" ]; then
        bail "--baseline_name BASELINE_NAME is needed!"
    fi

    if [ ! -d "${DTS_DIR}" ]; then
        bail "DTS directory ${DTS_DIR} not found. Make sure linux is compiled and CAS_ARCH is correct."
    fi
}

copy_from_sdk() {
    local RELEASE_ID="${1?Release ID required}"
    SDK_PACKAGES_PATH="/u01/app/jenkins/documents/sdk_packages/${BASELINE_VERSION}"
    SDK_BUNDLE_DIR="${SDK_PACKAGES_PATH}/tp_sdk_${RELEASE_ID}_pkg/"
    local source="${SDK_BUNDLE_DIR}/${2?Source file is required}"
    [[ ! -e ${source} ]] && bail "Source file in sdk packages not found. [${source}]"
    echo "> rsync  --archive --verbose --human-readable --checksum --no-o --no-g '${source}' '${WORKSPACE}/'"
    rsync  --archive --verbose --human-readable --checksum --no-o --no-g "${source}" "${WORKSPACE}/"
    [[ $? -ne 0 ]]  && bail "Failed to copy file ${source} to ${destination}"
}