#!/bin/bash
# ******************************************************************************
# *   Copyright (c) 2023-2026 Aumovio, Inc., all rights reserved
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: documents_for_release
# *
# *   Description: Copying from WET Sharedrive into Telematics_Platform Sharedrive
# *					- Release Notes
# *					- Test Results
# *
# *
# *                 **** THIS SCRIPT IS A TEMPORARY WORKAROUND FOR CONMOD
# *                      DELIVERIES
# *
# ******************************************************************************
SCRIPT_NAME=$(basename "${0}")
LOGFILE=$(dirname $0)/"${SCRIPT_NAME%.*}.log"
echo "LOGGING to ${LOGFILE}"
exec > >(tee "${LOGFILE}");

# All output from commands in this block sent to file $LOGFILE.
echo "START: ${SCRIPT_NAME} $(date)"

echo "Import external libraries"
source "${WORKSPACE}/.launchers/conmod-cm/utils/platform-common.lib"
source "${WORKSPACE}/.launchers/conmod-cm/utils/cat-common.lib"
source "${WORKSPACE}/.launchers/conmod-cm/utils/artifactory.lib"

# Variables
RBG_DRIVE="did01665"
RBG_SHARED_DRIVE="//automotive-wan.com/root/smt/${RBG_DRIVE}/ConMod/18_Software_builds_AudiConMod"
RET_CODE=0

#Handle exit codes to always promote variables
function on_exit {
    echo "Trapping on exit code: $?"
    echo "Workspace integrity verification"
    RBG_MOUNTED=$(mount | grep ${RBG_DRIVE})
    if [[ -n ${RBG_MOUNTED} ]]; then
        sudo umount "${MOUNTING_DIR}"
        [[ ${RET_CODE} -ne 0 ]] && echo "Unable to unmount Sharedrive. Please verify the host machine"
    fi
    echo "Workspace is safe"
    echo "END: $(basename "$0") [${RET_CODE}]: $(date)"
}
trap on_exit EXIT

