#!/bin/bash
# ***************************************************************************************
# *   Copyright (c) 2022 Continental Automotive Systems, Inc., all rights reserved
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: validate_jsons.sh
# *
# *   Description: Script responsible for validation of json files (delivery.json & target.json)
# *
# ***************************************************************************************

source "${WORKSPACE}/.launchers/conmod-cm/sdk/sdk-common.inc"
source "${WORKSPACE}/.launchers/conmod-cm/utils/artifactory.lib"

main() {
    process_cli_parameters "$@"

    local target_file="target.json"
    local delivery_file="delivery.json"

    pushd "${WORKSPACE}" > /dev/null
        get_metainfo ${RELEASE_ID} ${BASELINE_VERSION} ${target_file}
        local artifactory_target_checksum=$(echo "${artifactory_metadata}" | python3 -c "import sys, json; print(json.load(sys.stdin)['checksums']['sha256'])")
        get_metainfo ${RELEASE_ID} ${BASELINE_VERSION} ${delivery_file}
        local artifactory_delivery_checksum=$(echo "${artifactory_metadata}" | python3 -c "import sys, json; print(json.load(sys.stdin)['checksums']['sha256'])")

        download_artifacts ${WORKSPACE} ${RELEASE_ID} ${BASELINE_VERSION} ${target_file}
        download_artifacts ${WORKSPACE} ${RELEASE_ID} ${BASELINE_VERSION} ${delivery_file}
        local local_target_checksum=($(sha256sum ${WORKSPACE}/${target_file}))
        local local_delivery_checksum=($(sha256sum ${WORKSPACE}/${delivery_file}))

        if [ "${artifactory_target_checksum}" = "${target_file}" ]; then
            echo "Download of ${target_file} successful!"
        fi

        if [ "${artifactory_delivery_checksum}" = "${local_delivery_checksum}" ]; then
            echo "Download of ${delivery_file} successful!"
        fi

        python3 ${WORKSPACE}/.launchers/conmod-cm/verify/target_verification.py ${WORKSPACE} ${RELEASE_ID} ${BASELINE_VERSION}

    popd

}

main "$@"
