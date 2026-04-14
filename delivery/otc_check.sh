#!/bin/bash
# *****************************************************************************
# *
# *  (c) 2023 Continental Automotive Systems, Inc., all rights reserved
# *
# *  All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *  Any reproduction of this material without written consent from
# *  Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *  Filename: otc_check.sh
# *
# *  Description: Script responsible for validation of OTC credentials
# *
# *
# *****************************************************************************

SCRIPT_NAME=$(basename "${BASH_SOURCE[0]}")
# OTCConnect artfifactory link
OTC_CONNECT_ARTIF="https://eu.artifactory.automotive.cloud/artifactory/ait_catch_generic_l/releases/OTConnect"
OTC_CONNECT_MAJOR_VERSION="14.0"
OTC_CONNECT_MINOR_VERSION="598"
OTC_CONNECT_FILENAME="OTConnect-${OTC_CONNECT_MAJOR_VERSION}-${OTC_CONNECT_MINOR_VERSION}.zip"
OTC_CONNECT_FULL_URL="${OTC_CONNECT_ARTIF}/${OTC_CONNECT_MAJOR_VERSION}/${OTC_CONNECT_FILENAME}"
# FIXME:  This value should be updated in ~/.credentials/artifactory (9.4.2026)

LOGFILE=$(dirname "${BASH_SOURCE[0]}")/"${SCRIPT_NAME%.*}.log"
echo "LOGGING to ${LOGFILE}"
exec > >(tee "${LOGFILE}");
RET_CODE=0
# ----------------------------------------------------------- #
# All output from commands in this block sent to file $LOGFILE.
echo "START: ${SCRIPT_NAME} $(date)"

help_info() {
    cat << HELP
./$(basename "$0") --username auto\\\uid99999 --password YOUR_WINDOWS_SECRET_PASSWORD --domain ACOUNT_DOMAIN --release_id RELEASE_ID
Script for manual testing of esim.

Options:
    -h|--help                   Display this information.
    -u|--username               OTC user
    -p|--password               Windows domain password
    -d|--domain                 Windows domain
    -r|--release_id             Release ID

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
            -r|--release_id)
                RELEASE_ID="$1"
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
    source "${WORKSPACE}/.launchers/conmod-cm/utils/platform-common.lib"
    source "${WORKSPACE}/.launchers/conmod-cm/utils/artifactory.lib"

    [[ -z "${OTC_USERNAME}" ]] && bail "OTC Username is empty"
    [[ -z "${OTC_DOMAIN}" ]] && bail "OTC user domain is empty"
    [[ -z "${OTC_PASSWORD}" ]] && bail "OTC user password is empty"

    OTC_ACCOUNT="${OTC_DOMAIN}\\${OTC_USERNAME}"
}

check_credentials() {
    mkdir -p "${WORKSPACE}/OTConnect"
    pushd "${WORKSPACE}/OTConnect" > /dev/null

    ## FIXME: Workaround for credentials
    # Is the token value in the Node correct?
    token=$(read_artifactory_credentials)
    response=$(curl -silent --show-error --fail "${OTC_CONNECT_ARTIF}" -u "${token}" | grep "HTTP")

    if [[ ! "${response}" =~ "200" ]]; then
        echo "> WARNING: token in node is not valid!!!!!!!!!"
        echo "> Replaced by CURL_TOKEN value in this script"
        token="${ARTIFACTORY_USER}:${CURL_TOKEN}"
    fi

    # Auth needed
    echo "> curl -u 'TOKEN' -O '${OTC_CONNECT_FULL_URL}'"
    curl -u "${token}" -O "${OTC_CONNECT_FULL_URL}"

    echo "> unzip '${OTC_CONNECT_FILENAME}'"
    unzip "${OTC_CONNECT_FILENAME}"

    echo "> chmod 700 ./run"
    chmod 700 ./run

    echo "> dos2unix ./run"
    dos2unix ./run
    echo "> ./run projects --user='${OTC_ACCOUNT}' --pass='DO NOT PEEP' --role='Integrator' --connection='SLATM-Integration'"
    ./run projects --user="${OTC_ACCOUNT}" --pass="${OTC_PASSWORD}" --role='Integrator' --connection="SLATM-Integration"
    ret=$?
    [ $ret -ne 0 ] && bail "ERROR: credentials are wrong!"
    popd > /dev/null
}

main() {
  process_cli_parameters "$@"
  init_parameters
  # FIXME:
  if [[ "${RELEASE_ID}" =~ conmod-sa515m-3.y ]] || [[ "${RELEASE_ID}" =~ conmod-sa515m-cl ]]; then
      check_credentials
  else
      echo "check"
  fi
}

main "$@"
