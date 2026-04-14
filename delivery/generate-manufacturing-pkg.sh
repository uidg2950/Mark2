#!/bin/bash
# ***************************************************************************************
# *   Copyright (c) 2023-2024 Continental Automotive Systems, Inc., all rights reserved
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: generate-manufacturing-pkg.sh
# *
# *   Description: Script responsible for generating manufacturing-pkg
# *
# ***************************************************************************************


help_info() {
    cat << HELP
./$(basename "$0") --workspace /path/to/workspace --baseline conmod-sa515m-3.3.217.0 [--release_id conmod-sa515m-3.y] [--suffix O342_CHINA]
Script for population of sdk.

Options:
    -h|--help                   Display this information.
    -w|--workspace              Workspace directory.
    -b|--baseline               Baseline version.
    -r|--release_id             Release id.
    -s|--suffix                 Additional suffix for naming image
HELP
}

RELEASE_ID="conmod-sa515m-3.y"

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
            -w|--workspace)
                WORKSPACE="$1"
                shift
                ;;
            -b|--baseline)                       # conmod-sa515m-3.3.217.0
                BASELINE_VERSION="$1"
                shift
                ;;
            -r|--release_id)                     # conmod-sa515m-3.y
                RELEASE_ID="$1"
                shift
                ;;
            -e|--eso_source)                     # conmod-sa515m-3.y
                ESO_SOURCE_BUNDLE="$1"
                shift
                ;;
            -s|--suffix)
               BUILD_SUFFIX="$1"
               shift
               ;;
            *)
                bail "Invalid parameter: $param.\nUse -h|--help for more information."
                ;;
        esac
    done
}

