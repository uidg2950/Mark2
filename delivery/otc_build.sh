#!/bin/bash
# *****************************************************************************
# *
# *  (c) 2021-2024 Continental Automotive Systems, Inc., all rights reserved
# *
# *  All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *  Any reproduction of this material without written consent from
# *  Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *  Filename: otc_build.sh
# *
# *  Description:
# *
# *
# *****************************************************************************

SCRIPT_NAME=$(basename "${BASH_SOURCE[0]}")
LOGFILE=$(dirname "${BASH_SOURCE[0]}")/"${SCRIPT_NAME%.*}.log"
echo "LOGGING to ${LOGFILE}"
exec > >(tee "${LOGFILE}");
RET_CODE=0
# ----------------------------------------------------------- #
# All output from commands in this block sent to file $LOGFILE.
echo "START: ${SCRIPT_NAME} $(date)"

help_info() {
    cat << HELP
./$(basename "$0") --workspace /path/to/workspace --baseline conmod-sa515m-3.2.27.0 --username auto\\\uid99999 --password YOUR_WINDOWS_SECRET_PASSWORD
Script for manual testing of esim.

Options:
    -h|--help                   Display this information.
    -w|--workspace              Workspace directory.
    -b|--baseline               Artifact output directory.
    -r|--release_id             Baseline release id.
    -u|--username               OTC user
    -p|--password               Windows domain password
    -d|--domain                 Windows domain
    -f|--flavor                 Build flavor (prod/devel)

HELP
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
            -r|--release_id)
                RELEASE_ID="$1"
                shift
                ;;
            -b|--baseline)
                BASELINE_VERSION="$1"
                shift
                ;;
            -u|--username)
                OTC_USERNAME="$1"
                shift
                ;;
            -p|--password)
                OTC_PASSWORD="$1"
                shift
                ;;
            -d|--domain)
                OTC_DOMAIN="$1"
                shift
                ;;
            -f|--flavor)
                FLAVOR="$1"
                shift
                ;;
            *)
                echo -e "Invalid parameter: $param.\nUse -h|--help for more information."
                exit 1
                ;;
        esac
    done
}

init_parameters() {
    echo "Import external libraries"
    if [ ! -d "${WORKSPACE}" ]; then
        echo -e "Workspace dir not exists ${WORKSPACE}"
        exit 1;
    fi

    source "${WORKSPACE}/.launchers/linux/base.lib"
    source "${WORKSPACE}/.launchers/linux/common.lib"
    source "${WORKSPACE}/.launchers/linux/pipeline.lib"
    source "${WORKSPACE}/.launchers/conmod-cm/utils/artifactory.lib"
    source "${WORKSPACE}/.launchers/conmod-cm/utils/archive-tools.lib"

    [[ -z "${OTC_USERNAME}" ]] && bail "OTC Username is empty"
    [[ -z "${OTC_DOMAIN}" ]] && bail "OTC user domain is empty"
    [[ -z "${OTC_PASSWORD}" ]] && bail "OTC user password is empty"

    OTC_ACCOUNT="${OTC_DOMAIN}\\\\\\${OTC_USERNAME}"

    STAGING_DIR="$(mktemp -d ${WORKSPACE}/SDK-XXXXXX)"
    SDK_BUNDLE_DIR="tp_sdk_${RELEASE_ID}_pkg"
    OTC_DEST="${STAGING_DIR}/${SDK_BUNDLE_DIR}/sdk/"

    PKG_ZIP="tp_sdk_${BASELINE_VERSION}_pkg.zip"
    SDK_BUNDLE_ZIP="${STAGING_DIR}/${PKG_ZIP}"

    REPO_BRANCH="stable-conti"
    REPO_URL="buic-scm:IIC_SW_Tools/git-repo"
    CAS_TARGET_HW=sa515m
    OTC_WORKDIR=${WORKSPACE}/build-otc
    FILE_REPLACMENT_FOLDER=${WORKSPACE}/boot-replacement
    OTC_SDK_TAR=${OTC_WORKDIR}/sdk_signed.tar.gz
    OTC_CONTI_SIGNED=${OTC_WORKDIR}/conti-signed-images.tar.gz

    PROD_STR=''
    [[ "${FLAVOR}" == "prod" ]] && PROD_STR='P=1'
    [[ "${FLAVOR}" == "devel" ]] && PROD_STR='P=0'
}

