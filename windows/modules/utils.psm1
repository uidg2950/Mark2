<#
.Synopsis
    Common use Functions and variables
#>

$telematics_sharepoint = "https://continental.sharepoint.com/teams/ext_10001455"
$telematics_sharedir = "\\dpfs01p1.auto.contiwan.com\didt6639"
$telematics_docdir = "$telematics_sharedir\Jenkins\Documents"
$telematics_reldir = "$telematics_sharedir\TELEMATICS_PLATFORM\TEST_SW"
#$release_plan = "$($telematics_sharepoint)/Project%20Documents/Project%20Management/Schedule/TP_SI_Baseline_ReleasePlan.xlsm"
$release_plan = "$($telematics_docdir)\Release_Plan\TP_SI_Baseline_ReleasePlan.xlsm"

# Release Plan Columns mapping
$week_column=1
$platform_label_column=2
$build_date_column=3
$test_report_date_column=4
$rrr_date_column=5
$release_to_pds_column=6
$otp_framework_label_column=7
$otp_hal_label_column=8
$app_release_label_column=9
$modem_label_column=10
$tvip_label_column=11
$otp_host_label_column=12
$qualcomm_baseline_column=13
$requirements_baseline_column=14
$architecture_baseline_column=15
$svn_number=16
$reqs_arch_baseline_date_column=17
$metrics_due_date_column=18
$first_release_row=2
Set-Variable blue -option Constant -value 15773696 #Released
Set-Variable purple -option Constant -value 14381296 #Engineering Release

#Dates
$basedate = '01/01/1900' | Get-Date
$today = Get-Date | Select -ExpandProperty Date

$variant = @{
			   "conmod-sa515m-3.y" = "TP_FERMI_5G";
			   "conmod-sa515m-cl46-3.y" = "TP_FERMI_5G";
			   "otp-1.y" = "TP_HIGH";
			   "otp-mdm9x28-2.y" = "TP_BELL";
			   "otp-mdm9x28-2.50.2.y" = "TP_BELL_CPL3";
			   "otp-mdm9x28-2.64.1.y" = "TP_BELL_CPL4";
			   "otp-mdm9x28-2.69.0.y" = "TP_BELL_CPL5";
			   "otp-mdm9x50-2.y" = "TP_WATSON";
			   "otp-mdm9x50-sop1-2.y" = "TP_WATSON_SOP1";
			   "otp-mdm9x50-sop-2.y" = "TP_WATSON_SOP";
			   "otp-framework-2.y" = "TP_FRAMEWORK";
			   "otp-sa415m-2.y" = "TP_FERMI_VUC_4.5G";
			   "otp-sa415m-3.y" = "TP_FERMI_AP_4.5G";
			   "otp-sa515m-3.y" = "TP_FERMI_AP_5G";
			   "otp-sa515m-le-2-1-3.y" = "TP_FERMI_LE2.1_AP_5G";
			   "otp-imx8-3.y" = "TP_FERMI_AP_4.5G";
			   "otp-imx8-sa515m-3.y" = "TP_FERMI_AP_5G";
			   "otp-sa515m-thick-le-2-1-3.y" = "TP_FERMI_LE2.1_5G";
			}
$platform = @{
			   "conmod-sa515m-3.y" = "CONMOD_5_G";
			   "conmod-sa515m-cl46-3.y" = "CONMOD_5_G";
			   "otp-1.y" = "High";
			   "otp-mdm9x28-2.y" = "BELL";
			   "otp-mdm9x28-2.50.2.y" = "BELL";
			   "otp-mdm9x28-2.64.1.y" = "BELL";
			   "otp-mdm9x28-2.69.0.y" = "BELL";
			   "otp-mdm9x50-2.y" = "WATSON";
			   "otp-mdm9x50-sop1-2.y" = "WATSON";
			   "otp-mdm9x50-sop-2.y" = "WATSON";
			   "otp-framework-2.y" = "FRAMEWORK";
			   "otp-sa415m-2.y" = "FERMI_VUC_4_5_G";
			   "otp-sa415m-3.y" = "FERMI_AP_4_5_G";
			   "otp-sa515m-3.y" = "FERMI_AP_5_G";
			   "otp-sa515m-le-2-1-3.y" = "FERMI_LE2.1_AP_5_G";
			   "otp-sa515m-thick-le-2-1-3.y" = "FERMI_LE2.1_5_G";
			}

$approved_fermi_tab_releases = "TP_FERMI_AP_4.5G", "TP_FERMI_AP_5G", "TP_FERMI_5G", "TP_FERMI_LE2.1_AP_5G", "TP_FERMI_LE2.1_5G"

