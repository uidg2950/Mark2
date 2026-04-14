![Conti_image](<img_path>/images/Aumovio.jpg)

## Automotive Technologies

**Engineering Release Notes**

**Telematics Platform**

**A AN PL2 RD EMEA SW**

<br><br>


# CONMOD_5_G_V[(otp_versions.txt--BASELINE_SHORT_VERSION)]_CW[(ReleaseDay--YY.WW.D)]

| Document ID | CONMOD_5_G_ V[(otp_versions.txt--BASELINE_SHORT_VERSION)]_CW[(ReleaseDay--YY.WW.D)]  |
|-------------|----------------------------------------|
| Revision: | 00.01|
| Revision Date: | [(ReleaseDate--YYYY.MM.DD)] |
| Status: | Released |
| Author(s):  | Julian Garcia, Makar Klochko |
| Document Location: | Package Release |

<br><br>


# Document Information

## Project

| Project Name|   Discipline  | Release Type & Version | 
|-------------|---------------|------------------------|
| ConMod  | SSW  |  CONMOD_5_G_ V[(otp_versions.txt--BASELINE_SHORT_VERSION)]_CW[(ReleaseDay--YY.WW.D)] | 


## Document Owner

| Role | Name | Department  | Location |   
|------|------|-------------|----------|
| Sys Int |  Julian Garcia |  A AN PL2 RD EMEA SW  |  WET   |


## Released by (internal document approval)

|Role  |Name |  Department  | Location  |Date |
|------|-----|--------------|-----------|-----|
|Sys Int | Julian Garcia | A AN PL2 RD EMEA SW  | WET |  [(ReleaseDate--YYYY.MM.DD)] |
|RRR | Conti ConMod R&D team | A AN PL2 RD EMEA RBG SR  | RBG, WET |  [(ReleaseDate--YYYY.MM.DD)] |


## Reviewed by

|Role  |Name |  Department  | Location  |Date | 
|------|-----|--------------|-----------|-----|
|Reviewer | Werner Eberle | A AN PL2 RD EMEA RBG SR |   RBG | [(ReleaseDate--YYYY.MM.DD)] | 
|Reviewer | Julian Garcia |  A AN PL2 RD EMEA SW  |  WET | [(ReleaseDate--YYYY.MM.DD)] | 


## Distribution List

|Name  |Department |  Email  |
|------|-----------|---------|
|Customer – e.Solutions | PM  | eso.Group.MIB-High-Integration@esolutions.de |
|Customer – e.Solutions | Integration | eso.group.ConModPLs@esolutions.de |
|Customer – Harman  | PM   |  conmodswlead@harman.com |

<br><br>


# Terminology, Definitions and Abbreviations

Specific acronyms / abbreviations, used in this document:

|Term / Acronym  |Definition| 
|----------------|----------|
|APP  | SW running on the TP application processor | 
|CM |   Configuration Management | 
|CR |   Change Request| 
|EE | Electrical Engineering| 
|FOSS | Free and Open Source Software| 
|FTR  | Formal Technical Review| 
|HAL  | Hardware Abstraction Layer| 
|HW | Hardware| 
|KW | Klocwork Source Code Analysis| 
|LPM |  Low Power Mode (airplane mode)| 
|MCfg | Modem Configuration| 
|MCM  | Modem Configuration Manager| 
|ME | Mechanical Engineering| 
|NAD |  Network Access Device| 
|NADIF |  Network Access Device Interface| 
|OSS |  Open Source Software| 
|OTC  |  Online Trust Center| 
|OTP |    Open Telematics Platform | 
|PR |  Defect| 
|RNL  | Release note location on ETF| 
|SE | Systems Engineering| 
|SW | Software| 
|SWDL | Software Download| 
|SWL  | Software Loading| 
|SSW  | System Software | 
|TP | Telematics Platform| 
|TVIP | Telematics Vehicle Interface Platform | 
|VuC  | Vehicle Micro-Controller|

<br><br>


# Introduction

## Scope

This Release Note specifies the details of the 

- [(otp_versions.txt--NAD_CAS_MODEM_STRING)], 
- [(otp_versions.txt--OTP_HOST_VERSION)], 
- [(otp_versions.txt--OTP_VERSION)]


baselines as part of this 

- CONMOD_5_G_V[(otp_versions.txt--BASELINE_SHORT_VERSION)]_CW[(ReleaseDay--YY.WW.D)] 

release.

It describes the technical requirements, installation procedures, target environment, configuration changes, open defects, key performance indicators, test results and other qualifying information for this release.
All paths starting with "$RNL/" are given relative to the release note location on ETF Folder.


## Identification

Physical Configuration and Status of Files:

