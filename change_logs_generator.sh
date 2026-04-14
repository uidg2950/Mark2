#!/bin/bash
# *****************************************************************************
# *
# *  (c) 2024 Continental Automotive Systems, Inc., all rights reserved
# *
# *  All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *  Any reproduction of this material without written consent from
# *  Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *  Filename: changes_logs_generator.sh
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
export CAS_TARGET_HW=${3}
export BASE_VERSION=${4}
export RELEASE_ID=${5}
export NEW_BASELINE=${6}
export OLD_BASELINE=${7}

echo "Import external libraries"
source "${WORKSPACE}/.launchers/linux/base.lib"
source "${WORKSPACE}/.launchers/linux/common.lib"

if [ "$#" -lt 6 ] || [ "$#" -gt 7 ]; then
    bail "Illegal number of parameters: $#"
fi

## SCRIPT VARIABLES
JOB_NAME=$(basename "${WORKSPACE}" | cut -d@ -f1)
PROPERTIES_FILE="${WORKSPACE}/${JOB_NAME}.properties"
SHARED_DRIVE_DOCS="/u01/app/jenkins/documents"
GET_TICKETS_SCRIPT="get_tickets.sh"
SCRIPT_WORKAROUND="${WORKSPACE}/.launchers/conmod-cm/workarounds/"
# Repo configuration
REPO_BRANCH="stable-conti"
REPO_URL="buic-scm:IIC_SW_Tools/git-repo"
# Overall return status
RET_CODE=0

# Handle exit codes to always promote variables
function on_exit {
    echo "Trapping on exit code: $?"

    header2 "PROMOTE ENV VARIABLES"
    echo "Promoting to: ${PROPERTIES_FILE}"
    echo "BASELINE_VERSION=${NEW_BASELINE}"         | tee -a "${PROPERTIES_FILE}"
    echo "BUILD_FILES_URL=${WORKSPACE}"             | tee -a "${PROPERTIES_FILE}"
    echo "CAS_TARGET_HW=${CAS_TARGET_HW}"           | tee -a "${PROPERTIES_FILE}"
    echo "END: ${SCRIPT_NAME} [${RET_CODE}]: $(date)"
}

trap on_exit EXIT

echo "##################################################################"
echo "                               DETAILS"
echo
echo "Build description: "
echo
echo "WORKSPACE:            ${WORKSPACE}"
echo "PROJECT:              ${PROJECT}"
echo "CAS_TARGET_HW:        ${CAS_TARGET_HW}"
echo "BASE_VERSION:         ${BASE_VERSION}"
echo "RELEASE_ID:           ${RELEASE_ID}"
echo "NEW_BASELINE:         ${NEW_BASELINE}"
echo "OLD_BASELINE:         ${OLD_BASELINE}"
echo
echo


header1 "BUILD AREA"

# Cleaning Workspace
if [ -n "${WORKSPACE}" ]; then
    # Force bootstrap
    ERASE=('logs' '*.properties' 'sdk' 'UPC' '*.tar.gz' '*.tar' '*.txt' '.build' 'platform-framework' 'platform-hal' '.repo/local_manifests/' 'release-host' '*')

    echo "Deleting previous contents"
    for FILE in "${ERASE[@]}"; do
        echo "rm -rf ${WORKSPACE}/${FILE}"
        rm -rf ${WORKSPACE}/${FILE}

        #Verify artifacts got removed
        ls ${WORKSPACE}/${FILE} 2>/dev/null
    done
fi

# Checking shared drive availability
df "${SHARED_DRIVE_DOCS}" 1> /dev/null 2>&1
RET_CODE=$((RET_CODE + $?))
[[ ${RET_CODE} -ne 0 ]] && bail "Shared drive ${SHARED_DRIVE_DOCS} not available"

CHANGE_LOGS_DIR="${SHARED_DRIVE_DOCS}/sdk_packages/change_logs"
[[ ! -d "${CHANGE_LOGS_DIR}" ]] && bail "${CHANGE_LOGS_DIR} not found"

# FIXME: Workaround for conmod-sa515m-3.y hosted in OTP Repositories
PROJECT_NEST="${PROJECT}"
[[ ${RELEASE_ID} =~ conmod-sa515m ]] && PROJECT_NEST="otp"

header1 "New Repository for ${NEW_BASELINE} will be created"
repo_init "${PROJECT_NEST}" "${NEW_BASELINE}" all "${REPO_BRANCH}" "${REPO_URL}"

# Informative
header2 "GET PREVIOUS_BASELINE"
MANIFEST_REMOTE=$(git --git-dir="${MANIFESTS_DIR}/.git" config --get remote.origin.url)
RELEASE_REMOTE=$(git --git-dir="${MANIFESTS_DIR}/.git" config --get remote.origin.url | sed 's/manifest/release/')
RELEASE_REMOTE="${RELEASE_REMOTE}-${CAS_TARGET_HW}"
echo "> get_latest_remote_baseline ${CAS_TARGET_HW} ${PROJECT} ${BASE_VERSION} ${RELEASE_REMOTE}"
PREVIOUS_BASELINE=$(get_latest_remote_baseline ${CAS_TARGET_HW} ${PROJECT} ${BASE_VERSION} ${RELEASE_REMOTE})
echo "PREVIOUS_BASELINE=${PREVIOUS_BASELINE}"
[ "${PREVIOUS_BASELINE}" == "${NEW_BASELINE}" ] && echo "${NEW_BASELINE} is the latest baseline available"

header2 "REPO SYNC"
echo "> repo_sync hard full"
repo_sync hard full
RET_CODE=$((RET_CODE + $?))
[[ ${RET_CODE} -ne 0 ]] && bail "unable to commit results due to sync errors"

header2 "Patching script for changes log files generation"
[[ ! -f "${SCRIPT_WORKAROUND}/${GET_TICKETS_SCRIPT}" ]] && bail "Patched Script not found in ${SCRIPT_WORKAROUND}"
cp "${SCRIPT_WORKAROUND}/${GET_TICKETS_SCRIPT}" "${WORKSPACE}/tools/repo/${GET_TICKETS_SCRIPT}"
RET_CODE=$((RET_CODE + $?))
[[ ${RET_CODE} -ne 0 ]] && bail "Update of script failed"
echo "Script was successfully patched, we are ready!!"

header2 "GENERATE CHANGE-LOG FILES"
generate_change_log "${WORKSPACE}" "${OLD_BASELINE}" "${MANIFEST_BRANCH}"
RET_CODE=$((RET_CODE + $?))
[[ ${RET_CODE} -ne 0 ]] && echo "WARNING: No change files generated "

header2 "Staging Changes log files"
# Extracting version id
nversion=$(echo "${NEW_BASELINE}" | sed 's/.*-//g')
oversion=$(echo "${OLD_BASELINE}" | sed 's/.*-//g')

# Staging change files
changes_files=('change-log.txt' 'change-summary.txt')
for file in "${changes_files[@]}"; do
    [[ ! -f "${WORKSPACE}/${file}" ]] && bail "${file} not found"

    echo "Change permissions - Read Only"
    chmod 444 "${file}"

    # name of the files has the reference to the baselines
    echo "> cp -p ${WORKSPACE}/${file} ${CHANGE_LOGS_DIR}/${nversion}_${oversion}_${file}"
    cp -p "${WORKSPACE}/${file}" "${CHANGE_LOGS_DIR}/${nversion}_${oversion}_${file}"
done

# Notification
echo "Change logs availables in: ${CHANGE_DIR}"

echo "END: ${SCRIPT_NAME} [${RET_CODE}]: $(date)"
# ----------------------------------------------------------- #
