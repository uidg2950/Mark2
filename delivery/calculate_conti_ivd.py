#!/usr/bin/env python3

##
# © e.solutions GmbH – all rights reserved
##

import logging
import json
from io import StringIO
import csv
from typing import List, Tuple, Any, Dict
from zlib import crc32

#######################################################
# Parsing of swdl_blocks.json
#######################################################
"""swdl_blocks.json format:

[
  {
    "block_name": "General_Conti_Block",
    "content": [
      {"abl.elf": "abl"},
      {"aop.mbn": "aop"},
      {"boot.img": "boot"},
      {"devcfg.mbn": "tz_devcfg"},
      {"hyp.mbn": "qhee"},
      {"multi_image.mbn": "multi_image"},
      {"sbl1.mbn": "sbl"},
      {"tz.mbn": "tz"},
      {"uefi.elf": "uefi"},
      {"tp-pers-install.tar.gz": ""},
      {"system.ubifs": "system"},
      {"dsp2.ubifs": "dsp2"}
    ]
  },
  {
    "block_name": "MCFG_Conti_Block",
    "content": [
    {"tp_modem_config_list.tar.gz": [
       "mcfg_hw_FE515_LE_SS.mbn",
       "mcfg_sw_Vodafone_VoLTE_Turkey.mbn",
       "mcfg_sw_Vodafone_VoLTE_Germany.mbn",
       "mcfg_sw_Vodafone_M2M_Commercial_Global.mbn",
       "mcfg_sw_Verizon_CDMAless.mbn",
       "mcfg_sw_Telstra_Commercial.mbn",
       "mcfg_sw_Rogers_Commercial_CA.mbn",
       "mcfg_sw_ROW_Commercial.mbn",
       "mcfg_sw_MTS_Commercial_RU.mbn",
       "mcfg_sw_KT_Commercial_KT_LTE.mbn",
       "mcfg_sw_Etisalat_VoLTE.mbn",
       "mcfg_sw_DT_VoLTE_Commercial.mbn",
       "mcfg_sw_DCM_Commercial.mbn",
       "mcfg_sw_Cubic_VoLTE.mbn",
       "mcfg_sw_Cubic_Korea_VoLTE.mbn",
       "mcfg_sw_CU_Commercial_VoLTE.mbn",
       "mcfg_sw_CMCC_Commercial_Volte_OpenMkt.mbn",
       "mcfg_sw_Brazil_Commercial.mbn",
       "mcfg_sw_ATT_VoLTE.mbn",
       "mcfg_sw_AMX_Commercial_MX.mbn"
      ]
     }
    ]
  }
]

"""

# e.g., "General_Conti_Block"
BlockName = str

# e.g., "abl.elf"
BlockIngrediant = str

# e.g., "abl"
BlockComponent = str

# e.g., ["mcfg_hw_FE515_LE_SS.mbn", "mcfg_sw_Vodafone_VoLTE_Turkey.mbn"]
BlockComponentList = List[BlockComponent]

# e.g.
# {
#     "abl.elf" --> ["abl"],
#     "tp_modem_config_list.tar.gz" --> ["mcfg_hw_FE515_LE_SS.mbn", "mcfg_sw_Vodafone_VoLTE_Turkey.mbn"],
#     "tp-pers-install.tar.gz" --> []
# }
#
BlockIngrediantMap = List[Tuple[BlockIngrediant, BlockComponentList]]

# One entry in the swdl_blocks.json array
BlockInfo = Tuple[BlockName, BlockIngrediantMap]

# Complete content of swdl_blocks.json
BlockInfoList = List[BlockInfo]


def parseBlockComponentsFromString(blockComponent: str) -> BlockComponentList:
    """
    
    There are three ways that a BlockComponentList can represented in the json:

    1) An empty string "", which means an empty list
    2) A non-empty string "uefi"
    3) An array of strings ["mcfg_hw_FE515_LE_SS.mbn", "mcfg_sw_Vodafone_VoLTE_Turkey.mbn"]

    This helper function handles the first and second case.
    """
    return [] if blockComponent == "" else [blockComponent]


def parseBlockComponentsFromArray(
        blockComponentList: List[Any]) -> BlockComponentList:
    """
    
    There are three ways that a BlockComponentList can represented in the json:

    1) An empty string "", which means an empty list
    2) A non-empty string "uefi"
    3) An array of strings ["mcfg_hw_FE515_LE_SS.mbn", "mcfg_sw_Vodafone_VoLTE_Turkey.mbn"]

    This helper function handles the third case.
    """
    for blockComponent in blockComponentList:
        assert isinstance(
            blockComponent,
            str), "Invalid block component: {}".format(blockComponent)
    return blockComponentList