|Software Component |File Name  |Version  |Stored location |
|-------------------|-----------|---------|----------------|
|Open Telematics Platform SDK | sdk.tar.gz  |[(otp_versions.txt--OTP_VERSION)] |tp_sdk_conmod-sa515m(-cl4x)-3.y_pkg/sdk |
|EFS |  sdk-constructor.tar.gz| [(otp_versions.txt--OTP_VERSION)] | tp_sdk_conmod-sa515m(-cl4x)-3.y_pkg/sdk |
|Conti signed images|conti-signed-images.tar.gz | [(otp_versions.txt--OTP_VERSION)] | tp_sdk_conmod-sa515m(-cl4x)-3.y_pkg/sdk|

<br><br>


# Documentation Baseline

This section lists the technical documents related to the functionality of the delivered system, hardware, and/or software.


## Documentation in SDK

|Document Name | Description |  Version  |
|--------------|-------------|-----------|
|package-info.txt   |List with the version of all the packages |  [(otp_versions.txt--OTP_VERSION)]|
|[(otp_versions.txt--OTP_VERSION)]_doxygen.tar.gz| Doxygen API information | [(otp_versions.txt--OTP_VERSION)]|
|Readme.txt | Description on the contents for the Telematics Platform SDK bundle |  [(otp_versions.txt--OTP_VERSION)]|
|modem_qshrink.tar.gz |qshrink binary to support debugging| [(otp_versions.txt--OTP_VERSION)]|

## User Guides

|Document Name | Description |  Version  |
|--------------|-------------|-----------|
|Flashing_Instruction_TCU_for_SDK_Release_3.1.611_mcfg.pdf |  QFIL Flashing Instruction|  1.00|
|NADIF_API_ChangeNotificationLPM.pdf | NADIF API to set Modem power up operating mode | 1.0|
|sfe_vef_fc_conn.pdf | To verify the packet forwarding using SFE | 2020-08-24|
|Install_sec.elf_to_correct_NAND_MTD_partition.pdf | How to address a NAND MTD partition "by name" | 01|
|TP_102G-00001_Glossary.pdf |TP Glossary |  14.00|
|TP_F101U-00009_User_Guide_Common_Service.pdf |TP User guide for Common Service | 03.00|
|TP_F100W-00015_Writers_Guide_Update_Agent.pdf  |TP Writer guide for Update Agent | 09.00|
|TP_F101U-00023_User_Guide_Common_Library.pdf |TP User guide for Common Library | 03.00|
|TP_F101U-00025_User_Guide_Application_Permissions_Manager.pdf| TP User guide for Application permissions Manager | 03.00|
|TP_F101U-00026_User_Guide_Persistence.pdf  |TP User guide for Persistence |  06.00|
|TP_F101U-00028_User_Guide_Software_Loading_Manager.pdf |TP User guide for Software Loading Manager | 18.00|
|TP_F101U-00030_User_Guide_Security.pdf |TP User guide for Security |04.00|
|TP_F103U-00034_User_Guide_5G_NAD_Module.pdf| TP User guide for 5G NAD Module | 15.00|
|TP_F101U-00035_User_Guide_SDK.pdf| TP User guide for SDK | 01.00|
|TP_F101U-00036_User_Guide_NADIF_5G_NAD.pdf|  TP User guide for NADIF 5G NAD |  14.00|
|TP_F101U-00037_User_Guide_Time_Manager_5G_NAD.pdf  |TP User guide for Time Manager 5G NAD|   06.00|
|TP_F101U-00039_User_Guide_5G_NAD_Tier1_Power_Management_ConMod.pdf|  TP Guide NAD Tier1 Power Management|  02.00|
|TP_F101U-00040_User_Guide_Update_Package_Generation.pdf| TP Update package generation guide|   05.00|
|TP_F100U-00044_User_Guide_Modem_Configuration_Manager_ConMod.pdf |MCM tool |03.00|
|TP_F100U-00045_User_Guide_Device_Tree_Configuration.pdf| TP User Guide Device Tree Config| 02.00|
|TP_F103U-00046_User_Guide_Physical_Configuratiion_Audit.pdf  |TP User guide  Physical configuration Audit Script |01.00|
|TP_F101U-00047_User_Guide_Thermal_Management_5G_NAD.pdf| TP User guide for 5G Thermal Management |06.00|
|TP_F100U-00048_User_Guide_gPTP_Feature_User_Guide.pdf  |TP User Guide (g)PTP features of Ethernet MAC|01.00|
|TP_F101U-00053_User_Guide_NADIF_ConMod.pdf |ConMod-specific NADIF| 02.00|
|TP_F101U-00054_User_Guide_SecureBoot_5G_NAD_ConMod.pdf |Secure Boot for ConMod |01.00|
|TP_F101U-00055_User_Guide_5G_NAD_Module_ConMod.pdf |NAD Module for ConMod| 03.00|
|TP_F101U-00057_User_Guide_Update_Package_Generation_ConMod.pdf | Update Package Gen. For ConMod |  01.00|
|TP_F101U-00059_User_Guide_Flash_Scrub_and_Read_Patrol_ConMod.pdf  |Flash Scrubbing |2.0|
|TP_LTE_5G_SA515M_NAD_Specification.pdf |NAD HW Specification | 3.1|
|Update_Continental_Linux_user_and_group_range.pdf  |Linux user and group ranges  |1.0|
|ConMod_Telematics_Voice_Audio_Customisation_Guide.pdf| Telematics Voice/Audio Customization Guide from Qualcomm  |2.0|
|ConMod_How_to_sign_system_fs.pdf |Image signing / script modification| 2.0|
|Collecting_NAND_dumps.pdf  |How to collect a NAND dump |1.0|
|TP-NAD-RAM-Dumps-on-eMMC.pdf |Dump RAM to eMMC |1.0|
|disable_rx_delay.pdf |define io macro parameters to set rx-dll-bypass  |1.0|
|Fuse_OEM_ID_to_enable_boot_with_QTI_PROD_secured_Qualcomm_images.pdf | How to fuse OEM_ID  |1.2|
|Default.cfg| QXDM default config |1.0|
|default-qxdm5.dmc| QXDM dm5 mask file| 1.0|
|audio.cfg| QXDM audio log config |1.0|
|audio.dmc| QXDM audio log mask file| 1.0|
|CMCONTI-820_workaround_OEM_ID_fuse_sec_elf.zip | Special sec.elf image to fuse OEM_ID| 1.0|