$global:width = 80
$global:width2 = 60

function Conti_header
{
	Param
	(
	)
	Write-Host "                       NHBBEHmHEBBEN\n\" -foregroundcolor yellow -backgroundcolor Black
	Write-Host "                 NXPEBB B   B  B   EEBBBBk\n\" -foregroundcolor yellow -backgroundcolor Black
	Write-Host "             NBBk XKB   BP EBkKB  BK 0   B EBK\n\" -foregroundcolor yellow -backgroundcolor Black
	Write-Host "           BBK  EX   B   B  M 0E  B Nk BBB mP BMK\n\" -foregroundcolor yellow -backgroundcolor Black
	Write-Host "        ,BM   BBMBB  HBBBBKmw mkEBBKBBBw BBX  BBPBB\n\" -foregroundcolor yellow -backgroundcolor Black
	Write-Host "       B BPkBB 0  EBP       K          BBB  BB     BB\n\" -foregroundcolor yellow -backgroundcolor Black
	Write-Host "     HB  B0  BMNBk    MNHBBBBBB           BBN wKBBBw B\n\" -foregroundcolor yellow -backgroundcolor Black
	Write-Host "    BkNK  m  mB       BBBKBXkHBB            XB  B     B\n\" -foregroundcolor yellow -backgroundcolor Black
	Write-Host "   Mk B   BkBk            kXkXBK              B0 BBBKN B\n\" -foregroundcolor yellow -backgroundcolor Black
	Write-Host "   B   KBB P,          ,BBBkkPP                B B      B\n\" -foregroundcolor yellow -backgroundcolor Black
	Write-Host "  mB       B    XBBB  BBKXkkkP                  B       B\n\" -foregroundcolor yellow -backgroundcolor Black
	Write-Host "  Bm  0   XB KBBN  MBBBHkkkkkHBBBBBBBBBBBBBBBB  B   m   B\n\" -foregroundcolor yellow -backgroundcolor Black
	Write-Host "  Bk  BB  MB X   BBkBBBBBBBBBBBBBPkkkkkBB  KBB  B   BM  B\n\" -foregroundcolor yellow -backgroundcolor Black
	Write-Host "  wB       B   BBP         0kPmw BHEKEXB  BBB   B       B\n\" -foregroundcolor yellow -backgroundcolor Black
	Write-Host "   B     mBMP  BX                BBP PBB  BBB  B KBBB  mB\n\" -foregroundcolor yellow -backgroundcolor Black
	Write-Host "    B BBBK, BB                     BB  BBX    B Pm   B B\n\" -foregroundcolor yellow -backgroundcolor Black
	Write-Host "    BB    BB  B                 mBB   BN    KP XX  PB B\n\" -foregroundcolor yellow -backgroundcolor Black
	Write-Host "     XB,XB PNX BKB 0BBBBBBBBBBBBBBkBBBE, MKB B   BK ,B\n\" -foregroundcolor yellow -backgroundcolor Black
	Write-Host "       BX    BB  ,XPH                 ,BK  B  BBHBmBB\n\" -foregroundcolor yellow -backgroundcolor Black
	Write-Host "         BBkBm  BBM B PBXKBKPEKBBBBBBB  mBEHBB   Bm\n\" -foregroundcolor yellow -backgroundcolor Black
	Write-Host "           XHK K  BB  k PB  B  B  B   B   P  0BBB\n\" -foregroundcolor yellow -backgroundcolor Black
	Write-Host "              BBBHE  w, B  BBBPB  B   BBBXMBBk\n\" -foregroundcolor yellow -backgroundcolor Black
	Write-Host "                  MBBBBBB  0,  B  HBBBHPE,\n\" -foregroundcolor yellow -backgroundcolor Black
	Write-Host "                         mKELKEPKE, \n\n" -foregroundcolor yellow -backgroundcolor Black
}

function divLine
{
    Param
	(
		[Parameter(Mandatory=$false)] $mychar = "="
	)
    Write-Host ($mychar * $global:width)
}
function header1
{
    Param
    (
        [String] $message
    )
    $mytext = $message.ToUpper()
    $message_length = $message.length
    [int]$offset = ($global:width - $message_length) / 2
	if ($offset -lt 0){
		$offset = 0
	}
    #Write-Verbose "Width: $global:width length: $message_length Offset: $offset"
    Write-Host "`n"
    divLine
    Write-Host (" " * $offset)$mytext
    divLine
    Write-Host "`n"
}

