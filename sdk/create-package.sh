#!/bin/bash
# ******************************************************************************
# *   Copyright (c) 2018-2021 Continental Automotive Systems, Inc., all rights reserved
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: create-package.sh
# *
# *   Description: Creates sdk.tar.gz file from existent build workspace.
# *      Features: +Compress configuration is given by 'file-list-sdkc' file,
# *                 which defines: files and dirs to compress, and dir priorities for searching.
# ******************************************************************************
SCRIPT_NAME=$(basename "${0}")
LOGFILE="$(dirname "${0}")/${SCRIPT_NAME/\.*/.log}"
echo "LOGGING to ${LOGFILE}"
exec > >(tee "${LOGFILE}");

#----------------------------------------------------------- #
#All output from commands in this block sent to file $LOGFILE.
echo "START: ${SCRIPT_NAME} $(date)"

# Command line parameters
export WORKSPACE=${1}
export RELEASE_ID=${2}

echo "Import external libraries"
source "${WORKSPACE}/.launchers/conmod-cm/utils/platform-common.lib"

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    bail "Illegal number of parameters: $#"
fi

#Default values
RET_CODE=0
count=0

#Script variables
SDKC_OUTPUT_FILE="sdk-constructor.tar"
RELEASE_DIR="${WORKSPACE}/release"
FILE_LIST="${WORKSPACE}/.launchers/conmod-cm/sdk/sdkc/file-list-sdkc"
BUILD_DIR="${WORKSPACE}/sdkc/.build"

#Handle exit codes to always promote variables
function on_exit {
    echo "Trapping on exit code: $?"
    echo "END: ${SCRIPT_NAME} [${RET_CODE}]: $(date)"
}
trap on_exit EXIT

header1 "DETAILS"
echo "WORKSPACE:     ${WORKSPACE}"

function _find(){
    path_name=${1?path_name is mandatory}
    file_name=${2?file_name is mandatory}
    search_symlinks=$3
    # Search as a Symlink
    if [ -n "${search_symlinks}" ]; then
        search_type="-xtype l"
        options="-L"
    fi

    # if "options" is empty, find will execute a regular search without follow symlinks.
    echo $(find $options "${path_name}" ${search_type:--type f} \
    -not \( -path "./release-toolchain/*" -prune \) \
    -not \( -path "./release-host/*" -prune \) \
    -not \( -path ".build/prodfs/*" -prune \) \
    -not \( -path ".git/*" -prune \) \
    -name "${file_name}" -print -quit 2>/dev/null)
}

header1 "BUILD AREA"
pushd "${WORKSPACE}/sdkc" &>/dev/null

header1 "A new sdk constructor tar will be created"
header3 "Importing ${FILE_LIST}"
[ ! -f "${FILE_LIST}" ] && bail "Unable to locate ${FILE_LIST}"
source "${FILE_LIST}"

header2 "Compressing files"
header3 "Adding empty dirs"
tar cvf "${SDKC_OUTPUT_FILE}" --files-from /dev/null
counter=0
for dir_name in "${dir_list_sdkc[@]}" ;do
    if [[ -n "${dir_name}" ]]; then
        tar rfv "${SDKC_OUTPUT_FILE}" --exclude="${dir_name?}"/* ./"${dir_name}"
        counter=$((counter + 1))
    fi
done
RET_CODE=$((RET_CODE + $?))
[ ${RET_CODE} -ne 0 ] && bail "Failed to add empty directories to ${SDKC_OUTPUT_FILE}"
echo "Number of created dirs: ${counter}"

header3 "Move of install-prodfs-sdk"
mkdir -p "${WORKSPACE}/.launchers/linux/sdk"
mv ${WORKSPACE}/.launchers/conmod-cm/sdk/sdkc/* "${WORKSPACE}/.launchers/linux/sdk"

header3 "Compressing files listed in ${FILE_LIST}"
counter=0
for file_name in "${file_list_sdkc[@]}" ;do
    file_path=""

    # Search with priority
    for dir_name in "${dir_list_search_priorities[@]}" ;do

        # If the filename contains a directory attach it to the dir_name
        if [[ $(dirname "${file_name}") == "." ]]; then
            basename="${file_name}"
        else
            dir_name="${dir_name}/$(dirname "${file_name}")"
            basename=$(basename "${file_name}")
        fi

        # Search as regular file
        for option in "" "search_symlinks"; do
            file_path=$(_find "${dir_name}" "${basename}" "${option}")
            if [[ -f "${file_path}" ]]; then
                tar rvf "${SDKC_OUTPUT_FILE}" "${file_path}"
                RET_CODE=$((RET_CODE + $?))

                counter=$((counter + 1))
                break 2
            fi
        done
    done

    if [[ -z "${file_path}" ]]; then
        echo "Unable to locate '${file_name}'"
    fi
done
[[ ${RET_CODE} -ne 0 ]] && bail "Failed to compress ${FILE_LIST}"
echo "Number of found files:${counter}"

# Dirs for Signing Capabilities
if [[ ${RELEASE_ID} =~ sa515m ]];then
    echo "> Appendings for signing capabilities"
    for for_signature_dir in "${dirs_for_signature_sdkc[@]}"; do
        if [[ -d "${for_signature_dir}" ]]; then
            tar rvf "${SDKC_OUTPUT_FILE}" "${for_signature_dir}"
        else
            echo "> ${for_signature_dir} skipped, this is not present."
        fi
    done
    [[ ${RET_CODE} -ne 0 ]] && bail "Failed to append files for signing"
fi

# Compressing tar -> tar.gz
echo "Compressing ${SDKC_OUTPUT_FILE} file"
gzip "${SDKC_OUTPUT_FILE}"
RET_CODE=$((RET_CODE + $?))
[ ${RET_CODE} -ne 0 ] && bail "Something went wrong compressing ${SDKC_OUTPUT_FILE} into .gz"

popd

echo "END: ${SCRIPT_NAME} [${RET_CODE}]: $(date)"
# ----------------------------------------------------------- #
