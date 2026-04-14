#!/bin/bash
# ******************************************************************************
# *   Copyright (c) 2024 Continental Automotive Systems, Inc., all rights reserved
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: delivery-artifact-collector
# *
# *   Description: The main purposes of this script are:
# *                1) Creating delivery artifacts:
# *                   a) kernel_amend.tar.gz
# *                   b) msm_archive_created.tar.gz
# ******************************************************************************
SCRIPT_NAME=$(basename "${0}")
LOGFILE=$(dirname $0)/"${SCRIPT_NAME%.*}.log"
# ret_code variable
RET_CODE=0

source "${WORKSPACE}/.launchers/conmod-cm/artifacts/artifacts-common.inc"
source "${WORKSPACE}/.launchers/conmod-cm/utils/platform-common.lib"
source "${WORKSPACE}/.launchers/conmod-cm/utils/artifactory.lib"

create_kernel_amend() {
    local kernel_amend_tar=${1}

    # Create tmp folder to gather the .tar.gz contents
    local kernel_amend_tmp=$(mktemp -d)

    echo "Create ${kernel_amend_tar} file"

    pushd "${LINUX_DIR}" > /dev/null
    mkdir -p "${kernel_amend_tmp}/linux_patches"
    declare -a kernel_amend_files

    # Variable used to download opensource package from codeaurora
    local_version_var=$(git describe --dirty | sed 's/^v[.0-9]*//')
    if [ -n "${local_version_var}" ]; then
        echo "export LOCALVERSION=${local_version_var}" > "${kernel_amend_tmp}/local_version"
        # LOCALVERSION_MSM is the LOCALVERSION without  modifications, so:
        export LOCALVERSION_MSM=$(echo "${local_version_var}" | sed "s/\(.*-sa515m\)-.*/\1/")
        echo "LOCALVERSION_MSM=${LOCALVERSION_MSM}" | tee -a ${PROPERTIES_FILE}
        LINUX_PATCHES_TAR="linux_${local_version_var}_patches.tar.gz"
    else
        bail "Unable to find local_version variable from linux environment"
    fi

    # Variable used at compiling codeaurora source code to match TP delivery
    linux_tag=$(git describe --tag --abbrev=0)
    [ -n "${linux_tag}" ] && \
        echo "export KERNEL_TAG=${linux_tag}" >> "${kernel_amend_tmp}/local_version"
    [ -f "${kernel_amend_tmp}/local_version" ] && \
        kernel_amend_files+=("local_version")

    # Create conti patches over kernel package
    # Remove sensitive information from patches
    git format-patch tags/${linux_tag}..HEAD -o "${kernel_amend_tmp}/linux_patches"
    if [[ -n "$(find "${kernel_amend_tmp}" -type f -name "*.patch")" ]]; then
        sed -i '/From:.*@conti.*-.*.com/d' "${kernel_amend_tmp}"/linux_patches/*.patch
        ret=$((${ret} + $?))
    fi
    popd &> /dev/null

    pushd "${kernel_amend_tmp}"
    if [[ -n "$(find "${kernel_amend_tmp}" -type f -name "*.patch")" ]]; then
        tar -czf "${LINUX_PATCHES_TAR}" "linux_patches"
        ret=$((${ret} + $?))
        kernel_amend_files+=("${LINUX_PATCHES_TAR}")
    fi

    kernel_amend_files+=(".config")
    cp --verbose "${CONFIG_PATH}" "${kernel_amend_tmp}"

    if [ -d "${DTS_DIR}" ]; then
        dts_files=($(find "${DTS_DIR}" -type f -name "cas*.dts"  -exec basename {} \;))
        for dts in "${dts_files[@]}"; do
            cp --verbose "${DTS_DIR}/${dts}" "${kernel_amend_tmp}"
            kernel_amend_files+=("${dts}")
        done
    fi

    tar -czf "${OUTPUT_DIR}/${kernel_amend_tar}" ${kernel_amend_files[@]}
    RET_CODE=$((RET_CODE + $?))
    [[ ${RET_CODE} -ne 0 ]] && bail "Unable to create ${kernel_amend_tar} file"
    echo "Cleaning kernel_amend execution"
    popd &> /dev/null
    rm -rf "${kernel_amend_tmp}"

}

create_msm() {
    #msm variables
    local msm_tar=${1}
    local msm_tmp=$(mktemp -d)
    local msm_dir="msm-4.14"
    local msm_output="${OUTPUT_DIR}/${msm_tar}"
    local linux_project="p1/package/opensource/linux-4.14"

    [[ -z "${linux_tag}" ]] && bail "Execution error, Linux tag is empty"
    [[ -z "${LOCALVERSION_MSM}" ]] && bail "Execution error, LOCALVERSION_MSM is not set!"

    # only create new msm archive, if there is no file with the same version uploaded...
    local MSM_FILE_PATH="${ARTIFACTORY_SERVER}/${REPOSITORY}/${release_id}/msm/${LOCALVERSION_MSM}/${msm_tar}"
    artifactory_path_exists "${MSM_FILE_PATH}"
    if [ $? -eq 0 ]; then
        echo "Info: no new ${msm_tar} file will be created! Version for msm/${LOCALVERSION_MSM} is already uploaded!"
        RET_CODE=42
    else
        echo "Create ${msm_tar} file"
        echo "Linux Version = ${linux_tag}"

        pushd "${msm_tmp}" > /dev/null
            echo "git clone --branch ${linux_tag} --depth 1 buic-scm:${linux_project} ${msm_dir}"
            git clone --branch ${linux_tag} --depth 1 buic-scm:${linux_project} ${msm_dir}
            RET_CODE=$((RET_CODE + $?))
            [[ ${RET_CODE} -ne 0 ]] && bail "unable to clone msm-4.14 repository"

            cd ${msm_dir}
            echo "Removing .git directory"
            rm -rf .git/
            [[ $? -ne 0 ]] && bail "Unable to remove .git folder"
            echo "tar -czf "${msm_output}" ."
            tar -czf "${msm_output}" .
            RET_CODE=$((RET_CODE + $?))
            [[ ${RET_CODE} -ne 0 ]] && bail "unable to create ${msm_tar}"
            echo "Cleaning msm execution"

        popd &> /dev/null
        rm -rf "${msm_tmp}"
    fi
}

# uploads msm created after a build to msm folder. The qualcomm version string is extracted from the passed properties file.
# It needs an entry named 'LOCALVERSION_MSM'
upload_build_msm(){
    local workspace=${1?workspace is required}
    local release_id=${2?release_id is required}
    local baseline=${3?baseline is required}
    local file=${4?file is required}
    local dry_run=${5}

    local MSM_FOLDER_PATH="${ARTIFACTORY_SERVER}/${REPOSITORY}/${release_id}/msm"
    echo "Checking for properties file ${PROPERTIES_FILE}..."
    if [ -f ${PROPERTIES_FILE} ]; then
        LOCALVERSION_MSM=$(grep "LOCALVERSION_MSM" ${PROPERTIES_FILE} | cut -d'=' -f2)
        [[ -z "${LOCALVERSION_MSM}" ]] && echo "${PROPERTIES_FILE} does not contain LOCALVERSION_MSM!!!" && exit 1
        echo "Local MSM version for the build: ${LOCALVERSION_MSM}"
        local artifactory_url="${MSM_FOLDER_PATH}/${LOCALVERSION_MSM}/"
    else
        # not able to continue here without the properties files, so...
        echo "${PROPERTIES_FILE} does not exist!"
        exit 1
    fi

    # only upload new msm archive, if there is no file with the same version uploaded...
    local MSM_FILE_PATH="${artifactory_url}/${file}"
    artifactory_path_exists "${MSM_FILE_PATH}"
    if [ $? -eq 0 ]; then
        echo "Info: no new ${MSM_FILE_PATH} file will be uploaded! Version for msm/${LOCALVERSION_MSM} is already uploaded!"
        ret_code=0
    else
        # create folders, if they don't exist...
        # parent...
        create_folder "${MSM_FOLDER_PATH}" "${dry_run}"
        # msm folder
        create_folder "${artifactory_url}" "${dry_run}"

        #local artifactory_url="${ARTIFACTORY_SERVER}/${REPOSITORY}/${release_id}/${baseline}"
        echo "Upload to: ${artifactory_url}. file: ${file}"
        # Control flow
        local ret_code          # Overall return code for the function
        local curl_ret_code     # Internal return code for the retry strategy
        local max_retries       # Number of curl retries
        local retry_number      # Counter for the retries

        # Settings
        ret_code=0
        max_retries=3

        # Action
        token=$(read_artifactory_credentials)

        if [[ -z "${token}" ]]; then
            echo "Unable to retrieve authentication token"
            return 13
        fi

        pushd "${workspace}"
            if [[ -e "${file}" && -s "${file}" ]]; then
                echo "${dry_run:+[DRY RUN] } curl -s -X PUT ${artifactory_url}${file} -T ${workspace}/${file}"

                if [[ -z "${dry_run}" ]]; then
                    retry_number=0
                    curl_ret_code=1
                    while [[ "${curl_ret_code}" -gt 0 && "${retry_number}" -le "${max_retries}" ]]; do
                        curl -s -u "${token}" -X PUT "${artifactory_url}${file}" -T "${workspace}/${file}"
                        curl_ret_code=$?
                        retry_number=$((retry_number + 1))
                    done

                    # Report the last execution
                    ret_code=$((ret_code + curl_ret_code))
                fi
            else
                echo "File: ${file} not found"
            fi
        popd
    fi
    RET_CODE="${ret_code}"
}

# ----------- Main Execution  ----------- #
# Script variables - default values
LINUX_PATH="package/opensource/linux"
LINUX_PATCHES_TAR="linux_patches.tar.gz"
KERNEL_FILE="kernel_amend.tar.gz"
MSM_FILE="msm-4.14_archive_created.tar.gz"
CAS_ARCH="arm64"

process_cli_parameters "$@"
check_parameters

# Properties file
JOB_NAME=$(basename "${WORKSPACE}" | cut -d@ -f1)
PROPERTIES_FILE="${WORKSPACE}/${JOB_NAME}.properties"

echo "LOGGING to ${LOGFILE}"
exec > >(tee "${LOGFILE}");
# ----------------------------------------------------------- #
# All output from commands in this block sent to file $LOGFILE.

echo "Import external libraries"
source "${WORKSPACE}/.launchers/conmod-cm/utils/platform-common.lib"

# Exports Required for Cloning
export http_proxy="http://cntlm:3128"
export https_proxy="https://cntlm:3128"


header1 "ARTIFACTS CONSTRUCTION"
echo
echo "                               DETAILS"
echo
echo "Execution Description: "
echo
echo "WORKSPACE:            ${WORKSPACE}"
echo "LINUX_DIR:            ${LINUX_DIR}"
echo "CAS_ARCH:             ${CAS_ARCH}"
echo "OUTPUT_DIR:           ${OUTPUT_DIR}"
echo "OUTPUT_FILES:         ${KERNEL_FILE}, ${MSM_FILE}"
echo "PROPERTIES_FILE:      ${PROPERTIES_FILE}"
echo

header2 "Kernel Amend Generation"
create_kernel_amend "${KERNEL_FILE}"
[[ ${RET_CODE} -eq 0 ]] && echo "KERNEL_AMEND=${OUTPUT_DIR}/${KERNEL_FILE}" | tee -a ${PROPERTIES_FILE}

header2 "Msm tar file Generation"
create_msm "${MSM_FILE}"
[[ ${RET_CODE} -eq 0 ]] && echo "MSM_TAR_FILE=${OUTPUT_DIR}/${MSM_FILE}" | tee -a ${PROPERTIES_FILE}
[[ ${RET_CODE} -eq 42 ]] && RET_CODE=0 && echo "MSM_TAR_FILE=ALREADY_EXISTING" | tee -a ${PROPERTIES_FILE}

header2 "Uploading kernel_amend archive..."
upload_artifacts "${WORKSPACE}" "${RELEASE_ID}" "${BASELINE_NAME}" "kernel_amend.tar.gz"
RET_CODE=$((RET_CODE + $?))
[[ ${RET_CODE} -ne 0 ]] && echo "Error could not upload kernel_amend archive!"
header2 "Uploading MSM archive..."
upload_build_msm "${WORKSPACE}" "${RELEASE_ID}" "${BASELINE_NAME}" "msm-4.14_archive_created.tar.gz"
[[ ${RET_CODE} -ne 0 ]] && echo "Error could not upload msm archive archive!"

echo "END: ${SCRIPT_NAME} [${RET_CODE}]: $(date)"
# ----------------------------------------------------------- #