def parseBlockIngrediant(
        blockIngrediant: Dict) -> Tuple[BlockIngrediant, BlockComponentList]:
    """Parse a block ingrediant

    Example 1:
    {"tp_modem_config_list.tar.gz": ["mcfg_hw_FE515_LE_SS.mbn", "mcfg_sw_Vodafone_VoLTE_Turkey.mbn"]}
    
    Example 2:
    {"abl.elf": "abl"}
    
    Example 3:
    {"tp-pers-install.tar.gz": ""}
    """
    assert len(blockIngrediant) == 1, "Invalid block ingrediant: {}".format(
        blockIngrediant)
    name, val = next(iter(blockIngrediant.items()))
    assert isinstance(name,
                      str), "Invalid block ingrediant name: {}".format(name)
    if isinstance(val, str):
        return name, parseBlockComponentsFromString(val)
    assert isinstance(val, list), "Invalid block component: {}".format(val)
    return name, parseBlockComponentsFromArray(val)


def parseBlockIngrediantMap(ingrediantMap: List[Any]) -> BlockIngrediantMap:
    """Parse an ingrediant map

    Example:
    [
        {"abl.elf": "abl"},
        {"tp_modem_config_list.tar.gz": ["mcfg_hw_FE515_LE_SS.mbn", "mcfg_sw_Vodafone_VoLTE_Turkey.mbn"]}
    ]
    """
    result = []
    for blockIngrediant in ingrediantMap:
        assert isinstance(
            blockIngrediant,
            dict), "Invalid block ingrediant: {}".format(blockIngrediant)
        result.append(parseBlockIngrediant(blockIngrediant))
    return result


def parseBlockInfo(blockInfo: Dict) -> BlockInfo:
    """Parse a block info

    Example:
    {
        "block_name": "General_Conti_Block",
        "content": [
            {"abl.elf": "abl"},
            {"tp_modem_config_list.tar.gz": ["mcfg_hw_FE515_LE_SS.mbn", "mcfg_sw_Vodafone_VoLTE_Turkey.mbn"]}
        ]
    }
    """
    assert "block_name" in blockInfo, "Invalid block info: {}".format(
        blockInfo)
    name = blockInfo["block_name"]
    assert isinstance(name, str), "Invalid block name: {}".format(name)
    assert "content" in blockInfo, "Invalid block info: {}".format(blockInfo)
    content = blockInfo["content"]
    assert isinstance(content,
                      list), "Invalid block content: {}".format(content)
    return name, parseBlockIngrediantMap(content)


def parseBlockInfoList(blockInfoList: List[Any]) -> BlockInfoList:
    """Parse block info list
    """
    result = []
    for blockInfo in blockInfoList:
        assert isinstance(blockInfo,
                          dict), "Invalid block info: {}".format(blockInfo)
        result.append(parseBlockInfo(blockInfo))
    return result


def parseBlockInfoJson(swdl_blocks_json_content: str) -> BlockInfoList:
    """Parse the JSON string swdl_blocks_json_content and interpret it as a block info list
    """
    blockInfoList = json.loads(swdl_blocks_json_content)
    assert isinstance(
        blockInfoList,
        list), "Invalid block info list: {}".format(blockInfoList)
    return parseBlockInfoList(blockInfoList)


def allBlockComponents(blockInfoList: BlockInfoList,
                       blockName: BlockName) -> BlockComponentList:
    """List all SWDL block components for a SWDL block
    """
    # Find SWDL block
    _, ingrediantMap = next(i for i in blockInfoList if i[0] == blockName)
    # Concatenate lists
    return sum([x[1] for x in ingrediantMap], [])


