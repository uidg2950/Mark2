#!/bin/bash
# ******************************************************************************
# *   Copyright (c) 2023-2025 Aumovio, Inc., all rights reserved
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: baseline-staging
# *
# *   Description: Secure copy of conmod baselines into wetzlar shared drive
# *
# *
# ******************************************************************************
SCRIPT_NAME=$(basename "${0}")
LOGFILE=$(dirname $0)/"${SCRIPT_NAME%.*}.log"
echo "LOGGING to ${LOGFILE}"
exec > >(tee "${LOGFILE}");

# ----------------------------------------------------------- #
# All output from commands in this block sent to file $LOGFILE.
echo "START: ${SCRIPT_NAME} $(date)"

# Script Parameters
WORKSPACE=${1?workspace is required}
BASELINE_NAME=${2?baseline_name is required}
DELIVERY_TYPE=${3?delivery_type is required}

# Script variables
SHARED_DRIVE_DOCS="/u01/app/jenkins/documents"
STAGING_DOC_DIR="${SHARED_DRIVE_DOCS}/sdk_packages/${BASELINE_NAME}"
RGB_SHARED_DRIVE="//automotive-wan.com/root/smt/did01665/ConMod/18_Software_builds_AudiConMod"
MOUNTING_DIR="${WORKSPACE}/conmod_shared_drive"
RELEASE_STAGING_DIR="${MOUNTING_DIR}/release/${BASELINE_NAME}"
RET_CODE=0

echo "Import external libraries"
source "${WORKSPACE}/.launchers/linux/common.lib"

header1 "Storing Official Baseline"
echo
echo "                               DETAILS"
echo
echo "WORKSPACE:            ${WORKSPACE}"
echo "BASELINE_NAME:        ${BASELINE_NAME}"
echo "DELIVERY_TYPE:        ${DELIVERY_TYPE}"
echo

# Checking shared drive availability
df "${SHARED_DRIVE_DOCS}" 1> /dev/null 2>&1
[[ $? -ne 0 ]] && bail "${SHARED_DRIVE_DOCS} is not available"

# Creating folder for mount wetzlar shared drive
header2 "Creating folder for mount wetzlar shared drive"
echo "mkdir -p ${MOUNTING_DIR}"
mkdir -p ${MOUNTING_DIR}
RET_CODE=$((RET_CODE + $?))
[[ ${RET_CODE} -ne 0 ]] && bail "Mounting folder creation failed"

header2 "Mounting wetzlar shared drive"
# FIXME: This is a temporary solution for save official conmod baselines
echo "mount.cifs -o credentials=/home/uidg4627/.credentials/dpfil02,uid=uidg4627,gid=uidg4627 ${RGB_SHARED_DRIVE} ${MOUNTING_DIR}"
sudo mount.cifs -o credentials=/home/uidg4627/.credentials/dpfil02,uid=uidg4627,gid=uidg4627 "${RGB_SHARED_DRIVE}" "${MOUNTING_DIR}"
RET_CODE=$((RET_CODE + $?))
[[ ${RET_CODE} -ne 0 ]] && bail "Mounting ${RGB_SHARED_DRIVE} drive failed"

header2 "Storing Baseline Artifacts"
pushd ${CONMOD_SHARED_DRIVE} &> /dev/null

    echo "mkdir -p ${RELEASE_STAGING_DIR}"
    mkdir -p "${RELEASE_STAGING_DIR}"
    RET_CODE=$((RET_CODE + $?))
    [[ ${RET_CODE} -ne 0 ]] && bail "Baseline folder creation failed"

    echo "cp -rv ${STAGING_DOC_DIR} ${RELEASE_STAGING_DIR}/sdk-releases/"
    cp -rv "${STAGING_DOC_DIR}" "${RELEASE_STAGING_DIR}/sdk-releases/"
    RET_CODE=$((RET_CODE + $?))
    [[ ${RET_CODE} -ne 0 ]] && bail "Failed copying artifacts from ${STAGING_DOC_DIR}"

popd &> /dev/null

header2 "Unmount wetzlar shared drive"
sudo umount "${MOUNTING_DIR}"
RET_CODE=$((RET_CODE + $?))
[[ ${RET_CODE} -ne 0 ]] && echo "WARNING: unable to unmount shared drive, please verify the host machine"

echo "END: ${SCRIPT_NAME} [${RET_CODE}]: $(date)"
#-----------------------------------------------------------#