main(){

    process_cli_parameters "$@"

    header1 "Looking for Release Documents"
    echo
    echo "                               DETAILS"
    echo
    echo "WORKSPACE:                   ${WORKSPACE}"
    echo "RELEASE_ID:                  ${RELEASE_ID}"
    echo "BASELINE_VERSION:            ${BASELINE_VERSION}"
    echo "DELIVERY_TYPE:               ${DELIVERY_TYPE}"
    echo "RRR_CONFLUENCE_LINK          ${RRR_CONFLUENCE_LINK}"
    echo "TEST_PLAN_ID                 ${TEST_PLAN_ID}"
    echo "WIN_USER                     ${WIN_USER}"
    echo "WIN_PW                       *concealed*"
    echo

    # Mounting folder
    MOUNTING_DIR="${WORKSPACE}/rbg_drive"
    mkdir -p ${MOUNTING_DIR}
    RET_CODE=$((RET_CODE + $?))
    [[ ${RET_CODE} -ne 0 ]] && bail "Mounting folder creation failed"

    # FIXME: This is a temporary solution for save official conmod baselines
    header2 "Mounting RBG shared drive"
    echo "sudo mount.cifs -o credentials=/home/uidg4627/.credentials/dpfil02,uid=uidg4627,gid=uidg4627 ${RBG_SHARED_DRIVE} ${MOUNTING_DIR}"
    sudo mount.cifs -o credentials=/home/uidg4627/.credentials/dpfil02,uid=uidg4627,gid=uidg4627 "${RBG_SHARED_DRIVE}" "${MOUNTING_DIR}"
    RET_CODE=$((RET_CODE + $?))
    [[ ${RET_CODE} -ne 0 ]] && bail "Mounting ${RBG_SHARED_DRIVE} drive failed"

    # Baseline Directory
    BASELINE_DIR="${MOUNTING_DIR}/sdk-releases/${BASELINE_VERSION}"

    # Getting info from artifactory
    get_metainfo ${RELEASE_ID} ${BASELINE_VERSION} ""
    folder_content=$(echo "${artifactory_metadata}" | python3 -c "import sys, json; print(json.load(sys.stdin)['children'])")

    # removing []{}''
    # replacing "," -> ":"
    folder_content=$(echo "${folder_content}" | sed "s/[]{''}[]//g" | sed 's/,/:/g')

    # Split by ":"
    IFS=':' read -ra FILE_LIST <<< ${folder_content}
    FILES=()
    for item in "${FILE_LIST[@]}"; do
        if [[ ${item} =~ \/ ]]; then              # strings that starts with “/”
            FILES+=("${item///}")
        fi
    done

    # METAFILES
    RN_FILE="CONMOD_5_G_"
    TR_FILE="Aumovio_ConMod_NAD_Test_Results_Rel"
    BASE_VERSION=$(echo "${BASELINE_VERSION}" | cut -d"-" -f3-)
    SWC_REL_NOTES_JSON="SWC_Release_Notes_${BASE_VERSION}_Continental.json"   # FIXME:Continental -> Aumovio?
    MODEM_BSW_JSON="Modem_BSW_delivery_manifest_SWC.json"

    # Associative Array
    declare -A rel_json_metafiles=(["${RN_FILE}"]=false ["${TR_FILE}"]=false ["${MODEM_BSW_JSON}"]=false ["${SWC_REL_NOTES_JSON}"]=false)

    # Remove existing release note documents from artifactory
    header2 "Removing existing files from artifactory"
    for doc_regex in "${!rel_json_metafiles[@]}"; do
        for item in "${FILES[@]}"; do
            if [[ "${item}" =~ "${doc_regex}" ]]; then
                echo "> Removing existing file: ${ARTIFACTORY_SERVER}/vni_otp_generic_l/${RELEASE_ID}/${BASELINE_VERSION}/${item}"
                delete_artifact ${WORKSPACE} ${RELEASE_ID} ${BASELINE_VERSION} ${item}
            fi
        done
    done

    if [[ "${DELIVERY_TYPE}" != "Engineering Drop" ]]; then
        # Copy the new release documents from RBG share to Artifactory
        # In case there are no documents on RBG share try to generate them
        if [[ -d "${BASELINE_DIR}" ]]; then
            header2 "Search on RBG share for existing Release documents"
            for doc_regex in "${!rel_json_metafiles[@]}"; do
                DOC_FILE_NAME=$(find "${BASELINE_DIR}" -maxdepth 1 -name "${doc_regex}"* -print | rev | cut -d'/' -f1 | rev)
                if [[ -n "${DOC_FILE_NAME}" ]]; then
                    # Setting "true" flag
                    rel_json_metafiles["${doc_regex}"]=true

                    # Upload to Artifactory
                    echo "> Document found: ${DOC_FILE_NAME}"
                    echo "> Uploading new file: ${ARTIFACTORY_SERVER}/vni_otp_generic_l/${RELEASE_ID}/${BASELINE_VERSION}/${DOC_FILE_NAME}"
                    upload_artifacts ${BASELINE_DIR} ${RELEASE_ID} ${BASELINE_VERSION} ${DOC_FILE_NAME}
                    RET_CODE=$((RET_CODE + $?))
                    [[ ${RET_CODE} -ne 0 ]] && echo "WARNING: Uploading release documents failed"
                fi
            done
        else
            echo "> No Documents available on RBG Share for ${BASELINE_VERSION}"
        fi

        if [[ "${rel_json_metafiles[${RN_FILE}]}" == false ]] || \
           [[ "${rel_json_metafiles[${SWC_REL_NOTES_JSON}]}" == false ]]; then
            # If Release Document CONMOD_5_G_ is not available generate it
            echo "> Release Notes + SWC_Release_Notes not found on RBG share!"
            echo "> Trying to generate Release Notes PDF + SWC_Release_Notes"
            echo ""
            header2 "START - Generate Release Documents"
            sudo -H python3.9 -m pip install -r "${WORKSPACE}"/.launchers/conmod-cm/release_notes_creator/requirements.txt

            python3.9 "${WORKSPACE}"/.launchers/conmod-cm/release_notes_creator/main_documentation_generation.py \
                    --delivery_type "${DELIVERY_TYPE}" --baseline_version "${BASELINE_VERSION}" --release_id "${RELEASE_ID}" \
                    --rrr_confluence_link "${RRR_CONFLUENCE_LINK}" --jazz_test_plan_id "${TEST_PLAN_ID}" --win_uid "${WIN_USER}" \
                    --win_passwd "${WIN_PW}" --output_folder "${WORKSPACE}/output"

            header2 "END - Generate Release Documents"

            # Create a blank-separated file list of release note pdf and json for upload
            FILES=()
            if [[ "${rel_json_metafiles[${RN_FILE}]}" == false ]]; then
                generated_release_document=(`ls ${WORKSPACE}/output/*.pdf`)
                generated_release_document=${generated_release_document##*/}
                FILES+=("${generated_release_document}")
            fi

            # add json file if present
            if [[ "${rel_json_metafiles[${SWC_REL_NOTES_JSON}]}" == false ]]; then
                generated_release_json=(`ls ${WORKSPACE}/output/*.json`)
                generated_release_json=${generated_release_json##*/}
                # add json file with preceding blank so it is a list
                FILES+=("${generated_release_json}")
            fi

            # Upload to Artifactory
            header2 "Uploading Generated Files"
            upload_artifacts "${WORKSPACE}/output" "${RELEASE_ID}" "${BASELINE_VERSION}" "${FILES[*]}"
        fi

        if [[ "${rel_json_metafiles[${MODEM_BSW_JSON}]}" == false ]]; then
            # If Release Document Modem_BSW_delivery_manifest_SWC.json is not available generate it
            echo "> Modem_BSW_delivery_manifest_SWC.json not found on RBG share!"
            echo "> Trying to generate Modem_BSW_delivery_manifest_SWC.json"
            python3 "${WORKSPACE}"/.launchers/conmod-cm/metafiles/modem_bsw_delivery.py "${WORKSPACE}" "${RELEASE_ID}" "${BASELINE_VERSION}"
        fi
    fi

    # Unmount Sharedrive
    header2 "Unmount RBG Sharedrive"
    sudo umount "${MOUNTING_DIR}"
    RET_CODE=$((RET_CODE + $?))
    [[ ${RET_CODE} -ne 0 ]] && bail "Unable to unmount Sharedrive, or script errors. Please verify the host machine"

    echo "End of Script"
}

main "$@"
