#!/bin/bash
# ***************************************************************************************
# *   Copyright (c) 2022-2024 Continental Automotive Systems, Inc., all rights reserved
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: generate-sdk-constructor.sh
# *
# *   Description: Script responsible for generating of sdk-constructor archive it
# *
# ***************************************************************************************

source "${WORKSPACE}/.launchers/conmod-cm/sdk/sdk-common.inc"

BUILD_DIR=".build"
ENV_BUILDSYS_FILE="${BUILD_DIR}/env-buildsys-static"
ENV_COMMON_FILE="${BUILD_DIR}/env-common"
MANIFESTS_DIR=".repo/manifests"
PACKAGE_INFO_FILE="${SDK_WORKSPACE}/release/docs/package-info.txt"
ENV_OVERWRITE_FILE="${WORKSPACE}/.launchers/conmod-cm/sdk/sdkc/env-overwrite"

init_workarea() {
  BUILD_TOOLS_DIR="tools/build"
  CAS_TARGET_HW="sa515m"
  repo_init "otp" "${BASELINE_VERSION}"
  [[ $? -ne 0 ]] && bail "Unable to repo_init due to sync errors"

  header1 "Fixing Manifest for SDK Generation"

  echo "> Fix format of manifest"
  xmllint --format "${MANIFESTS_DIR}/default.xml"  > "${MANIFESTS_DIR}/temporary.xml"
  [[ $? -ne 0 ]] && bail "Unable to create temp reformated manifest"
  mv "${MANIFESTS_DIR}/temporary.xml" "${MANIFESTS_DIR}/default.xml"
  [[ $? -ne 0 ]] && bail "Failed to replace manifest"

  refs_to_remove=( "platform-framework" "platform-hal" "specs" "telematics-ut" )

  # removing unnecessary references from Manifest
  for ref in "${refs_to_remove[@]}"; do
    echo "Removing ${ref} reference"
    sed -i "/${ref}/d" "${MANIFESTS_DIR}/default.xml"
  done

  header2 "REPO SYNC"
  echo "> repo_sync soft full"
  repo_sync soft full
  [[ $? -ne 0 ]] && bail "Unable to commit results due to sync errors"

  header2 "PREPARE WORK AREA"
  header3 "Disabling target compilation goals"
  sed -Ei '/export (bld_goals|bld_target_goals|bld_target_s_goals|\
bld_packages|bld_target_packages)/d' "${BUILD_TOOLS_DIR}"/scripts/misc/bootstrap

  pattern=". \$(bld_build_dir)\/paths"
  pattern_new="touch \$(bld_build_dir)\/paths"
  [[ -f "${BUILD_TOOLS_DIR}/main.mk" ]] && sed -i "s/$pattern/$pattern_new/" "${BUILD_TOOLS_DIR}/main.mk"

  # Prevent from getting find warnings
  echo "mkdir -p package/specs"
  mkdir -p package/specs

  echo "make clean ${PROD_STR} CAS_TARGET_HW=${CAS_TARGET_HW}"
  make clean ${PROD_STR} CAS_TARGET_HW="${CAS_TARGET_HW}"
  [[ ${RET_CODE} -ne 0 ]] && bail "Unable to commit results due to make clean"

  echo "make M=1 bootstrap ${PROD_STR} CAS_TARGET_HW=${CAS_TARGET_HW}"
  make M=1 bootstrap ${PROD_STR} CAS_TARGET_HW="${CAS_TARGET_HW}"
  [[ $? -ne 0 ]] && bail "Unable to commit results due to make bootstrap"
}

replace_skeleton() {
  echo "Replace skeletons"
  local project=${1?Project name is required}
  echo "project: ${project}"
  local branch=${2?Branch is required}
  echo "branch: ${branch}"
  local source_path=${3?Skeleton source path is required}
  echo "source_path: ${source_path}"
  local destination_path=${4?Destination path is required}
  echo "destination_path: ${destination_path}"
  local tmp_dir=$(mktemp -d)
  git clone --branch ${branch} --depth 1 buic-scm:${project} --single-branch ${tmp_dir}
  cp ${tmp_dir}/${source_path} ${destination_path}
  RET_CODE=$((RET_CODE + $?))
  [[ "${RET_CODE}" -ne 0 ]] && bail "Failed to copy ${source_path}"
  rm -rf ${tmp_dir}
}