#######################################################
# Parsing of image_crc_versions.csv
#######################################################
"""image_crc_versions.csv format:

<Image Name>,<Image Type>,<Image CRC>,<Image Version>
abl,PROGRAM,0x74ab1208,0aa9d41
aop,PROGRAM,0xcea7b345,67822b0
apdp,PROGRAM,0x1cde50e1,PLATFORM-DEFAULT-VERSION
boot,PROGRAM,0x0bb5ec15,b2c1ef1
dsp2,PROGRAM,0x050bb4ef,b7d47b0
mcfg_hw_FE515_LE_SS.mbn,PROGRAM,0x199443cb,0a018025
mcfg_sw_AMX_Commercial_MX.mbn,PROGRAM,0xc4965b39,0a011600
mcfg_sw_ATT_VoLTE.mbn,PROGRAM,0xb5e1482b,0a050335
mcfg_sw_Brazil_Commercial.mbn,PROGRAM,0x60bdaaa1,0a012100
mcfg_sw_CMCC_Commercial_Volte_OpenMkt.mbn,PROGRAM,0x8c6c802d,0a012010
mcfg_sw_Cubic_Korea_VoLTE.mbn,PROGRAM,0xf3d6a0b6,0a02f901
mcfg_sw_Cubic_VoLTE.mbn,PROGRAM,0x49ff473b,0a03fa01
mcfg_sw_CU_Commercial_VoLTE.mbn,PROGRAM,0x24a4d7c5,0a011561
mcfg_sw_DCM_Commercial.mbn,PROGRAM,0xf338dfc5,0a010d0d
mcfg_sw_DT_VoLTE_Commercial.mbn,PROGRAM,0x228a139d,0a011f1f
mcfg_sw_Etisalat_VoLTE.mbn,PROGRAM,0xf36abfdc,0a02fb01
mcfg_sw_KT_Commercial_KT_LTE.mbn,PROGRAM,0xb0fa0690,0a01280b
mcfg_sw_MTS_Commercial_RU.mbn,PROGRAM,0x295451e2,0a013a00
mcfg_sw_Rogers_Commercial_CA.mbn,PROGRAM,0x9aa3059a,0a014800
mcfg_sw_ROW_Commercial.mbn,PROGRAM,0xd95ac938,0a030809
mcfg_sw_Telstra_Commercial.mbn,PROGRAM,0xa2632148,0a030f00
mcfg_sw_Verizon_CDMAless.mbn,PROGRAM,0x98e7cf79,0a010126
mcfg_sw_Vodafone_M2M_Commercial_Global.mbn,PROGRAM,0x64767917,0a120400
mcfg_sw_Vodafone_VoLTE_Germany.mbn,PROGRAM,0x5df3416f,0a010449
mcfg_sw_Vodafone_VoLTE_Turkey.mbn,PROGRAM,0xcbef1dea,0a0104c6
multi_image,PROGRAM,0x659d6fb2,6c7428f
qhee,PROGRAM,0x14c1b0a9,475dac8
sbl1,PROGRAM,0x6134247d,83d431d
sbl1-audi-conmod,PROGRAM,0x56133453,83d431d
sbl1-chestnut,PROGRAM,0x6134247d,83d431d
sbl1-chestnut-lite,PROGRAM,0xf93e6dbd,83d431d
system,PROGRAM,0x5c08980f,2.0.0.0
tz,PROGRAM,0xc1734370,475dac8
tz_devcfg,PROGRAM,0xe8b15baf,475dac8
uefi,PROGRAM,0xb2396f8a,add374b
xbl_config,PROGRAM,0x77f19204,83d431d

"""

# e.g., "abl"
ImageName = BlockComponent

# e.g., "PROGRAM"
ImageType = str

# e.g., "0xb2396f8a"
ImageCRC = int

# e.g., 2.0.0.0
ImageVersion = str

# e.g., ["system", "PROGRAM", 0x5c08980f, "2.0.0.0"]
ImageInfo = Tuple[ImageName, ImageType, ImageCRC, ImageVersion]

# Complete content of image_crc_versions.csv
ImageInfoList = List[ImageInfo]


def parseImageInfo(row: List[str]) -> ImageInfo:
    """Parse one image CRC versions file row

    Example:
    ["system", "PROGRAM", "0x5c08980f", "2.0.0.0"]

    Return (CRC converted to int):
    ["system", "PROGRAM", 0x5c08980f, "2.0.0.0"]
    """
    assert len(row) == 4, "Unexpected row in CRC versions file: {}".format(row)
    name = row[0]
    # slightly ugly workaround; "sbl" is supposed to refer to "sbl1-audi-conmod"
    if name == "sbl1-audi-conmod":
        name = "sbl"
    image_type = row[1]
    crc = int(row[2], 0)
    version = row[3]
    return name, image_type, crc, version


def parseImageCrcVersionsCsv(
        image_crc_versions_csv_content: str) -> ImageInfoList:
    """Parse the CSV string image_crc_versions_csv_content and interpret it as an image info list
    """
    imageInfoList = csv.reader(StringIO(image_crc_versions_csv_content))
    rows = [row for row in imageInfoList]
    assert len(rows) > 1, "Invalid image CRC versions file: {}".format(
        image_crc_versions_csv_content)
    title_row = rows[0]
    assert title_row == [
        "<Image Name>", "<Image Type>", "<Image CRC>", "<Image Version>"
    ], "Unexpected title row in image CRC versions file: {}".format(title_row)
    return [parseImageInfo(row) for row in rows[1:]]


