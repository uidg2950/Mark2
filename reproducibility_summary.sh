# *****************************************************************************
# *
# *  (c) 2020 Continental Automotive Systems, Inc., all rights reserved
# *
# *  All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *  Any reproduction of this material without written consent from
# *  Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *  Filename: reproducibility_summary.sh
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
export RELEASE_ID=${6}

echo "Import external libraries"
source "${WORKSPACE}/.launchers/linux/base.lib"
source "${WORKSPACE}/.launchers/linux/common.lib"

### Script Variables
MANIFESTS_DIR="${WORKSPACE}/.repo/manifests"
RELEASE_HOST_DIR="${WORKSPACE}/release-host"
RELEASE_TOOLCHAIN_DIR="${WORKSPACE}/release-toolchain"
TELEMATICS_RELEASE_DRIVE="/u01/app/jenkins/releases"
RET_CODE=0

# Checking release drive availability
df "${TELEMATICS_RELEASE_DRIVE}" 1> /dev/null 2>&1
RET_CODE=$((RET_CODE + $?))
[[ ${RET_CODE} -ne 0 ]] && bail "Shared drive ${TELEMATICS_RELEASE_DRIVE} not available"

header2 "DETAILS"
echo
echo "Description"
echo
echo "WORKSPACE:                    ${WORKSPACE}"
echo "PROJECT:                      ${PROJECT}"
echo "BASE_VERSION:                 ${BASE_VERSION}"
echo "BASELINE_VERSION:             ${BASELINE_VERSION}"
echo "CAS_TARGET_HW:                ${CAS_TARGET_HW}"
echo "RELEASE_ID:                   ${RELEASE_ID}"
echo
echo "TELEMATICS_RELEASE_DRIVE:     ${TELEMATICS_RELEASE_DRIVE}"
echo

# Summary
header2 "Summary of reproducibility execution" 
echo "> Baseline: ${BASELINE_VERSION}"

[[ ! -f ${MANIFESTS_DIR}/env-plf-config ]] && bail "${MANIFESTS_DIR}/env-plf-config not found" 

# toolchain and host comparsion
header2 "otp-toolchain and otp-host versions"
OTP_TOOLCHAIN_VALUE=$(grep "OTP_TOOLCHAIN_VERSION" ${MANIFESTS_DIR}/env-plf-config | cut -d "=" -f 2)
OTP_TOOLCHAIN_CHECKOUT=$(git --git-dir="${RELEASE_TOOLCHAIN_DIR}/.git" rev-parse --abbrev-ref HEAD)
OTP_HOST_VALUE=$(grep "OTP_HOST_VERSION" ${MANIFESTS_DIR}/env-plf-config | cut -d "=" -f 2)
OTP_HOST_CHECKOUT=$(git --git-dir="${RELEASE_HOST_DIR}/.git" rev-parse --abbrev-ref HEAD)


echo -e "\nInformation from Manifest:\totp-host: ${OTP_HOST_VALUE}\t\totp-toolchain: ${OTP_TOOLCHAIN_VALUE}"
echo -e "Information from Repository:\totp-host: ${OTP_HOST_CHECKOUT}\t\totp-toolchain: ${OTP_TOOLCHAIN_CHECKOUT}"

# Number of files & Size of image folder
header2 "Number of files and size of release folder"
FILES_BASELINE=$(ls -al ${TELEMATICS_RELEASE_DRIVE}/${RELEASE_ID}/${BASELINE_VERSION}-devel/release/images/devel/4K | wc -l)
SIZE_BASELINE=$(du -sh ${TELEMATICS_RELEASE_DRIVE}/${RELEASE_ID}/${BASELINE_VERSION}-devel/release/images/devel/4K | cut -d"/" -f1)
REPROD_FILES_BASELINE=$(ls -al ${WORKSPACE}/release/images/devel/4K | wc -l)
REPROD_SIZE_BASELINE=$(du -sh ${WORKSPACE}/release/images/devel/4K | cut -d"/" -f1)

echo -e "\nOriginal Baseline:\tNumber of files: ${FILES_BASELINE}\t\tSize of folder: ${SIZE_BASELINE}"
echo -e "Reproduced Baseline:\tNumber of files: ${FILES_BASELINE}\t\tSize of folder: ${REPROD_SIZE_BASELINE}"

# This is only for informative purposes
header2 "Diff folders summary"

diff -rq ${TELEMATICS_RELEASE_DRIVE}/${RELEASE_ID}/${BASELINE_VERSION}-devel/release/images/devel/4K ${WORKSPACE}/release/images/devel/4K

echo "END: ${SCRIPT_NAME} [${RET_CODE}]: $(date)"
# ----------------------------------------------------------- #
