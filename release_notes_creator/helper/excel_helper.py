def check_sheetname_in_excel(wb, sheetname, file):
    """
    The check_sheetname_in_excel function checks if the sheetname is in the Excel file.
    If it's not, then an exception is raised.

    :param wb: Access the workbook
    :param sheetname: Check if the sheetname is in the excel file
    :param file: Specify the file name of the excel file
    :return: None
    """
    sheetnames = wb.sheetnames
    if sheetname not in sheetnames:
        raise Exception("{} not in Excel file => {}".format(sheetname, file))
