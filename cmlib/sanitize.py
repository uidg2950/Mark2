#!/usr/bin/python
# *****************************************************************************
# *
# *  (c) 2016 Continental Automotive Systems, Inc., all rights reserved
# *
# *  All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *  Any reproduction of this material without written consent from
# *  Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename:
# *
# *   Revision History:
# *
# *****************************************************************************
import re
import os

import cmlib


def sanitizeString(input_text):
    """sanitize
    :rtype : str
    """
    if input_text is None:
        return_value = None
    else:
        return_value = re.sub("\s+", " ", input_text)
        return_value = return_value.replace("\t", "")
        return_value = return_value.strip()
    return return_value


def sanitizePath(input_text) -> str:
    """

    :rtype : str
    """
    return_value = ""
    if input_text is not None:
        return_value = os.path.normpath(input_text)
        return_value = os.path.normcase(return_value)
        return_value = return_value.strip()
    return return_value


def sanitizeEmail(email, domain) -> str:
    """
    """
    email = sanitizeString(email)
    domain = sanitizeString(domain)
    if re.match(r'[^@]+@[^@]+\.[^@]+', email):
        return email
    else:
        return email + "@" + domain


def sanitize_ticket(ticket_id):
    """

    :param ticket_id:
    :return:
    """
    ticket_name = ticket_id.strip()
    ticket_name = re.sub('[^a-zA-Z0-9#_\-,\s]+', '', ticket_name)
    ticket_name = re.split(r'[\s,]', ticket_name)

    return ticket_name


def sanitize_dependency(dependency):
    """

    :param dependency:
    :return:
    """
    return_value = []

    dependency_name = dependency.strip()
    dependency_name = re.sub('[^a-zA-Z0-9#,\s]+', '', dependency_name)
    dependency_name = re.split(r'[\s,]', dependency_name)
    dependency_name = [x for x in dependency_name if x != '']

    for dependency_item in dependency_name:
        # FIXME: prone to bugs if a hash consist of all digits
        if not re.match('^(I[0-9a-fA-F]{40}|\d+)$', dependency_item):
            warning('Malformed Change-Id {}'.format(dependency_item))
        else:
            return_value.append(dependency_item)

    return return_value
