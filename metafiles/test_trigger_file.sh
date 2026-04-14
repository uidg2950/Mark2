#!/bin/bash
# ******************************************************************************
# *   Copyright (c) 2023 Continental Automotive Systems, Inc., all rights reserved
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: test_trigger_file
# *
# *   Description: Generat Test File for Automatic Test.
# *
# *
# ******************************************************************************
SCRIPT_NAME=$(basename "${0}")
LOGFILE=$(dirname $0)/"${SCRIPT_NAME%.*}.log"
echo "LOGGING to ${LOGFILE}"
exec > >(tee "${LOGFILE}");

# All output from commands in this block sent to file $LOGFILE.
echo "START: ${SCRIPT_NAME} $(date)"

## Script Parameters
WORKSPACE=${1?workspaces is required}
RELEASE_ID=${2?release_id is required}
BASELINE_VERSION=${3?baseline_version is required}

echo "Import external libraries"
source "${WORKSPACE}/.launchers/conmod-cm/utils/platform-common.lib"

# Variables
AUTOTST_DRIVE="WETP00DA.cw01.contiwan.com"
AUTOTST_SHARED_DRIVE="//${AUTOTST_DRIVE}/y$/CT_PVV/11_Build_Mirror/CONMOD"
ARTIFACTORY_SERVER='https://us.artifactory.automotive.cloud/artifactory'
ARTIFACT_REPO='vni_otp_generic_l'
RET_CODE=0

#Handle exit codes to always promote variables
function on_exit {
    echo "Trapping on exit code: $?"
    echo "Workspace integrity verification"
    WTZ_MOUNTED=$(mount | grep ${AUTOTST_DRIVE})
    if [[ -n ${WTZ_MOUNTED} ]]; then
        sudo umount "${MOUNTING_DIR}"
        [[ ${RET_CODE} -ne 0 ]] && echo "Unable to unmount Sharedrive. Please verify the host machine"
    fi
    echo "Workspace is safe"
    echo "END: $(basename "$0") [${RET_CODE}]: $(date)"
}
trap on_exit EXIT

header1 "Execution Details"
echo
echo "                               DETAILS"
echo
echo "WORKSPACE:                   ${WORKSPACE}"
echo "RELEASE_ID:                  ${RELEASE_ID}"
echo "BASELINE_VERSION:            ${BASELINE_VERSION}"
echo

# Checking Wetzlar host is reachable
ping -c1 "${AUTOTST_DRIVE}" &> /dev/null
[[ $? -ne 0 ]] && bail "${AUTOTST_DRIVE} is not available"

# Mounting folder
header2 "Directory for mounting"
MOUNTING_DIR="${WORKSPACE}/autotst_drive"
echo "mkdir -p ${MOUNTING_DIR}"
mkdir -p ${MOUNTING_DIR}
RET_CODE=$((RET_CODE + $?))
[[ ${RET_CODE} -ne 0 ]] && bail "Mounting folder creation failed"

# Creating file for Testing
## Vars
FFTST="${WORKSPACE}/${BASELINE_VERSION}_tst_trigger.txt"
ARTIFACTORY_URL="${ARTIFACTORY_SERVER}/${ARTIFACT_REPO}/${RELEASE_ID}/${BASELINE_VERSION}"
## Print
header2 "File content"
echo "RELEASE_ID=${RELEASE_ID}" | tee "${FFTST}"
echo "BASELINE_VERSION=${BASELINE_VERSION}" | tee -a "${FFTST}"
echo "ARTIFACTORY_URL=${ARTIFACTORY_URL}" | tee -a "${FFTST}"

# FIXME: This is a temporary solution for save official conmod baselines
header2 "Mounting Test Shared Drive"
echo "sudo mount.cifs -o credentials=/home/uidg4627/.credentials/dpfil02,uid=uidg4627,gid=uidg4627 ${AUTOTST_SHARED_DRIVE} ${MOUNTING_DIR}"
sudo mount.cifs -o credentials=/home/uidg4627/.credentials/dpfil02,uid=uidg4627,gid=uidg4627 "${AUTOTST_SHARED_DRIVE}" "${MOUNTING_DIR}"
RET_CODE=$((RET_CODE + $?))
[[ ${RET_CODE} -ne 0 ]] && bail "Mounting ${AUTOTST_SHARED_DRIVE} drive failed"

# Copying file
header2 "Copying File"
echo "cp -v ${FFTST} ${MOUNTING_DIR}"
cp -v "${FFTST}" "${MOUNTING_DIR}"
RET_CODE=$((RET_CODE + $?))
[[ ${RET_CODE} -ne 0 ]] && bail "Copying file failed"

# Unmount Sharedrive
header2 "Unmount Test Shared Drive"
echo "sudo umount ${MOUNTING_DIR}"
sudo umount "${MOUNTING_DIR}"
RET_CODE=$((RET_CODE + $?))
[[ ${RET_CODE} -ne 0 ]] && bail "Unable to unmount Sharedrive, or script errors. Please verify the host machine"

echo "End of Script"
# ----------------------------------------------------------- #