def availableImageNames(imageInfoList: ImageInfoList) -> List[ImageName]:
    """List all the avaible image names in image_crc_versions.csv
    """
    return [info[0] for info in imageInfoList]


#######################################################
# Helper functions
#######################################################


def checkBlockComponents(blockComponents: BlockComponentList,
                         availableImages: List[ImageName]) -> None:
    """Check that the block components from swdl_blocks.json are a subset of the images in image_crc_versions.csv
    """
    blockComponentsSet = set(blockComponents)
    availableImagesSet = set(availableImages)
    # images which are in blockComponentsSet but not in availableImagesSet
    difference = blockComponentsSet.difference(availableImagesSet)
    assert len(
        difference
    ) == 0, "The following block components from the JSON are not available in the CSV: {}".format(
        difference)


def findInfo(blockComponent: BlockComponent,
             imageInfoList: ImageInfoList) -> ImageInfo:
    """Find the image information for a block component
    """
    return next(i for i in imageInfoList if i[0] == blockComponent)


def findCRC(blockComponent: BlockComponent,
            imageInfoList: ImageInfoList) -> int:
    """Find the CRC32 for a block component
    """
    return findInfo(blockComponent, imageInfoList)[2]


def findCRCs(blockComponents: BlockComponentList,
             imageInfoList: ImageInfoList) -> List[int]:
    """Find all CRC32s for the block components of a SWDL block
    """
    return [findCRC(c, imageInfoList) for c in blockComponents]


def concatenate(crcs: List[int]) -> bytes:
    """Concatenate CRCs (as byte arrays of length 4)
    """
    return b''.join([crc.to_bytes(4, byteorder='big') for crc in crcs])


def crc(val: bytes) -> int:
    """zlib CRC32, the same algorithm is used by the target library
    """
    return crc32(val, 0)


#######################################################
# IVD calculations
#######################################################


def calculate_ivd(swdl_blocks_json_content: str,
                  image_crc_versions_csv_content: str, blockName: str) -> int:
    """Calculate the IVD of a Conti SWDL block

    Args:
        swdl_blocks_json_content (str): Textual content of swdl_blocks.json (static Conti file)
        image_crc_versions_csv_content (str): Textual content of image_crc_versions.csv (dynamically generated metainfo alongside Conti images)
        blockName (str): Name of the Conti SWDL block, e.g. General_Conti_Block

    Returns:
        int: The CRC32, same will be calculated on the target
    """
    blockInfoList = parseBlockInfoJson(swdl_blocks_json_content)
    blockComponents = allBlockComponents(blockInfoList, blockName)
    # Sort lexicographically
    blockComponents.sort()
    logging.debug("Relevant components for SWDL block {}: {}".format(
        blockName, blockComponents))
    imageInfoList = parseImageCrcVersionsCsv(image_crc_versions_csv_content)
    availableImages = availableImageNames(imageInfoList)
    checkBlockComponents(blockComponents, availableImages)
    relevantCRCs = findCRCs(blockComponents, imageInfoList)
    logging.debug("Relevant CRCs: {}".format(
        ["0x{:x}".format(c) for c in relevantCRCs]))
    concatenated = concatenate(relevantCRCs)
    logging.debug("Concatenated: 0x{}".format(concatenated.hex()))
    return crc(concatenated)


#######################################################
# For usage as a script (e.g., testing)
#######################################################

import argparse as ap
from pathlib import Path


def parse_args(parser: ap.ArgumentParser, args: List[str]) -> ap.Namespace:

    # Options

    # -

    # Positional arguments

    parser.add_argument("swdl_blocks_json",
                        type=Path,
                        help="swdl_blocks.json from extracted Conti SDK.")

    parser.add_argument(
        "image_crc_versions_csv",
        type=Path,
        help=
        "image_crc_versions.csv which is generated alongside the Conti images inside the 4K folder."
    )

    parser.add_argument(
        "block_name",
        type=str,
        help=
        "SWDL block name matching the name in swdl_blocks.json from extracted Conti SDK"
    )

    return parser.parse_args(args)


def main(args: List[str]) -> int:
    # Parse args
    description = "Conti offline IVD calculation"
    parser = ap.ArgumentParser(description=description)
    parsed_args = parse_args(parser, args)

    swdl_blocks_json = Path(parsed_args.swdl_blocks_json)
    image_crc_versions_csv = Path(parsed_args.image_crc_versions_csv)
    block_name = str(parsed_args.block_name)

    # Logging
    logging.basicConfig(level=logging.DEBUG)

    ivd = calculate_ivd(swdl_blocks_json.read_text(),
                        image_crc_versions_csv.read_text(), block_name)
    print("IVD: 0x{:x}".format(ivd))

    return 0


import sys

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