print_info() {
    echo "##################################################################"
    echo "                               DETAILS"
    echo
    echo "Build description: "
    echo
    echo "WORKSPACE:            ${WORKSPACE}"
    echo "RELEASE_ID:           ${RELEASE_ID}"
    echo "BASELINE_VERSION:     ${BASELINE_VERSION}"
    echo "OTC_USERNAME:         ${OTC_ACCOUNT}"
    echo "OTC_DEST:             ${OTC_DEST}"
    echo "FLAVOR:               ${FLAVOR}"
    echo "PROD_STR:             ${PROD_STR}"
    echo
}

# Handle exit codes to always promote variables
function on_exit {
    echo "Trapping on exit code: $?"

    header2 "PROMOTE ENV VARIABLES"
    echo "Promoting to: ${PROPERTIES_FILE}"
    echo "END: ${SCRIPT_NAME} [${RET_CODE}]: $(date)"
}

trap on_exit EXIT

build_signed() {
  header1 "PREPARING BUILD AREA"
  echo "> rm -rf ${OTC_WORKDIR}"
  rm -rf ${OTC_WORKDIR}
  echo "> mkdir -p ${OTC_WORKDIR}"
  mkdir -p ${OTC_WORKDIR}
  echo "> pushd "${OTC_WORKDIR}" >/dev/null"
  pushd "${OTC_WORKDIR}" >/dev/null

  header1 "New Repository for ${BASELINE_VERSION} will be created"
  repo_init "otp" "${BASELINE_VERSION}" all "${REPO_BRANCH}" "${REPO_URL}"

  header2 "REPO SYNC"
  echo "> repo_sync hard full"
  repo_sync hard full
  RET_CODE=$((RET_CODE + $?))
  [[ ${RET_CODE} -ne 0 ]] && bail "unable to commit results due to sync errors"

  header2 "Workaround for openssl3 signing"
  SEARCH_PATTERN='export OTP_HOST_VERSION=conmod-host-3.*$'
  REPLACE_PATTERN='export OTP_HOST_VERSION=otp-host-3.426.3'
  ENV_RELATIVE=".repo/manifests/env-plf-config"
  echo "> sed --in-place 's%${SEARCH_PATTERN}%${REPLACE_PATTERN}%' ${ENV_RELATIVE}"
  sed --in-place "s%${SEARCH_PATTERN}%${REPLACE_PATTERN}%" "${ENV_RELATIVE}"

  header2 "Building OTC"
  echo "> make ${PROD_STR} CAS_TARGET_HW='${CAS_TARGET_HW}'  OTC_USER='${OTC_ACCOUNT}' OTC_PASS='DON'T PEEP ON PASS' OTC_KEY='prod'"
  make ${PROD_STR} CAS_TARGET_HW="${CAS_TARGET_HW}" OTC_USER="${OTC_ACCOUNT}" OTC_PASS="${OTC_PASSWORD}" OTC_KEY='prod'

  RET_CODE=$((RET_CODE + $?))
  [[ ${RET_CODE} -ne 0 ]] && bail "unable to build project"

  echo "> make image ${PROD_STR} CAS_TARGET_HW='${CAS_TARGET_HW}' OTC_USER='${OTC_ACCOUNT}' OTC_PASS='DON'T PEEP ON PASS' OTC_KEY='prod'"
  make image ${PROD_STR} CAS_TARGET_HW="${CAS_TARGET_HW}" OTC_USER="${OTC_ACCOUNT}" OTC_PASS="${OTC_PASSWORD}" OTC_KEY='prod'

  RET_CODE=$((RET_CODE + $?))
  [[ ${RET_CODE} -ne 0 ]] && bail "unable to generate images"

  echo "> make sdk ${PROD_STR} CAS_TARGET_HW='${CAS_TARGET_HW}' OTC_USER='${OTC_ACCOUNT}' OTC_PASS='DON'T PEEP ON PASS' OTC_KEY='prod'"
  make sdk ${PROD_STR} CAS_TARGET_HW="${CAS_TARGET_HW}" OTC_USER="${OTC_ACCOUNT}" OTC_PASS="${OTC_PASSWORD}" OTC_KEY='prod'

  RET_CODE=$((RET_CODE + $?))
  [[ ${RET_CODE} -ne 0 ]] && bail "unable to generate SDK"

  popd &> /dev/null
}

