#!/bin/bash
# *****************************************************************************
# *
# *  (c) 2020-2024 Continental Automotive Systems, Inc., all rights reserved
# *
# *  All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *  Any reproduction of this material without written consent from
# *  Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *  Filename: reproducibility_build.sh
# *
# *  Description:
# *
# *
# *****************************************************************************
SCRIPT_NAME=$(basename "${BASH_SOURCE[0]}")
LOGFILE=$(dirname "${BASH_SOURCE[0]}")/"${SCRIPT_NAME%.*}.log"
echo "LOGGING to ${LOGFILE}"
exec > >(tee "${LOGFILE}");

# ----------------------------------------------------------- #
# All output from commands in this block sent to file $LOGFILE.
echo "START: ${SCRIPT_NAME} $(date)"

# COMMAND LINE PARAMETERS
export WORKSPACE=${1}
export PROJECT=${2}
export BASE_VERSION=${3}
export BASELINE_VERSION=${4}
export CAS_TARGET_HW=${5}
export FLAVOR=${6}
export BUILD_CLOBBER=${7}
export RELEASE_ID=${8}


echo "Import external libraries"
source "${WORKSPACE}/.launchers/linux/base.lib"
source "${WORKSPACE}/.launchers/linux/common.lib"

if [ "$#" -lt 6 ] || [ "$#" -gt 9 ]; then
    bail "Illegal number of parameters: $#"
fi

## SCRIPT VARIABLES
JOB_NAME=$(basename "${WORKSPACE}" | cut -d@ -f1)
# MANIFEST SOURCES
# These are the default locations used by the 3.y lines, however previous release lines used a
# different location that can only be checked after the first repo sync is executed for them.
HAL_MANIFEST_DIR="${WORKSPACE}/manifests/platform-hal"
FRAMEWORK_MANIFEST_DIR="${WORKSPACE}/manifests/platform-framework"
# This only applies for PD like builds
PLATFORM_MANIFEST_DIR="${WORKSPACE}/manifests/platform"
# Default location for repo tools
MANIFESTS_DIR="${WORKSPACE}/.repo/manifests"
# PACKAGE SOURCES
PROJECT_DIR="${WORKSPACE}/project"
RELEASE_DIR="${WORKSPACE}/release"
RELEASE_HOST_DIR="${WORKSPACE}/release-host"
RELEASE_TOOLCHAIN_DIR="${WORKSPACE}/release-toolchain"
# SUB-MANIFESTS
MODULES=('FRAMEWORK' 'HAL')
# Control Flow
FIRST_SYNC=''
[[ ${BUILD_CLOBBER} == "true" ]] && CLEANER='M=1 clobber' || CLEANER='clean'

# Output consumed by pipelines
TARGET_HW_VARIANTS=()  # Holds all the variants available so they can be consumed by the pipe
PROPERTIES_FILE="${WORKSPACE}/${JOB_NAME}.properties"

# Repo configuration
REPO_BRANCH="stable-conti"
REPO_URL="buic-scm:IIC_SW_Tools/git-repo"

# Default values
fw_hal_target_hw_pattern=$(get_fw_hal_target_hw_pattern)

# set P=x make parameter
PROD_STR=$(check_and_get_prod_str ${FLAVOR})

# Handle exit codes to always promote variables
function on_exit {
    echo "Trapping on exit code: $?"

    header2 "PROMOTE ENV VARIABLES"
    echo "Promoting to: ${PROPERTIES_FILE}"
    echo "BASELINE_VERSION=${BASELINE_VERSION}"     | tee -a "${PROPERTIES_FILE}"
    echo "BUILD_FILES_URL=${WORKSPACE}"             | tee -a "${PROPERTIES_FILE}"
    echo "CAS_TARGET_HW=${CAS_TARGET_HW}"           | tee -a "${PROPERTIES_FILE}"
    echo "END: ${SCRIPT_NAME} [${RET_CODE}]: $(date)"
}

trap on_exit EXIT

# Overall return status
RET_CODE=0

# BUILD VARIABLES

EFS_SHARED_DRIVE=$(get_efs_shared_drive "${CAS_TARGET_HW}" "${WORKSPACE}")

# Calculated values
VARIANT=$(get_variant "${BASE_VERSION}" "${CAS_TARGET_HW}")                 # Variant changes the behavior on modem and fetch along with FW and HAL
# image size - 2K images by default
case "${RELEASE_ID}" in
    *sa515m*)
        IMG_SZ="-4K"
        ;;
    *)
        IMG_SZ="-all"
        ;;
esac

echo "##################################################################"
echo "                               DETAILS"
echo
echo "Build description: "
echo
echo "WORKSPACE:            ${WORKSPACE}"
echo "PROJECT:              ${PROJECT}"
echo "BASE_VERSION:         ${BASE_VERSION}"
echo "BASELINE_VERSION:     ${BASELINE_VERSION}"
echo "CAS_TARGET_HW:        ${CAS_TARGET_HW}"
echo "BUILD_CLOBBER:        ${CLEANER}"
echo "RELEASE_ID:           ${RELEASE_ID}"
echo
echo "EFS_SHARED_DRIVE:     ${EFS_SHARED_DRIVE}"
echo "RELEASE_DIR:          ${RELEASE_DIR}"
echo
echo "VARIANT:              ${VARIANT}"
echo "bld_version_number:   ${bld_version_number}"
echo
echo "FLAVOR:               ${FLAVOR}"
echo "PROD_STR:             ${PROD_STR}"
echo


