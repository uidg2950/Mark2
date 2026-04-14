#!/usr/bin/python
"""
# *****************************************************************************
# *
# * (c) 2021 Continental Automotive Systems, Inc., all rights reserved
# *
# * All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# * Any reproduction of this material without written consent from
# * Continental Automotive Systems, Inc. is strictly forbidden.
# *
# * Filename:     change_report_csv_format.py
# *
# * Description: weekly changes based on database information
# *
# ************** ***************************************************************
"""
import os
import re
import sys
import shutil
import requests
from datetime import datetime

# This is requiered due python 3 doesn't support relative references
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from cmlib import util

# Environment
try:
    buidir = os.environ['BUIDIR']
    scrdir = os.environ['SCRDIR']
    docdir = os.environ['DOCDIR']
except KeyError:
    raise BaseException("ERROR: environment not set")

# Parameters
workspace = sys.argv[1]
new_baseline = sys.argv[2]
old_baseline = sys.argv[3]

## Variables
log_filename = "change-summary.txt"
# csv filename
csv_default = "change-summary.csv"
nbi=new_baseline.split('-')[-1]
obi=old_baseline.split('-')[-1]
csv_filename=obi+'_to_'+nbi+'_'+'ticket-list.csv'
# Absolute paths
change_txt = os.path.join(workspace,log_filename)                          # Source
change_log_csv = os.path.join(workspace,csv_filename)                      # Output
change_logs_docdir = os.path.join(docdir, 'sdk_packages/change_logs')

############ Main Execution ############
util.header("Re-formatting integrated changes report")

util.header2("Extracting changes information from {}".format(change_txt))
try:
	f = open(change_txt)
except FileNotFoundError:
	sys.exit("Error: {} not found".format(change_txt))
finally:
    f.close()

# Final content list
csv_content=[]

# Reading change-summary file
with open(change_txt) as file:
    for line in file:
        if 'Repo:' in line:
            repo=line.split(':')[1].strip()
        elif '|' in line:
            line=line.split('|')
            commit=line[0]
            author=line[1]
            adate=line[2]
            if ':' in line[3]:
                ticket=line[3].split(':')[0]
                check_format=re.split(r'(\W+)',ticket.strip())      # Ticket format verification [A-Z]-[0-9]+
                is_ticket=re.match(r'^\d+',check_format[-1])
                if is_ticket is not None:
                    headline=line[3].replace(ticket+':','')         # Really?
                else:
                     ticket="-"
                     headline=line[3]
            else:
                ticket="-"
                headline=line[3]
            csv_content.append('{}|{}|{}|{}|{}|{}'.format(repo,commit,author,adate,ticket,headline))
            print('{}|{}|{}|{}|{}|{}'.format(repo,commit,author,adate,ticket,headline))

util.header2("Generating Change log file in CSV format")

# Writing csv file
columns="Repo|Commit|Author|Date|Ticket|Headline"
with open (change_log_csv,"w") as csv:
    csv.writelines(columns+'\n')
    for line_content in csv_content:
        csv.writelines(line_content)
csv.close()

# Creating output file
util.header2("output file")
print("Copying from: {} -> {}".format(change_log_csv,change_logs_docdir))
shutil.copy(change_log_csv,change_logs_docdir)
print("Output file path: {}".format(change_logs_docdir))
