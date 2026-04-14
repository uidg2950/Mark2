# -*- coding: utf-8 -*-
#!/usr/bin/python
# *****************************************************************************
# *
# *  (c) 2023 Continental Automotive Systems, Inc., all rights reserved
# *
# *  All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *  Any reproduction of this material without written consent from
# *  Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: conmod_email_generator.py
# *
# *   Description:  email notification to eSo.
# *
# *
# *****************************************************************************

import sys
import os

# This is requiered due python 3 doesn't support relative references
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from cmlib.notification import ReportNotification, email_defaults
from cmlib import util

baseline_name = sys.argv[1]     # otp-sa515m-thick-3.1.7.6.3
delivery_type = sys.argv[2]     # Engineering Drop / Continental Release / Pre Release
url = sys.argv[3]               # ETF > https://etf.esolutions.de/user/?etf_id=<ID>
addendum =  sys.argv[4]         # Addendum - Observations or Highlights
comments =  sys.argv [5]        # Comments
send_to = sys.argv[6]           # emails

# Sender -  Jenkins by default
build_user = email_defaults['build_user']
build_user_email = email_defaults['build_user_email']

# Notification list
default_list_file = "{}/../templates/notification/conmod".format(currentdir)
default_list = []

with open(default_list_file) as f:
    for line in f:
        line = line.strip()
        if '#' not in line:
            default_list.append(line)

## To string
default_list = ','.join(default_list)
## Concatenation
send_to = default_list + ',' + send_to

# Headline
print("\nBuilding {} Notification email\n".format(delivery_type))

# Local variables
conmod_descriptors = "[CONMOD][main][AU][ALL][UNIT]"

# Version id
version_id = baseline_name.split('-')[-1]

# Subject Template
subject = "[{}][Conti_SDK][{}]{}[{} Notification]".format(baseline_name, version_id, conmod_descriptors, delivery_type)

# Email File
conmod_email = "email_to_eso.html"

email_file = open(conmod_email,"w")
email_file.write('''<html>
<body>
<p>Hello,</p>
<p>New [Conti_SDK] is available on ETF:</p>
<p id="p1"><strong>[Conti_SDK]</strong>&nbsp;&nbsp;&nbsp;&nbsp;[<a href="{}">{}</a>]</p>
<p>It has to be used for:</p>
<p>&nbsp;&nbsp;&nbsp;&nbsp;*conMod_esoSDK* [Version]{}[No additional information]</p>
<p>branch: [main]</p>
<p>Regards,</p>
<p style="margin : 0; padding-top:0;">_______________________________________________________</p>
<p style="margin : 0; padding-top:0;">Best Regards / Mit freundlichen Gruessen / Saludos cordiales</p>
<p style="margin : 0; padding-top:0;">Sent by: Jenkins Automation User</p>
<p style="margin : 0; padding-top:0;">Please do not reply to this user, contact ConMod Team instead.</p>
</html>'''.format(url, url, conmod_descriptors))
email_file.close()

# Adding Highlight(s)
if addendum != "-":
    # Comments to be added
    if comments != "-":
        comments = comments.split(";")
        content = []
        # Writing email notification file
        with open (conmod_email,"r+") as email_file:
            for line in email_file:
                content.append(line)
                if "branch: [main]" in line:
                    next_line= email_file.readline()
                    headline_of_comments='<p style="margin : 0; padding-top:0;">&nbsp;&nbsp;&nbsp;&nbsp;{}:</p>'.format(addendum)
                    content.append(headline_of_comments)
                    content.append("<ul>")
                    for highlight in comments:
                        content.append("<li>{}</li>".format(highlight.lstrip()))
                    content.append("</ul>")
            email_file.seek(0)
            email_file.truncate()
            email_file.write("".join(content))

# Sending notification
notification = ReportNotification(build_user, build_user_email, send_to, conmod_email , subject)
print(notification)
notification.send()
