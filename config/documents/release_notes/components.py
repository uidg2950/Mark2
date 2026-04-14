#!/usr/bin/python
# *****************************************************************************
# *
# *  (c) 2016 Continental Automotive Systems, Inc., all rights reserved
# *
# *  All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *  Any reproduction of this material without written consent from
# *  Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename:     components.py
# *
# *   Description:
# *
# *   Revision History:
# *
# *  Ver          Author           Date          Description of Change(s)
# *  -----------  --------------- -------------- ------------------------------
# *               A. Quintero      09/01/2015    init version
# *               A. Quintero      09/03/2015    update for SL6.0_WP09
# *               A. Quintero      09/29/2015    update for SL6.0_WP11
# *               A. Quintero      10/19/2015    update for SL6.0_WP14
# *               A. Quintero      12/04/2015    update for SL6.0_WP20
# *               A. Quintero      12/17/2015    update for SL6.0_WP23
# *               A. Quintero      12/22/2015    update for SL6.0_WP24
# *               A. Quintero      12/22/2015    update SirfV version
# *               A. Quintero      01/20/2016    update for SL6.0_WP25
# *               A. Quintero      02/10/2016    update for SL6.1_WP1
# *  TP_Dpk#3949  A. Quintero      02/10/2016    update for SL6.1_WP2
# *  TP_Dpk#4176  A. Quintero      03/06/2016    update for SL6.3_WP2
# *  TP_Dpk#4814  A. Quintero      03/06/2016    update for SL6.3_WP3
# *  TP_Dpk#5043  A. Quintero      03/06/2016    update for SL6.3_WP3.2
# *  TP_Dpk#5640  A. Quintero      03/06/2016    update for SL6.4 WP01
# *               A. Quintero      17/08/2016    update for SL6.4 WP02
# *               A. Quintero      17/10/2016    update for SL6.3.1 WP02
# *****************************************************************************
end_line=' <br />'

firmware_string = r"""
    "DWL"," C04.05.19.04.SL8RDBT R2833 CNSHZ-ED-XP0031 2016/10/14 13:24:12","","Sierra Wireless",0,"","00000000","00000000"
    {end_line}"FW","FW_754_10_A1_2.SL808FAx","R7.54.10.A1.201610141156.SL8082BTAR","Sierra Wireless",2006864,"101416 11:56","ccec3826","10002020"
    {end_line}"MODEM 3G+","Revision: C04.05.19.04.SL8RDAP R2833 CNSHZ-ED-XP0031 2016/10/14 13:24:12"
    {end_line}"OAT","02.02.00.20161014131952","NAD App Framework Reference Application","Continental Automotive Systems",486720,"101416 13:23","7b4ee321","10700000"
    {end_line}"Open AT Application Framework package","2.54.10.A1.201610141212"
    {end_line}"Open AT OS Package","6.54.1.A1.201602291326"
    {end_line}"Firmware Package","7.54.10.A1.201610141156"
    {end_line}"ExtendedATApplication Library Package","3.1.0.A1.201603041348"
    {end_line}"Internet Library Package","5.58.1.A1.201605100735"
    {end_line}"eCall Library Package","1.3.4.201512300930"
""".format(end_line=end_line)

plus_components = {
    'ds':{
        'baseline':'Developer Studio 3.4 Copyright (c) Sierra Wireless 2009-2015',
        'component': 'Developer Studio"',
        'version': '3.4.0.201506101227'
    },
    'sirfv':{
        'baseline':r'',
        'component': 'SirfV',
        'version':'5xp__5.6.3-P4.RVCT_eLNA_OSP_NDBG+5xpt_5.6.3-P4.KCC'
    },
    'afw':{
        'baseline': firmware_string,
        'component': 'NAD FIRMWARE',
        'version':'SL6.4 WP2'
    }
}