header1 "BUILD AREA"
pushd "${WORKSPACE}" >/dev/null

# Base Dev Branch or Refactoring Branch
# MANIFEST_BRANCH=$(get_manifest_branch ${PROJECT} ${BASE_VERSION} ${CAS_TARGET_HW} ${REFACTORING})
# This is the RELEASE_ID

if [ -n "${WORKSPACE}" ]; then
    # Force bootstrap
    ERASE=('logs' '*.properties' 'sdk' 'UPC' '*.tar.gz' '*.tar' '*.txt' '.build' 'platform-framework' 'platform-hal' '.repo/local_manifests/' 'release-host')


    if [ "${BUILD_CLOBBER}" == "true" ]; then
        ERASE+=('*')    # Delete all contents but hidden ones
    fi

    echo "Deleting previous contents"
    for FILE in "${ERASE[@]}"; do
        echo "rm -rf ${WORKSPACE}/${FILE}"
        rm -rf ${WORKSPACE}/${FILE}

        #Verify artifacts got removed
        ls ${WORKSPACE}/${FILE} 2>/dev/null
    done
fi

# If .repo is present this is not the first time we initialize the project
[[ -d "${MANIFESTS_DIR}" ]] || FIRST_SYNC="x"

header1 "New Repository for ${BASELINE_VERSION} will be created"
repo_init "${PROJECT}" "${BASELINE_VERSION}" all "${REPO_BRANCH}" "${REPO_URL}"

header2 "GET PREVIOUS_BASELINE"
MANIFEST_REMOTE=$(git --git-dir="${MANIFESTS_DIR}/.git" config --get remote.origin.url)
RELEASE_REMOTE=$(git --git-dir="${MANIFESTS_DIR}/.git" config --get remote.origin.url | sed 's/manifest/release/')
RELEASE_REMOTE="${RELEASE_REMOTE}-${CAS_TARGET_HW}"
if [ -z "${PREVIOUS_BASELINE}" ] ||  [ "${PREVIOUS_BASELINE}" == "-" ]; then
    echo "get_latest_remote_baseline ${CAS_TARGET_HW} ${PROJECT} ${BASE_VERSION} ${RELEASE_REMOTE}"
    PREVIOUS_BASELINE=$(get_latest_remote_baseline ${CAS_TARGET_HW} ${PROJECT} ${BASE_VERSION} ${RELEASE_REMOTE})
fi
echo "PREVIOUS_BASELINE=${PREVIOUS_BASELINE}"
[ "${PREVIOUS_BASELINE}" == "${BASELINE_VERSION}" ] && echo "${BASELINE_VERSION} is the latest baseline available"

header2 "REPO SYNC"
echo "> repo_sync hard full"
repo_sync hard full
RET_CODE=$((RET_CODE + $?))
[[ ${RET_CODE} -ne 0 ]] && bail "unable to commit results due to sync errors"

if [[ "${BUILD_RPM}" == "true" ]]; then
    header2 "ENABLING RPM"
    enable_rpm "${WORKSPACE}"
elif [[ "${BUILD_RPM}" == "false" ]]; then
    header2 "DISABLING RPM"
    disable_rpm "${WORKSPACE}"
else
    echo "Nothing to do with ARM licenses"
fi

header2 "CLEAN/CLOBBER WORK AREA"
echo "> make ${CLEANER} ${PROD_STR} CAS_TARGET_HW=${CAS_TARGET_HW}"
make ${CLEANER} ${PROD_STR} CAS_TARGET_HW="${CAS_TARGET_HW}"
RET_CODE=$((RET_CODE + $?))
[[ ${RET_CODE} -ne 0 ]] && bail "unable to continue due errors on make clobber"

header2 "GENERATE CHANGE-LOG FILES"
generate_change_log "${WORKSPACE}" "${PREVIOUS_BASELINE}" "${MANIFEST_BRANCH}"

header2 "MAKE pull and compile latest"
echo "make ${PROD_STR} CAS_TARGET_HW=${CAS_TARGET_HW}"
make ${PROD_STR} CAS_TARGET_HW=${CAS_TARGET_HW}
RET_CODE=$((RET_CODE + $?))

header2 "MAKE image${IMG_SZ}"
echo "make image${IMG_SZ} ${PROD_STR}"
make "image${IMG_SZ}" ${PROD_STR}
RET_CODE=$((RET_CODE + $?))
[ ${RET_CODE} -ne 0 ] && bail " Unable to continue due 'make image' failures"

# NOTE: This section affects the release area contents
header2 "COPYING xQCN FILES TO THE RELEASE AREA"
if [ -d "${EFS_SHARED_DRIVE}" ]; then
    echo "copy_xqcn_files ${RELEASE_DIR} ${EFS_SHARED_DRIVE} ${CAS_TARGET_HW}"
    copy_xqcn_files "${RELEASE_DIR}" "${EFS_SHARED_DRIVE}" "${CAS_TARGET_HW}"
else
    echo "No '${EFS_SHARED_DRIVE}' directory is available"
fi

popd >/dev/null
echo "END: ${SCRIPT_NAME} [${RET_CODE}]: $(date)"
# ----------------------------------------------------------- #