<br><br>


# New Functionality

The purpose of this section is to highlight the functionality that has been introduced, enabled or validated in this HTP Release:

## API Changes

API versions:

- API HAL VERSION: hal-3.0.0
- API FW VERSION: fw-3.0.0

## New Features and Improvements

### Features

[(RRR--Highlights for this Release--Features)]

### Bugfixes

[(RRR--Highlights for this Release--Bugfixes / Improvements)]


### Detailed Feature List

[(RRR--Detailed Scope--Implemented Features)]



Linux user and group range, see "Update_Continental_Linux_user_and_group_range.pdf".

<br><br>


# Installation

##  BUILD INFO

See **"TP_F101U-00035_User_Guide_SDK.pdf"**.

## Driver Installation

See **"TP_F103U-00034_User_Guide_5G_NAD_Module.pdf"**.

## SW Update / Flashing Procedure

See **"TP_F103U-00034_User_Guide_5G_NAD_Module.pdf"**.

The description for QFIL flashing due to the new memory mapping can be found in 

**"Flashing_Instruction_TCU_for_SDK_Release_3.1.611_mcfg_v0.90.pdf"**. 

This flashing instruction is also applicable for the current release.

## Special Instructions

See **"TP_F103U-00034_User_Guide_5G_NAD_Module.pdf"**.

<br><br>


# Target Environment and Compatibility

## Hardware

### TCU Hardware Configuration

| Component Name|   Supplier/Comments| 
|---------------|--------------------| 
| TCU C2.1, C2.2, C2.3|   Harman| 


This release is compatible with NAD C2 hardware.
For Test Environment please refer to Test Report Document.

### NAD Hardware Variants

The SW supports the following NAD module HW variants:

| Variant Name: |   Europe|   North America | Rest of World | China| 
|---------------|---------|-----------------|---------------|------|
| Short Name  | EU  | NA  | RW|   CN| 
| Variant | FE5EU0020 | FE5NA0020 | FE5RW0020 | FE5CN0020 | 
| HW ID | 0x00440601  | 0x00450601  | 0x00430601  | 0x00460601 | 
| HW version | P4.1 BOM version2 | P4.1 BOM version2 | P4.1 BOM version2 | P4.1 BOM version2 | 
| xqcn file version | QCN_FE5EU0020_35.00 | QCN_FE5NA0020_35.00 | QCN_FE5RW0020_35.00 | QCN_FE5CN0020_35.00 | 


## Release Level

Development SW for 
- bench
- car, stationary tests
- drive tests

<br>


## Software

### Software Configuration

| SW Component Name | Version(s)  | Supplier/Comments| 
|-------------------|-------------|------------------|
| Linux Kernel  | [(otp_versions.txt--LINUX_KERNEL_VERSION)]  | The Linux Foundation| 
| Qualcomm base code |  [(otp_versions.txt--QCOM_METABUILD_STRING)] |   Qualcomm| 
| Modem SW |  [(otp_versions.txt--NAD_CAS_MODEM_STRING)] | Qualcomm| 
| SA515M A7 TelSDK|   [(otp_versions.txt--TELUX_VERSION)] |   Qualcomm| 