main() {
    process_cli_parameters "$@"

    source "${WORKSPACE}/.launchers/conmod-cm/utils/platform-common.lib"
    source "${WORKSPACE}/.launchers/conmod-cm/utils/artifactory.lib"

    local manufacturing_package_dir="/u01/app/jenkins/documents/sdk_packages/${BASELINE_VERSION}-manufacturing"
    if [[ ! -z ${BUILD_SUFFIX} ]]
    then
      manufacturing_package_dir="/u01/app/jenkins/documents/sdk_packages/${BASELINE_VERSION}-${BUILD_SUFFIX}-manufacturing"
    fi
    local pkg_dir="tp_sdk_${RELEASE_ID}_pkg"
    local release_subpath="${pkg_dir}/release/images/devel/4K"
    local eso_unpacked="${WORKSPACE}/unpacked_eso"
    local release_pkg="${BASELINE_VERSION}-manufacturing-pkg.zip"

    mkdir -p "${eso_unpacked}"
    local eso_pkg=$(find ${WORKSPACE} -maxdepth 1 -type f ! -name '*external*')
    unzip "${eso_pkg}" -d ${eso_unpacked}
    mkdir -p ${WORKSPACE}/conti/unzipped/${pkg_dir}/release/images/devel
    mkdir -p ${WORKSPACE}/conti/unzipped/${pkg_dir}/release/docs
    mkdir -p ${WORKSPACE}/conti/sdk
    local sdk_bundle_zip=$(find ${WORKSPACE}/conti -maxdepth 1 -type f -name '*.zip')

    unzip ${sdk_bundle_zip} -d ${WORKSPACE}/conti/sdk
    cp -ra ${WORKSPACE}/conti/sdk/${pkg_dir}/release/docs/* ${WORKSPACE}/conti/unzipped/${pkg_dir}/release/docs
    cp ${WORKSPACE}/conti/sdk/${pkg_dir}/sdk/otc-signed.txt ${WORKSPACE}/conti/unzipped/${pkg_dir}/release/docs/

    local sw_versions="${WORKSPACE}/conti/unzipped/${pkg_dir}/release/docs/Manufacturing-SW-versions.txt"
    touch  ${sw_versions}
    echo -e "BASELINE_VERSION: ${BASELINE_VERSION}\n" >> "${sw_versions}"
    echo -e "RELEASE_ID: ${RELEASE_ID}\n" >> "${sw_versions}"
    echo -e "ESO_SOURCE_BUNDLE: ${ESO_SOURCE_BUNDLE}\n" >> "${sw_versions}"

    local toolchain_zip="tp_toolchain_${BASELINE_VERSION}_pkg.zip"
    echo "> download_artifacts '${WORKSPACE}/conti' '${RELEASE_ID}' '${BASELINE_VERSION}' '${toolchain_zip}'"
    download_artifacts "${WORKSPACE}/conti" "${RELEASE_ID}" "${BASELINE_VERSION}" "${toolchain_zip}"
    
    unzip "${WORKSPACE}/conti/${toolchain_zip}" -d "${WORKSPACE}/conti"

    local install_folder="${WORKSPACE}/conti/install"
    SDK_ARTIFACTS=( "sdk/${pkg_dir}/sdk/sdk-constructor.tar.gz" "sdk/${pkg_dir}/sdk/sdk.tar.gz" "otp-host.tar.gz" "toolchain.tar.gz" )
    SDK_ARTIFACTS_PATHS=( "${install_folder}" "${install_folder}/release/fs/devel" "${install_folder}/release-host/fs/host" "${install_folder}/release-toolchain/fs/devel" )
    SDK_ARTIFACTS_COUNT=${#SDK_ARTIFACTS[@]}

    echo "Installing tar files"
    for (( c=0; c<SDK_ARTIFACTS_COUNT; c++ )); do
       local item_path="${WORKSPACE}/conti/${SDK_ARTIFACTS[${c}]}"

       [[ ! -d ${SDK_ARTIFACTS_PATHS[${c}]} ]] && echo "Unable to locate ${SDK_ARTIFACTS_PATHS[${c}]}. Creating it." && mkdir -p "${SDK_ARTIFACTS_PATHS[${c}]}"
       [[ ! -f ${item_path} ]]  && echo "Unable to find ${item_path}" && exit 1
       echo "tar -zxf "${item_path}" -C ${SDK_ARTIFACTS_PATHS[${c}]}"
       tar -zxf "${item_path}" -C ${SDK_ARTIFACTS_PATHS[${c}]}
       RET_CODE=$((RET_CODE + $?))
       [ ${RET_CODE} -ne 0 ] && bail "Unable to unpacking ${SDK_ARTIFACTS[${c}]}"
    done

    header2 "Generating images"
    echo "> bash ${WORKSPACE}/.launchers/linux/sdk/install-prodfs-sdk --workspace ${install_folder} --image_size 4K --signed_images ${WORKSPACE}/conti/sdk/${SDK_BUNDLE_DIR}/sdk/conti-signed-images.tar.gz"
    bash ${install_folder}/.launchers/linux/sdk/install-prodfs-sdk --workspace "${install_folder}" --image_size 4K --signed_images ${WORKSPACE}/conti/sdk/${pkg_dir}/sdk/conti-signed-images.tar.gz
    RET_CODE=$((RET_CODE + $?))
    [[ ${RET_CODE} -ne 0 ]] && bail "Unable to generate images"

    echo "> mkdir -p ${WORKSPACE}/conti/unzipped/${release_subpath}"
    mkdir -p "${WORKSPACE}/conti/unzipped/${release_subpath}"
    echo"> rsync --stats -v --checksum --archive ${install_folder}/release/images/devel/4K/ ${WORKSPACE}/conti/unzipped/${release_subpath}"
    rsync --stats -v --checksum --archive "${install_folder}/release/images/devel/4K/" "${WORKSPACE}/conti/unzipped/${release_subpath}"
    
    echo "> cp ${WORKSPACE}/unpacked_eso/*/images/system.ubifs ${WORKSPACE}/conti/unzipped/${release_subpath}/"
    cp ${WORKSPACE}/unpacked_eso/*/images/system.ubifs ${WORKSPACE}/conti/unzipped/${release_subpath}/
    echo "> cp ${WORKSPACE}/unpacked_eso/*/images/system.ubifs.sig ${WORKSPACE}/conti/unzipped/${release_subpath}/"
    cp ${WORKSPACE}/unpacked_eso/*/images/system.ubifs.sig ${WORKSPACE}/conti/unzipped/${release_subpath}/
    echo "> cp ${WORKSPACE}/unpacked_eso/*/images/ubi.img ${WORKSPACE}/conti/unzipped/${release_subpath}/"
    cp ${WORKSPACE}/unpacked_eso/*/images/ubi.img ${WORKSPACE}/conti/unzipped/${release_subpath}/
    echo "> mv ${WORKSPACE}/conti/unzipped/${release_subpath}/sbl1.mbn ${WORKSPACE}/conti/unzipped/${release_subpath}/sbl1-qcom.mbn"
    mv ${WORKSPACE}/conti/unzipped/${release_subpath}/sbl1.mbn ${WORKSPACE}/conti/unzipped/${release_subpath}/sbl1-qcom.mbn
    echo "> cp ${WORKSPACE}/conti/unzipped/${release_subpath}/sbl1-audi-conmod.mbn ${WORKSPACE}/conti/unzipped/${release_subpath}/sbl1.mbn"
    cp ${WORKSPACE}/conti/unzipped/${release_subpath}/sbl1-audi-conmod.mbn ${WORKSPACE}/conti/unzipped/${release_subpath}/sbl1.mbn

    header2 "Generating images"
    local XQCN_PROJECT="p1/project/otp/xqcn"
    local XQCN_WORKSPACE="${WORKSPACE}/xqcn"

    echo "> git clone buic-scm:${XQCN_PROJECT} --branch ${BASELINE_VERSION} --depth 1  --single-branch ${XQCN_WORKSPACE}"
    git clone buic-scm:"${XQCN_PROJECT}" --branch "${BASELINE_VERSION}" --depth 1  --single-branch "${XQCN_WORKSPACE}"

    echo "> copy_xqcn_files ${WORKSPACE}/conti/unzipped/${pkg_dir}/release ${XQCN_WORKSPACE}"
    copy_xqcn_files "${WORKSPACE}/conti/unzipped/${pkg_dir}/release" "${XQCN_WORKSPACE}"

    header2 "PERFORM VALIDATIONS"

    header2 "QCN CHECK"
    echo "> python3 ${WORKSPACE}/.launchers/conmod-cm/delivery/check_qcn_files.py --path ${WORKSPACE}/conti/unzipped/${pkg_dir}/release/images/devel/4K"
    python3 ${WORKSPACE}/.launchers/conmod-cm/delivery/check_qcn_files.py --path ${WORKSPACE}/conti/unzipped/${pkg_dir}/release/images/devel/4K
    echo "> rm 'xqcn_mcfg_versions.txt'"
    rm "${WORKSPACE}/conti/unzipped/${pkg_dir}/xqcn_mcfg_versions.txt"

    RET_CODE=$((RET_CODE + $?))
    [[ ${RET_CODE} -ne 0 ]] && bail "Failed to validate qcn"

    header2 "IVD CHECK"
    echo "> python3 ${WORKSPACE}/.launchers/conmod-cm/delivery/validate_ivd.py --workspace ${WORKSPACE} --baseline ${BASELINE_VERSION} --release_id ${RELEASE_ID}"
    python3 ${WORKSPACE}/.launchers/conmod-cm/delivery/validate_ivd.py --workspace "${WORKSPACE}" --baseline "${BASELINE_VERSION}" --release_id "${RELEASE_ID}"

    RET_CODE=$((RET_CODE + $?))
    [[ ${RET_CODE} -ne 0 ]] && bail "Failed to validate IVD"
    
    echo "> cp ${WORKSPACE}/IVD_Report.txt ${WORKSPACE}/conti/unzipped/${pkg_dir}/release/docs/"
    cp ${WORKSPACE}/IVD_Report.txt ${WORKSPACE}/conti/unzipped/${pkg_dir}/release/docs/
    RET_CODE=$((RET_CODE + $?))
    [[ ${RET_CODE} -ne 0 ]] && bail "Failed to copy IVD report"

    local MNFCT_ARTIFACTS=( "modem_elf.tar.gz" "modem_qshrink.tar.gz" "" "otp_versions.txt" "qcom-bsp.tar.gz" "vmlinux.tar.gz")
    local MNFCT_COUNT=${#MNFCT_ARTIFACTS[@]}
    for (( c=0; c<MNFCT_COUNT; c++ )); do
        echo "> download_artifacts '${WORKSPACE}/conti/unzipped' '${RELEASE_ID}' '${BASELINE_VERSION}' '${MNFCT_ARTIFACTS[${c}]}'"
        download_artifacts "${WORKSPACE}/conti/unzipped" "${RELEASE_ID}" "${BASELINE_VERSION}" "${MNFCT_ARTIFACTS[${c}]}"
    done

    rm -rf ${manufacturing_package_dir}/${release_subpath}
    mkdir -p ${manufacturing_package_dir}/${release_subpath}

    pushd ${WORKSPACE}/conti/unzipped
        zip --filesync --recurse-paths "${WORKSPACE}/conti/${release_pkg}" "${pkg_dir}"
    popd
}

main "$@"

