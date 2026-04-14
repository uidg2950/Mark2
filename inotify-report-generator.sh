#!/bin/bash
# ******************************************************************************
# *   Copyright (c) 2023-2025 Aumovio, Inc., all rights reserved
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: inotify-report-generator.sh
# *
# *   Description: This script will generate reports based on the output from
# *                inotify tool.
# *
# ******************************************************************************
SCRIPT_NAME=$(basename "${0}")
LOGFILE=$(dirname $0)/"${SCRIPT_NAME%.*}.log"
echo "LOGGING to ${LOGFILE}"
exec > >(tee "${LOGFILE}");

# ----------------------------------------------------------- #
# All output from commands in this block sent to file $LOGFILE.
echo "START: ${SCRIPT_NAME} $(date)"

## Script Parameters
WORKSPACE=${1?workspaces is required}
BASELINE_NAME=${2?baseline_name is required}
FLAVOR=${3?flavor is required}
PACKAGES=${4?packages is required}

## Script variables
packages_target_file="${WORKSPACE}/.build/packages-target"
IFS=' ' read -r -a packages_target <<< "$(cat ${packages_target_file})"
inotify_reports="${WORKSPACE}/inotify_report_${BASELINE_NAME}"
# shared drive variables
RGB_SHARED_DRIVE="//automotive-wan.com/root/smt/did01665/ConMod/18_Software_builds_AudiConMod"
MOUNTING_DIR="${WORKSPACE}/conmod_shared_drive"
FOSS_REPORT_STAGING_DIR="${MOUNTING_DIR}/FOSS_reports"
# state variable
RET_CODE=0

PROD_STR=''
[[ "${FLAVOR}" == "prod" ]] && PROD_STR='P=1'
[[ "${FLAVOR}" == "devel" ]] && PROD_STR='P=0'

# packages to be excluded
distclean_packages=( conti-fc-nav-hal-sepolicy conti-tp-hal-sepolicy libtool libxml-parser-perl )
packages_path=()
packages_analyzed=()

## Import external libraries
echo "Import external libraries"
source "${WORKSPACE}/.launchers/conmod-cm/utils/platform-common.lib"

echo "##################################################################"
echo "                               DETAILS"
echo
echo
echo "WORKSPACE:            ${WORKSPACE}"
echo "BASELINE_NAME:        ${BASELINE_NAME}"
echo "FLAVOR:               ${FLAVOR}"
echo "PROD_STR:             ${PROD_STR}"
echo
echo

## File verification
[[ ! -f "${packages_target_file}" ]] && bail "${packages_target_file} doesn't exist"

## Listing Target packages in packages-target file
for pckg in ${packages_target[@]}; do
    y=$(echo ${pckg}| awk -v FS='--' '{print $1}')
    packages_path+=( "${y}" )
done

# For Labels
case "${PACKAGES}" in
    opensource)
        label_packages="Opensource"
        ;;
    conti)
        label_packages="Continental"
        ;;
    qcom)
        label_packages="Qualcomm"
        ;;
    caf)
        label_packages="Codeaurora"
esac

## Count of Packages & Paths
t_elements=${#packages_target[@]}
p_elements=${#packages_path[@]}
[[ ${t_elements} -ne ${p_elements} ]] && bail "List of packages is corrupted!"

## inotify logs folder
if [[ -d "${inotify_reports}" ]]; then
    rm -rf "${inotify_reports}"/*
else
    mkdir -p "${inotify_reports}"
fi

header1 "inotify execution for ${label_packages} packages"
## inotify execution
for (( i=0;i<$t_elements;i++ )); do
    if [[ ! "${distclean_packages[*]}" =~ "${packages_target[i]}" ]]; then
        # Path construction
        if [[ "${packages_target[i]}" =~ conti ]]; then
            path_monitor=${WORKSPACE}/package/conti/${packages_path[i]}
        elif [[ "${packages_target[i]}" =~ caf ]]; then
            path_monitor=${WORKSPACE}/package/codeaurora/${packages_path[i]}
        elif [[ "${packages_target[i]}" =~ qcom ]]; then
            path_monitor=${WORKSPACE}/package/qualcomm/${packages_path[i]}
        else
            if [[ "${packages_target[i]}" =~ sme ]]; then
                path_monitor=${WORKSPACE}/package/conti/${packages_path[i]}
            else
                path_monitor=${WORKSPACE}/package/opensource/${packages_path[i]}
            fi
        fi

        # Path verification
        if [[ ${path_monitor} =~ ${PACKAGES} ]]; then
		    if [[ -d "${path_monitor}" ]]; then
		        header4 "Package: ${packages_target[i]}"
                packages_analyzed+=( "${packages_target[i]}" )
                # main command
                inotifywait -r "${path_monitor}" -m -e open > "${inotify_reports}/${packages_target[i]}_log.txt" &
                make "${packages_target[i]}" ${PROD_STR} J=1   # J -> Number of allowed Jobs in Parallel
                killall inotifywait
            else
                echo "WARNING: ${path_monitor} not found"
            fi
        fi
    fi
done

## Resume of packages analyzed

header1 "Resume of packages analyzed"
echo "${packages_analyzed[@]}"
echo

header1 "staging reports into wetzlar shared drive"

# Creating folder for mount wetzlar shared drive
echo "> Creating folder for mount wetzlar shared drive"
echo "> mkdir -p ${MOUNTING_DIR}"
mkdir -p ${MOUNTING_DIR}
RET_CODE=$((RET_CODE + $?))
[[ ${RET_CODE} -ne 0 ]] && bail "Mounting folder creation failed"

header2 "Mounting wetzlar shared drive"
# FIXME: This is a temporary solution for save official conmod baselines
echo "mount.cifs -o credentials=/home/uidg4627/.credentials/dpfil02,uid=uidg4627,gid=uidg4627 ${RGB_SHARED_DRIVE} ${MOUNTING_DIR}"
sudo mount.cifs -o credentials=/home/uidg4627/.credentials/dpfil02,uid=uidg4627,gid=uidg4627 "${RGB_SHARED_DRIVE}" "${MOUNTING_DIR}"
RET_CODE=$((RET_CODE + $?))
[[ ${RET_CODE} -ne 0 ]] && bail "Mounting ${RGB_SHARED_DRIVE} drive failed"

header2 "Storing Reports"
pushd "${FOSS_REPORT_STAGING_DIR}" &> /dev/null
    # copying reports
    echo "cp -Rv ${inotify_reports} ${FOSS_REPORT_STAGING_DIR}"
    cp -Rv "${inotify_reports}" "${FOSS_REPORT_STAGING_DIR}"
    RET_CODE=$((RET_CODE + $?))
    [[ ${RET_CODE} -ne 0 ]] && bail "Failed copying reports into ${FOSS_REPORT_STAGING_DIR} folder"

popd &> /dev/null

header2 "Unmount wetzlar shared drive"
sudo umount "${MOUNTING_DIR}"
RET_CODE=$((RET_CODE + $?))
[[ ${RET_CODE} -ne 0 ]] && echo "WARNING: unable to unmount shared drive, please verify the host machine"

echo "# ----------------------------------------------------------- #"
echo "END: $(basename $0) [${RET_CODE}]: $(date)"
# ----------------------------------------------------------- #
