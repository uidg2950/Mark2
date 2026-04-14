<#
.Synopsis
    Functions to be used for Excel Files operations
#>
function Open-Excel
{
    Param
	(
	)
	Begin
	{
		if ($psculture -ne "en-US")
		{
			Write-Host "Changing Current Culture to en-US"
			$culture = [System.Globalization.CultureInfo]::GetCultureInfo('en-US')
			[threading.thread]::CurrentThread.CurrentUICulture = $culture
			[threading.thread]::CurrentThread.CurrentCulture = $culture
		}
		$excel = New-Object -ComObject "Excel.Application"
		return $excel
	}
}

function Close-Excel
{
    Param
    (
		[Parameter(Mandatory=$true,  Position=0)] $excel
    )
	Begin
	{
		Write-Host "Closing Excel Application "
		$excel.Quit()

		#Release Excel objects
		[System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null

		[System.GC]::Collect()
		[System.GC]::WaitForPendingFinalizers()
	}
}

function Get-Workbook
{
    Param
    (
		[Parameter(Mandatory=$true,  Position=0)] $excel,
		[Parameter(Mandatory=$true,  Position=1)][String] $file_name
    )

	Begin
	{
		$missing = [System.Type]::Missing
		try
		{
			$workbook = $excel.Workbooks.Open($file_name, $missing, $true, $missing, $missing, #ReadOnly,
						$missing, $true) #IgnoreReadOnlyRecommended
		}
		Catch {
			Write-Error "The $file_name can't be opened"
			$workbook = $null
		}
		return $workbook
	}
}

function Get-Spreadsheet
{
    Param
    (
		[Parameter(Mandatory=$true,  Position=0)] $workbook,
		[Parameter(Mandatory=$true,  Position=1)][String] $spreadsheet_name
    )

	Begin
	{
		try
		{
			$spreadsheet = $workbook.Sheets.Item($spreadsheet_name)
		}
		Catch {
			Write-Error "Spreadsheet $spreadsheet_name could not be opened!"
			$spreadsheet = $null
		}
		return $spreadsheet
	}
}

function Get-SpreadsheetRowsCount
{
    Param
    (
		[Parameter(Mandatory=$true,  Position=0)] $spreadsheet
    )

	Begin
	{
		try
		{
			$count = $spreadsheet.UsedRange.Rows.Count
		}
		Catch {
			Write-Error "Could not get rows count!"
			$count = 0
		}
		return $count
	}
}

function Get-Cell
{
    Param
    (
		[Parameter(Mandatory=$true,  Position=0)] $spreadsheet,
		[Parameter(Mandatory=$true,  Position=1)][Int] $row,
		[Parameter(Mandatory=$true,  Position=2)][Int] $col
    )

	Begin
	{
		try
		{
			$value = $spreadsheet.Cells.Item($row, $col)
		}
		Catch {
			Write-Error "Could not get item!"
			$value = $null
		}
		return $value
	}
}

function Get-CellHyperlinks
{
    Param
    (
		[Parameter(Mandatory=$true,  Position=0)] $spreadsheet,
		[Parameter(Mandatory=$true,  Position=1)][Int] $row,
		[Parameter(Mandatory=$true,  Position=2)][Int] $col
    )

	Begin
	{
		$hyperlinks = @()
		try
		{
			$hyperlink = $spreadsheet.Cells.Item($row, $col).hyperlinks
			foreach ($link in $hyperlink){
				$hyperlinks += $link
				<# Write-Host "Address: $($link.Address)"
				Write-Host "Type: $($link.Type)"
				Write-Host "Subaddress: $($link.Subaddress)"
				Write-Host "ScreenTip: $($link.ScreenTip)"
				Write-Host "Name: $($link.Name)"
				Write-Host "EmailSubject: $($link.EmailSubject)"
				#$link | gm | Write-Host #>
			}
		}
		Catch {
			Write-Error "Could not get item hyperlinks!"
		}
		return $hyperlinks
	}
}