function header2
{
    Param
    (
        [String] $message
    )
    $mytext = $message
    $message_length = $message.length
    [int]$offset = ($global:width2 - $message_length) / 2
	if ($offset -lt 0){
		$offset = 0
	}
    Write-Host "`n"
    divLine("-")
    Write-Host (" " * $offset)$mytext
    divLine("-")
    Write-Host "`n"
}

function Get-UpperUrlDir
{
    Param
    (
        [String] $dir
    )
	Begin
	{
		$remove_dirs = 1
		$dir_l = $dir.split("/")
		if ($dir_l[$dir_l.length -1] -eq ""){
			$remove_dirs += 1
		}
		$upper_dir = $dir_l[0..($dir_l.length - $remove_dirs -1)] -join "/"
		return $upper_dir
	}
}

function New-Dir
{
    Param
	(
		[Parameter(Mandatory=$true,  Position=0)] $Path,
		[Parameter(Mandatory=$true,  Position=1)] $dir_name
	)
	Begin
	{
	    $new_path = Join-Path -Path $Path -ChildPath $dir_name
		Write-Host("Creating $($new_path)!")
		New-Item -ItemType Directory -Force -Path $new_path
	}
}

function Move-DirFile
{
	Param
	(
		[Parameter(Mandatory=$true,  Position=0)] [string] $source_item,
		[Parameter(Mandatory=$true,  Position=1)] [string] $target_item,
		[Parameter(Mandatory=$false, Position=2)] $recurse = $false
	)
	Begin
	{
	    if(!(test-path $source_item))
		{
			Write-Error("$($source_item) could not be found!")
			exit 1
		}
		Write-Host("Transferring $($source_item) to $($target_item)")
		If ($recurse) {
			Copy-Item -Path $source_item -Destination $target_item -Recurse
		}
		else {
			Copy-Item -Path $source_item -Destination $target_item
		}
	}
}

Function Get-FileHashTP
{
    Param
    (
	    [Parameter(Mandatory=$true,  Position=0)] [String] $FileName,
	    [Parameter(Mandatory=$false, Position=1)] [String] $algorithm = "SHA256"
    )
    Begin
    {
	    $FileStream = New-Object System.IO.FileStream($FileName,[System.IO.FileMode]::Open)
	    $StringBuilder = New-Object System.Text.StringBuilder
	    [System.Security.Cryptography.HashAlgorithm]::Create($algorithm).ComputeHash($FileStream)|%{[Void]$StringBuilder.Append($_.ToString("x2"))}
	    $FileStream.Close()
	    $hash = $StringBuilder.ToString()

	    $retVal = New-Object -TypeName psobject -Property @{
	        Algorithm = $algorithm.ToUpperInvariant()
	        Hash = $hash
	    }

	    $retVal
    }
}

Function Get-ElementsText
{
    Param
	(    [Parameter(Mandatory=$true,  Position=0)] $elements,
         [Parameter(Mandatory=$false, Position=1)] $prefix = ""
	)
	$retVal = ""
	foreach($element in $elements){
		if ($retVal -eq "") {
			$retVal = "$($prefix) $element"
		} else {
			$retVal += "`n$($prefix) $element"
		}
	}
	$retVal
}

Function Remove-DirFile
{
    Param
	(    [Parameter(Mandatory=$true,  Position=0)] $item,
         [Parameter(Mandatory=$true,  Position=1)] $errors,
		 [Parameter(Mandatory=$false, Position=2)] $recurse = $false
	)

    $params = @{
		Path = $item
		Force = $true
		Recurse = $recurse
	}
	Write-Host("Removing $($item)!")
	Try {
		Remove-Item @params
	}
	Catch{
		Write-Error("$($item) cannot be removed!")
		$errors = $true
	}
	return $errors
}

Export-ModuleMember -Function *
Export-ModuleMember -Variable release_plan, basedate, today, variant, platform, approved_fermi_tab_releases
Export-ModuleMember -Variable first_release_row, blue, purple
# Columns mapping
Export-ModuleMember -Variable week_column, platform_label_column, build_date_column
Export-ModuleMember -Variable release_to_pds_column, test_report_date_column, rrr_date_column
Export-ModuleMember -Variable otp_framework_label_column, otp_hal_label_column
Export-ModuleMember -Variable app_release_label_column, modem_label_column
Export-ModuleMember -Variable tvip_label_column, otp_host_label_column
Export-ModuleMember -Variable qualcomm_baseline_column, requirements_baseline_column
Export-ModuleMember -Variable architecture_baseline_column, reqs_arch_baseline_date_column
Export-ModuleMember -Variable metrics_due_date_column
Export-ModuleMember -Variable telematics_sharepoint
Export-ModuleMember -Variable telematics_docdir, telematics_reldir
