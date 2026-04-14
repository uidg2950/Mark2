#!/usr/bin/python
# *****************************************************************************
# *
# *  (c) 2022-2025 Continental Automotive Systems, Inc., all rights reserved
# *
# *  All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *  Any reproduction of this material without written consent from
# *  Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: conmod_artifacts_notification.py
# *
# *   Description:  Internal notification. Mainly focused on testing team.
# *
# *
# *****************************************************************************

import sys
import os
import glob
import re

# This is requiered due python 3 doesn't support relative references
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from cmlib.html_util import create_html_table, create_list_of_changes, create_html_link_entry
from cmlib import notification, util, artifactory
from cmlib.notification import ReportNotification

# Arguments
baseline_name = sys.argv[1]     # otp-sa515m-thick-3.1.7.6.3
release_id = sys.argv[2]        # conmod-sa515m-3.y
send_to = sys.argv[3]           # emails

# CAT-9683: get changelog from release share
release_path = "/u01/app/jenkins/releases/{}/{}-devel".format(release_id, baseline_name)

# Directories
try:
    buidir = os.environ['BUIDIR']
    scrdir = os.environ['SCRDIR']
    docdir = os.environ['DOCDIR']
except KeyError:
    raise BaseException("ERROR: environment not set")

## Variables
# Sender -  Jenkins by default
build_user = notification.email_defaults['build_user']
build_user_email = notification.email_defaults['build_user_email']
## Notification list - conmod_internals
default_list_file = "{}/../templates/notification/conmod_artifacts".format(currentdir)
# Lists
default_list = []
artifacts_resume = []
content = []

# Subject Template
subject = "[{}] Artifacts Notification".format(baseline_name)

## Creating Notification list
with open(default_list_file) as f:
    for line in f:
        line = line.strip()
        if '#' not in line:
            default_list.append(line)
# To string
default_list = ','.join(default_list)
# Concatenation
send_to = default_list + ',' + send_to

## Artifacts Verification
artifacts = {
    # Deerpark share
    'Swl Bundle' : "swl-test",
    # Artifactory
    'Bundle Zip' : "tp_sdk.*\.zip",
}

# Listing artifacts available
for label,pattern in sorted(artifacts.items()):
    util.info("Checking Artifactory...")
    util.info("Label: {}, pattern: {}".format(label,pattern))

    raw_folder_content = artifactory.get_metainfo(baseline_name, release_id)
    re_pattern = re.compile(pattern)

    for index in range(len(raw_folder_content["children"])):
        target_file = None
        cross='x'
        if label == "Bundle Zip":
            if raw_folder_content["children"][index]["uri"][1:] == "otc":
                raw_sub_folder_content = artifactory.get_metainfo(baseline_name + "/otc", release_id)
                for index in range(len(raw_sub_folder_content["children"])):
                    if re_pattern.match(raw_sub_folder_content["children"][index]["uri"][1:]):
                        target_file = raw_sub_folder_content["uri"].replace("/api/storage", "") + raw_sub_folder_content["children"][index]["uri"]
                        break
            elif raw_folder_content["children"][index]["uri"][1:] == "sdk":
                raw_sub_folder_content = artifactory.get_metainfo(baseline_name + "/sdk", release_id)
                for index in range(len(raw_sub_folder_content["children"])):
                    if re_pattern.match(raw_sub_folder_content["children"][index]["uri"][1:]):
                        target_file = raw_sub_folder_content["uri"].replace("/api/storage", "") + raw_sub_folder_content["children"][index]["uri"]
                        break
        else:
            if re_pattern.match(raw_folder_content["children"][index]["uri"][1:]):
                target_file = raw_folder_content["uri"].replace("/api/storage", "") + raw_folder_content["children"][index]["uri"]

        if target_file == None:
            cross=''

        if cross == "x":
            # list only found files
            output_resume = (cross, label, target_file)
            artifacts_resume.append(output_resume)

table = "<br><p>No new changes!</p><br>"
changes, changes_since = create_list_of_changes(release_path)
if len(changes) > 0:
    table = "<p><b>List of changes {}:</b></p>".format(changes_since)
    table += create_html_table(changes)

## Body template
body = '''
<p>Hello,</p>
<p>The following artifacts were generated for {} baseline:</p>
<p><b>Artifacts:</b></p>

'''.format(baseline_name)

# Signature template
signature = '''
<br>
<p>Regards,</p>
_______________________________________________________
<br>Best Regards / Mit freundlichen Gruessen / Saludos cordiales\n
<br>Sent by: Jenkins Automation User\n
<br>Please do not reply to this user, contact ConMod Team instead.
'''

# File name
conmod_notification = "internal_notification.html"

# Creating email notification
final_notification= '''<html>
<body>
{body}
{table}
{signature}
</body>
</html>
'''.format(body=body,table=table,signature=signature)

# Writing email notification file
with open (conmod_notification,"w") as result:
    result.writelines(final_notification)

# Adding Highlight(s)
with open (conmod_notification, "r+") as file:
    for line in file:
        content.append(line)
        if "Artifacts:" in line:
            next_line= file.readline()
            if next_line.strip() == "":                                                                                 # If the next line is empty
                for resume in artifacts_resume:
                    link = create_html_link_entry(str(resume[2]))
                    content.append("<p>  ["+str(resume[0])+"] "+str(resume[1])+" -> "+link+"</p>\n")
                content.append(next_line)                                                                             # Adding one space
    file.seek(0)
    file.truncate()
    file.write("\n".join(content))

# Sending notification
notification = ReportNotification(build_user, build_user_email, send_to, conmod_notification , subject)
print(notification)
notification.send()
