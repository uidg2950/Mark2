#!/usr/bin/python
# *****************************************************************************
# *
# *  (c) 2022 Continental Automotive Systems, Inc., all rights reserved
# *
# *  All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *  Any reproduction of this material without written consent from
# *  Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: cmlib/util.py
# *
# *   Revision History:
# *
# *****************************************************************************
import re
import os

width = 120
width2 = 80
average_pr_hrs = 1.5  # Average hrs a day spent solving + testing a PR
end_line = '\n'
NBSP = '&nbsp;'
MAX_VERSION_SPLIT = 4

# Gerrit review constants
BLANK = ' '
CHECK = 'x'
NOT_RUN = '-'  # pending approval
NO_SCORE = '0'
MINUS_ONE = '-1'
MINUS_TWO = '-2'
PLUS_ONE = '+1'
SW_INT_REQ = 'SW Integration requested'
TAB = '\t\t'
UNAVAILABLE = '-'
VOID = '<void>'
# Magical paths
COMMIT_MSG_PATH = '/COMMIT_MSG'
MERGE_LIST_PATH = '/MERGE_LIST'
# Test results
NOT_AVAILABLE = 'Not Available'
NOT_MANDATORY = 'Not Mandatory'
NULL = None
FAILED = -1
UNREQUIRED = -2

# Exclusion patterns
FUNCTIONAL_USERS = [
    'uidg4627',  # Telematics Functional Account
    'uidr9216',  # Connectivity Functional Account
]

def header(message) -> None:
    """

    :rtype : None
    """
    message_length = len(message)
    offset = (width - message_length) // 2
    print()
    print('#' * width)
    print(' ' * offset + message.upper())
    print('#' * width)
    print(flush=True)


def header2(message) -> None:
    message_length = len(message)
    offset = (width2 - message_length) // 2
    print()
    print('-' * width2)
    print(' ' * offset + message.upper())
    print('-' * width2)
    print(flush=True)


def header3(message) -> None:
    message_length = len(message)
    offset = (width2 - message_length) // 2
    print(flush=True)
    print('-' * offset + message.upper() + '-' * offset)


def warning(message, error=False):
    head = 'ERROR' if error else 'WARNING'
    message_length = len(message)
    offset = (width - message_length) // 2
    print()
    print('+' * width)
    print(' ' * (offset - 8) + "{}: ".format(head) + message.upper())
    print('+' * width)
    print()


def debug(message):
    print('DEBUG: ', message, flush=True)

def info(message):
    print('INFO: ', message, flush=True)