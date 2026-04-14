#!/usr/bin/python3
# *****************************************************************************
# *
# *  (c) 2025 Aumovio Automotive Systems, Inc., all rights reserved
# *
# *  All material contained herein is AUMOVIO CONFIDENTIAL and PROPRIETARY.
# *  Any reproduction of this material without written consent from
# *  Aumovio, Inc. is strictly forbidden.
# *
# *   Filename: validate_ivd.py
# *
# *   Description:  Compare ivd from vanilla eSo image and with Aumovio
# *   manufacturing packages
# *
# *
# *****************************************************************************

import logging
import argparse
from pathlib import Path
from calculate_conti_ivd import calculate_ivd

def _parse_args():
    parser = argparse.ArgumentParser(description = "Conti offline IVD calculation")
    parser.add_argument(
        "--workspace", dest="workspace", 
        type=str,
        help="The workspace path",
        required=True
    )
    parser.add_argument(
        "--baseline", dest="baseline",
        type=str,
        help="Baseline ID",
        required=True
    )
    parser.add_argument(
        "--build_suffix", dest="build_suffix",
        type=str,
        help="BUild Suffix",
        required=False
    )
    parser.add_argument(
        "--release_id", dest="release_id",
        type=str,
        help="Release ID like conmod-sa515m-cl46r3-3.y",
        required=False,
        default="conmod-sa515m-3.y"
    )
    parsed_args = parser.parse_args()
    manufacturing_package_dir = parsed_args.workspace + "/conti/unzipped/tp_sdk_" + parsed_args.release_id +"_pkg/release/images/devel/4K"

    return {
        'manufacturing_package_crc': Path(manufacturing_package_dir+"/image_crc_versions.csv"),
        'eso_crc': next(Path(parsed_args.workspace).glob("unpacked_eso/*/images/image_crc_versions.csv")),
        'swdl_blocks_json': Path(parsed_args.workspace + "/.launchers/conmod-cm/delivery/swdl_blocks.json")
    }

if __name__ == "__main__":
    # Logging
    logging.basicConfig(filename='IVD_Report.txt', level=logging.DEBUG)

    environment = _parse_args()
    block_name = "General_Conti_Block_without_system"
    swdl_blocks_json = environment["swdl_blocks_json"]
    mnfct_ivd = calculate_ivd(swdl_blocks_json.read_text(),
                               environment["manufacturing_package_crc"].read_text(), block_name)
    logging.info("MANUFACTURING IVD: 0x{:x}".format(mnfct_ivd))

    eso_ivd = calculate_ivd(swdl_blocks_json.read_text(),
                               environment["eso_crc"].read_text(), block_name)

    logging.info("ESO ORIGINAL IVD: 0x{:x}".format(eso_ivd))

    assert(mnfct_ivd == eso_ivd)

    logging.info("IVD HASHES MATCHED")
