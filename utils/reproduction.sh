#!/bin/bash
# ******************************************************************************
# *   Copyright (c) 2023 Continental Automotive Systems, Inc., all rights reserved
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: reproduction.sh
# *
# *   Description: Checks out conmod-cm repo to an older version for reproduction builds
# *
# ******************************************************************************

while [ $# -gt 0 ]; do
        param="$1"
        shift
        case $param in
            -w|--workspace)
                WORKSPACE="$1"
                shift
                ;;

            -b|--baseline)
                BASELINE_VERSION="$1"
                shift
                ;;

            *)
                bail "Invalid parameter: $param.\nUse -h|--help for more information."
                ;;
        esac
    done

RET_CODE=0

pushd "${WORKSPACE}/.launchers/conmod-cm" &>/dev/null
    local git_tag=$(git tag -l "${BASELINE_VERSION}*")
    if [[ ${git_tag[*]} =~ "${BASELINE_VERSION}" ]]; then
        echo "git checkout ${BASELINE_VERSION}"
        $(git checkout "${BASELINE_VERSION}")
        RET_CODE=$((RET_CODE + $?))
    elif [[ ${git_tag[*]} =~ "REL" ]]; then
        echo "git checkout ${BASELINE_VERSION}-REL"
        $(git checkout "${BASELINE_VERSION}-REL")
        RET_CODE=$((RET_CODE + $?))
    elif [[ ${git_tag[*]} =~ "PRE" ]]; then
        echo "git checkout ${BASELINE_VERSION}-PRE"
        $(git checkout "${BASELINE_VERSION}-PRE")
        RET_CODE=$((RET_CODE + $?))
    elif [[ ${git_tag[*]} =~ "ENG" ]]; then
        echo "git checkout ${BASELINE_VERSION}-ENG"
        $(git checkout "${BASELINE_VERSION}-ENG")
        RET_CODE=$((RET_CODE + $?))
    else
        echo "No existing Release found"
    fi

    [[ ${RET_CODE} -ne 0 ]] && echo "Warning: failed to checkout git tag"

popd &>/dev/null
