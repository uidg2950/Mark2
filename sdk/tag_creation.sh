#!/bin/bash
# ******************************************************************************
# *   Copyright (c) 2022 Continental Automotive Systems, Inc., all rights reserved
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: tag_creation.sh
# *
# *   Description: Creates tag for conmod-cm repo.
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

# Include
source "${WORKSPACE}/.launchers/conmod-cm/utils/platform-common.lib"

# Script Parameters
WORKSPACE=${1?workspace is required}
BASELINE_NAME=${2?baseline_name is required}

# Script variables
CONMOD_CM="${WORKSPACE}/.launchers/conmod-cm"
RET_CODE=0

header1 "Creating TAGs for conmod-cm repo"
echo
echo "                               DETAILS"
echo
echo "WORKSPACE:            ${WORKSPACE}"
echo "BASELINE_NAME:        ${BASELINE_NAME}"
echo

pushd "${CONMOD_CM}" &>/dev/null
  # Set tag name to Baseline Version
  TAG="${BASELINE_NAME}"
  TAG_VERSION=$(git tag | grep ${TAG} | wc -l)

  # Check if there is already a tag available for the baseline version
  if [[ ${TAG_VERSION} -ge 1 ]]; then
    # Update tag if already available
    # Remove local tag
    echo "> git tag -d ${TAG}"
    git tag -d "${TAG}"
    RET_CODE=$((RET_CODE + $?))
    # Create new local tag
    echo "> git tag ${TAG}"
    git tag "${TAG}"
    RET_CODE=$((RET_CODE + $?))
    # Remove remote tag
    echo "> git push origin :${TAG}"
    git push origin :"${TAG}"
    RET_CODE=$((RET_CODE + $?))
    # Push new tag to remote
    echo "> git push origin ${TAG}"
    git push origin "${TAG}"
    RET_CODE=$((RET_CODE + $?))
    echo "> TAG ${VER} updated!"
  else
    # Create tag if no tag available
    echo "> git tag ${TAG}"
    git tag "${TAG}"
    RET_CODE=$((RET_CODE + $?))
    echo "> git push origin ${TAG}"
    git push origin "${TAG}"
    RET_CODE=$((RET_CODE + $?))
  fi

  [[ ${RET_CODE} -ne 0 ]] && echo "Warning: failed to push git tag"

popd &>/dev/null

echo "END: ${SCRIPT_NAME} [${RET_CODE}]: $(date)"