workarounds() {
  # replacing secureboot_sign_image function to use presigned binaries.
  CREATE_IMAGE_PATTERN='secureboot_sign_image ${page_sz} ${page_sz_B} ${leb_sz_B}'
  REPLACE_PATTERN='[ -f ${bld_top_dir}\/conti-signed-images.tar.gz ] \&\& tar -xzf ${bld_top_dir}\/conti-signed-images.tar.gz -C ${imgdir}\/${sz}\
  ${bld_script_dir}/secboot-image-sign sign ${page_sz} ${page_sz_B} ${leb_sz_B} "debugpolicy" ${OTC_USER_PARAM} ${OTC_PASS_PARAM} ${OTC_KEY_PARAM}'
  CREATE_IMAGE_RELATIVE="${BUILD_DIR}/scripts/create-image"
  echo "> sed --in-place 's%${CREATE_IMAGE_PATTERN}%${REPLACE_PATTERN}%' ${CREATE_IMAGE_RELATIVE}"
  sed --in-place "s%${CREATE_IMAGE_PATTERN}%${REPLACE_PATTERN}%" "${CREATE_IMAGE_RELATIVE}"
  RET_CODE=$((RET_CODE + $?))

  echo "> Remove following strings from ${CREATE_IMAGE_RELATIVE}"

  sed --quiet '/print-package/p' "${CREATE_IMAGE_RELATIVE}"
  echo "> sed --in-place '/print-package/d' ${CREATE_IMAGE_RELATIVE}"
  sed --in-place '/print-package/d' "${CREATE_IMAGE_RELATIVE}"
  RET_CODE=$((RET_CODE + $?))

  sed --quiet '/python ${bld_top_dir}\/tools\/platform\/mcfg_versions_list.py.*/p' "${CREATE_IMAGE_RELATIVE}"
  sed  --in-place 's/python ${bld_top_dir}\/tools\/platform\/mcfg_versions_list.py.*/echo "No new xqcn_mcfg_versions.txt will be generated"/' "${CREATE_IMAGE_RELATIVE}"
  RET_CODE=$((RET_CODE + $?))
  [[ "${RET_CODE}" -ne 0 ]] && bail "Unable to replace substrings in create_image script"

  replace_skeleton "p1/project/otp/main" "conmod-sa515m-3.y" "sa515m/scripts/conti_sign_adapter_skeleton.py" ".build/scripts/conti_sign_adapter.py"
  replace_skeleton "p1/project/vivace/build" "conmod-sa515m-3.y" "scripts/secboot-image-sign-skeleton" "tools/build/scripts/secboot-image-sign"
}

copy_images() {
    header3 "replacing package-info.txt file"
    # package-info.txt file generated through the sdk-constructor pipeline has some lacks
    # due the environment used for generate this.
    if [[ -f "${PACKAGE_INFO_FILE}" ]]; then
       echo "> replacing package-info.txt file"
       echo "cp ${PACKAGE_INFO_FILE} ${SDK_WORKSPACE}/release/docs/"
       cp "${PACKAGE_INFO_FILE}" "${SDK_WORKSPACE}/release/docs/"
    else
       echo "${PACKAGE_INFO_FILE} not found for replacement"
    fi

    # .build/env- files need to be sanitized to avoid including paths
    # from the builder machine. This must be done after generating images
    header3 "Updating env-buildsys-static"
    echo "Overwriting ${ENV_BUILDSYS_FILE}"
    [[ ! -f "${ENV_BUILDSYS_FILE}" ]] && bail "Unable to locate ${ENV_BUILDSYS_FILE}"
    while read var; do
        var_name=$(echo "${var}" | awk -F '[ =]' '{print $2}')
        [[ ! -z "${var_name}" ]] && sed -i "s@.*$var_name=.*@$var@" "${ENV_BUILDSYS_FILE}"
    done <$ENV_OVERWRITE_FILE

    header3 "Updating env-common"
    echo "Overwriting ${ENV_COMMON_FILE}"
    [[ ! -f ${ENV_COMMON_FILE} ]] && bail "Unable to locate ${ENV_COMMON_FILE}"
    sed -i "s@.*CAS_WORKDIR=.*@@" "${ENV_COMMON_FILE}"

    # copying xqcn_mcfg_versions.txt
    #if [[ -e "xqcn_mcfg_versions.txt" ]]; then
    #    header3 "copying xqcn_mcfg_versions.txt file"
    #    copy_to_sdk "xqcn_mcfg_versions.txt" "."
    #    [[ $? -ne 0 ]] && bail "Unable to copy xqcn_mcfg_versions.txt file"
    #fi
}

main() {
  process_cli_parameters "$@"
  common_sdk_init

  local SDKC_WORKSPACE="${WORKSPACE}/sdkc"
  local SDK_DIR="sdk"
  local SDKC_OUTPUT_FILE="sdk-constructor.tar.gz"

  echo "> mkdir -p ${SDKC_WORKSPACE}"
  mkdir -p "${SDKC_WORKSPACE}"
  [[ $? -ne 0 ]] && bail "Failed to create workspace for sdk-constructor"
  pushd "${SDKC_WORKSPACE}" > /dev/null
    init_workarea
    workarounds
    copy_from_build "xqcn_mcfg_versions.txt" "${SDKC_WORKSPACE}/"

    copy_images
    ${WORKSPACE}/.launchers/conmod-cm/sdk/create-package.sh "${WORKSPACE}" "${RELEASE_ID}"

    copy_to_sdk "${SDKC_WORKSPACE}/${SDKC_OUTPUT_FILE}" "${SDK_DIR}"

  popd
}

main "$@"
