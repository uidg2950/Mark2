# *****************************************************************************
# *
# *  (c) 2016-2020 Continental Automotive Systems, Inc., all rights reserved
# *
# *  All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename:  release_baseline_reader.ps1
# *
# *   Description:  Extracts the otp label from release plan and runs the script
# *                 for triggering a new build. For powershell 3.0
# ******************************************************************************

[cmdletbinding()]
Param
(
	[Parameter(Mandatory=$true,  Position=0)] [String] $project,   # e.g. conmod
	[Parameter(Mandatory=$true,  Position=1)] [String] $release    # e.g. conmod-sa515m-3.y
)

$WORKSPACE = $Env:WORKSPACE

$ScriptDir = Split-Path -parent $MyInvocation.MyCommand.Path
Import-Module $ScriptDir\modules\utils.psm1
Import-Module $ScriptDir\modules\excel_utils.psm1

Write-Host "------------- Searching Baseline -------------"

If ($variant.ContainsKey($release)){
	Write-Host "> Opening spreadsheet $release_plan"
	$excel = Open-Excel
	if ($excel -eq $null){
		Write-Error "Could not open Excel!"
		exit 1
	}
	Try {
		$workbook = Get-Workbook $excel $release_plan
		$spreadsheet_base_name = "$($variant.Get_Item($release))"
		$spreadsheet_name = "$($spreadsheet_base_name)_$($today.Year)"

		if ($release -like "*otp-sa?15*" -Or $release -like "otp-imx8*"){
			Write-Host "Overriding values for Fermi"
			Import-Module $ScriptDir\modules\fermi_overrides.psm1
			if ($release -like "otp-imx8*"){
				$app_release_label_column = $imx_label_column
			}
			else{
				$app_release_label_column = $sax15m_release_label_column
			}
			if ($approved_fermi_tab_releases -notcontains $spreadsheet_base_name)
			{#temporary fix for Fermi tabs that have not been reviewed yet
				$spreadsheet_name = "$($spreadsheet_name)-DRAFT"
			}
		}
		$spreadsheet = Get-Spreadsheet $workbook $spreadsheet_name
		Write-Host "> Spreadsheet: $spreadsheet_name"

		$last_release_row = Get-SpreadsheetRowsCount $spreadsheet

		Write-Host "---- Looking for build planned for $today ----"
		For ($row = $first_release_row; $row -le $last_release_row; $row++ ){
			$date = (Get-Cell $spreadsheet $row $build_date_column).value2
			$date = $basedate.AddDays($date - 2) #Fix Excel leap year bug

			If (($today) -eq ($date)){
				$otp_label = (Get-Cell $spreadsheet $row $app_release_label_column).text
				Write-Host "Release label found: $otp_label"

				$modem_tag = (Get-Cell $spreadsheet $row $modem_label_column).text
				$index = $modem_tag.LastIndexOf("_")
				$modem_tag = $modem_tag.Substring(0,$index)
				Write-Host "Modem tag found: $modem_tag"

				Break
			}
		}
		$workbook.Close($false)
	}
	Catch {
		Write-Error "The $release_plan can't be opened"
		exit 1
	}
	Finally{
		Close-Excel $excel
	}

} else {
	Write-Warning "$($release) is not defined in $($release_plan)"
}

if ($otp_label -eq $null -Or $otp_label -eq ""){
	Write-Error "otp_label not found for $today"
	#exit 1
}

if ($modem_tag -eq $null -Or $modem_tag -eq ""){
	Write-Error "Modem not found or empty"
	# exit 1
}
Write-Host "------------- End of Execution -------------"