### Banner

```
[(Test_Results--BANNER)]
```

AT+GMR output should follow this format:

```
"<QC Metabuild ID>", "<Boot Ver>", "<Apps Ver>", "<Modem SW Ver>", "<xQCN Ver>", "<Conti custom config Ver>", "<OEM Ver>", "<Carrier config Ver>" 
```

AT+GMR for this release should be:

```
[(Test_Results--at+gmr)]
```

**Disregard EFS version of this board.**

<br><br>


# System Limitations and Constraints

## Component System Limitations and Constraints


## Known Defects

[(RRR--Detailed Scope--Known Defects)]

<br><br>


# Feature Limitations and Hints on Testing Features

[(RRR--Limitations to be Documented in Release Notes)]


<br><br>


# Changes to Product Configuration

This section describes changes made to the product configuration for this release.

## Defects Closed in this Release

[(RRR--Detailed Scope--Corrected Defects)]


## OSS Packages 

The information on deployed (F)OSS packages can be taken from 

```
tp_sdk_[(otp_versions.txt--OTP_VERSION)]_pkg.zip
   \tp_sdk_conmod-sa515m-(cl4x-)3.y_pkg
      \release
         \docs
            package-info.txt
```

This list contains four sections:

| Short Name	| Section Header| Description| 
|-------------|---------------|------------| 
| **"Host"**	| === Packages associated with tools running on development host ===	|Packages/tools running on the host during build and SDK generation |
| **"Target-SWDev"**	| === Packages used for target SW development target (not installed on target flash) [target] ===	|Packages used for SW Dev of other packages. Those are not installed on the TCU target themselves. Mostly binaries or executors shared or used by other packages. |
| **"Target-install"**	| === Packages fully installed on target flash [target] ===	|Packages installed on the TCU target |
| **"Toolchain-SWDev"** | === Packages used for target SW development toolchain (not installed on target flash) [toolchain] ===	|Packages used for SW dev of the toolchain (not installed on target) |
| **"Toolchain-install"**	| === Packages fully installed on target flash [toolchain] ===	|Packages for tooling, support SW, fully installed on target|

<br><br>


# New Defects

These have been included in section "Limitations and Constraints". 
Please also refer to the Test Report for defects found during test.

<br><br>


# Key Performance Indicators

## RAM/Flash/CPU Usage and Startup-Shutdown-Reboot Times

| Document Name	| Description	| Location| 
|---------------|-------------|---------| 
| RAM usage | 	RAM - Split SoC cores	| See 13 Appendix: “KPI Report”| 
| Flash usage | 	NAND partitions and sizes | 	See 13 Appendix: “KPI Report” | 
| CPU usage | 	CPU usage of running processes| 	See 13 Appendix: “KPI Report”| 
| Startup-Shutdown-Reboot|  Times	Times for Startup, Shutdown and Reboot	| See 13 Appendix: “KPI Report”| 



## Code Quality: Static Code Check

| Category | 	Level	| Comment	| Number                      | 
|----------|--------|---------|-----------------------------| 
| "serious_difference"| 	L1 | 	Klocwork findings, severity 1	| [(SWC_json--Klockwork-lv1)] | 
| "considerable_difference"	| L2| 	Klocwork findings, severity 2	| [(SWC_json--Klockwork-lv2)] | 
| "marginal_difference"	| L3	| Klocwork findings, severity 3	| [(SWC_json--Klockwork-lv3)] | 
| "no_or_slight_difference"	| L4	| Klocwork findings, severity 4	| no figures collected        | 



## Code Quality: Unit Test

| Category	| Value                                | 
|-----------|--------------------------------------| 
| UTFC = Unit Test Function Coverage	| [(google_test.properties--Function)] | 
| UTBC = Unit Test Branch Coverage| [(google_test.properties--Branch)]   | 

<br><br>


# Testing and Test Results

Test Results for [(otp_versions.txt--BASELINE_SHORT_VERSION)] are provided in a separate test report document.
See also section "Limitations and Constraints".

<br><br>


# Other Information

## Doxygen APIs

See
```
tp_sdk_[(otp_versions.txt--OTP_VERSION)]_pkg.zip
   \tp_sdk_conmod-sa515m-(cl4x-)3.y_pkg
      \Doxygen
         [(otp_versions.txt--OTP_VERSION)]_doxygen.tar.gz
```

## Integration

See 
```
tp_sdk_[(otp_versions.txt--OTP_VERSION)]_pkg.zip
   \tp_sdk_conmod-sa515m-(cl4x-)3.y_pkg
      \release
         \docs
            otp_versions.txt
```

<br><br>


# Appendix

KPI Report: Starts on next page.