upload_vmlinux() {
    header1 "copying OTC vmlinux to shared_drive"
    echo "> pushd "${OTC_WORKDIR}" >/dev/null"
    pushd "${OTC_WORKDIR}" >/dev/null

    local RELEASE_FOLDER="/u01/app/jenkins/releases/${RELEASE_ID}/${BASELINE_VERSION}-devel"
    [[ ! -d "${RELEASE_FOLDER}" ]] && bail "Release folder not existed ${RELEASE_FOLDER}"
    local BUILD_SHARE="${RELEASE_FOLDER}/otc/"

    echo "mkdir -p ${BUILD_SHARE}"
    mkdir -p ${BUILD_SHARE}

    header1 "copying otc-modem elf"
    copy_modem_elf "${OTC_WORKDIR}" "${BUILD_SHARE}"

    header1 "copying otc-modem QShrink"
    copy_modem_qshrink "${OTC_WORKDIR}" "${BUILD_SHARE}"
    RET_CODE=$((RET_CODE + $?))
    [[ ${RET_CODE} -ne 0 ]] && bail "Failed to copy modem_qshrink"

    header1 "copying otc-elf"
    copy_elfs "${OTC_WORKDIR}" "${BUILD_SHARE}"

    header1 "copying otc-vmlinux"
    copy_vmlinux "${OTC_WORKDIR}" "${BUILD_SHARE}"
    RET_CODE=$((RET_CODE + $?))
    [[ ${RET_CODE} -ne 0 ]] && bail "Failed to copy vminux"
    
    header1 "Copy conti-signed artifacts"
    
    echo "cp ${OTC_CONTI_SIGNED} ${OTC_WORKDIR}/conti-signed-images-otc-raw.tar.gz"
    cp ${OTC_CONTI_SIGNED} ${OTC_WORKDIR}/conti-signed-images-otc-raw.tar.gz

    ARTIFACTS=$(ls ./vmlinux.tar.gz ./qcom-bsp.tar.gz ./conti-signed-images-otc-raw.tar.gz 	./modem_qshrink.tar.gz 	./modem_elf.tar.gz 2>/dev/null)

    header1 "upload artifacts"
    upload_artifacts "${OTC_WORKDIR}" "${RELEASE_ID}" "${BASELINE_VERSION}/otc" "${ARTIFACTS}"
    RET_CODE=$((RET_CODE + $?))
    [[ ${RET_CODE} -ne 0 ]] && bail "Failed to upload otc signed artifacts"

    popd &> /dev/null
}

replace_boot_img () {
  echo "Replace boot img:"

  local WORKDIR=${1?Workdir is required}
  local OUTPUT_FILE=${2?Output File required}
  local BOOT_SOURCE=${3?Boot source file is required}
  local BOOT_DEST=${4?Boot destination file is required}

  echo "Workdir: ${WORKDIR}"
  echo "Target file: ${OUTPUT_FILE}"
  echo "Boot source path: ${BOOT_SOURCE}"
  echo "Boot destination path: ${BOOT_DEST}"

  [[ ! -f "${OUTPUT_FILE}" ]]  && bail "${OUTPUT_FILE} not available"

  echo "mkdir -p ${WORKDIR}"
  mkdir -p ${WORKDIR}

  pushd ${WORKDIR}
    echo "> tar --extract --ungzip --file ${OUTPUT_FILE} --directory ."
    tar --extract --ungzip --file "${OUTPUT_FILE}" --directory .
    RET_CODE=$((RET_CODE + $?))
    [[ ${RET_CODE} -ne 0 ]]  && bail "Unable to extract tar.archive to working folder"

    echo "mv ${BOOT_SOURCE} ${BOOT_DEST}"
    mv "${BOOT_SOURCE}" "${BOOT_DEST}"
    [[ $? -ne 0 ]] && bail "Unable to move from ${BOOT_SOURCE} to ${BOOT_DEST}"

    TAR_FILES=$(ls -A)
    echo "tar --create --gzip --file ${OUTPUT_FILE} ${TAR_FILES}"
    tar --create --gzip --file "${OUTPUT_FILE}" ${TAR_FILES}
    [[ $? -ne 0 ]] && bail "Unable to updated ${OUTPUT_FILE}"
  popd

  rm -rf ${WORKDIR}
}

update_bundle() {
  header1 "Copying resulted artifacts"

  if [ ! -f ${OTC_SDK_TAR} ]; then
    bail "OTC sdk.tar at ${OTC_SDK_TAR} not found"
  fi
  if [ ! -f ${OTC_CONTI_SIGNED} ]; then
    bail "OTC sdk.tar at ${OTC_CONTI_SIGNED} not found"
  fi

#  DO Not replace boot.img inside SDK.tar.gz bcs might be needed for generation of unsigned images
#  replace_boot_img "${FILE_REPLACMENT_FOLDER}" "${OTC_SDK_TAR}" "${FILE_REPLACMENT_FOLDER}/boot/boot_tier1_4K.img" "${FILE_REPLACMENT_FOLDER}/boot/boot_4K.img"
  replace_boot_img "${FILE_REPLACMENT_FOLDER}" "${OTC_CONTI_SIGNED}" "${FILE_REPLACMENT_FOLDER}/boot_tier1.img" "${FILE_REPLACMENT_FOLDER}/boot.img"
  replace_boot_img "${FILE_REPLACMENT_FOLDER}" "${OTC_CONTI_SIGNED}" "${FILE_REPLACMENT_FOLDER}/boot_tier1.img.signed" "${FILE_REPLACMENT_FOLDER}/boot.img.signed"

  cp ${OTC_SDK_TAR} ${OTC_DEST}/sdk.tar.gz

  RET_CODE=$((RET_CODE + $?))
  [[ ${RET_CODE} -ne 0 ]] && bail "Unable to copy ${OTC_SDK_TAR} dir"

  cp ${OTC_CONTI_SIGNED} ${OTC_DEST}/

  RET_CODE=$((RET_CODE + $?))
  [[ ${RET_CODE} -ne 0 ]] && bail "Unable to create ${OTC_CONTI_SIGNED} dir"

  local SIGNED_MARK_FILE="${OTC_DEST}/otc-signed.txt"
  echo "> Creating label file ${SIGNED_MARK_FILE}"
  echo "'conti-signed-images.tar.gz' signed with Continental OTC keys on $(date)" > ${SIGNED_MARK_FILE}

  RET_CODE=$((RET_CODE + $?))
  [[ ${RET_CODE} -ne 0 ]] && bail "Unable to create ${SIGNED_MARK_FILE} file"

  header2 "Updating tp_sdk_${BASELINE_VERSION}_pkg.zip file"
  pushd "${STAGING_DIR}" &>/dev/null
    echo "> zip --filesync --recurse-paths ${SDK_BUNDLE_ZIP} ${SDK_BUNDLE_DIR}"
    zip --filesync --recurse-paths "${SDK_BUNDLE_ZIP}" "${SDK_BUNDLE_DIR}"
    RET_CODE=$((RET_CODE + $?))
    [[ "${RET_CODE}" -ne 0 ]] && bail "Unable to update the ${SDK_BUNDLE_ZIP} file"
  popd &>/dev/null
}


cleanup() {
  header1 "Cleanup"
  echo "> rm -rf ${OTC_WORKDIR}"
  rm -rf ${OTC_WORKDIR}
}

main() {
  process_cli_parameters "$@"
  init_parameters
  print_info
  download_artifacts "${STAGING_DIR}" "${RELEASE_ID}" "${BASELINE_VERSION}/sdk" "${PKG_ZIP}"
  unpack_zip_archive "${SDK_BUNDLE_ZIP}" "${STAGING_DIR}"
  build_signed
  upload_vmlinux
  update_bundle
  upload_artifacts "${STAGING_DIR}" "${RELEASE_ID}" "${BASELINE_VERSION}/otc" "${PKG_ZIP}"
#  cleanup
}

main "$@"
