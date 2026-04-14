#!/usr/bin/python
"""
# ***********************************************************************************************
# *
# *   (c) 2017-2020 Continental Automotive Systems, Inc., all rights reserved
# *
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename:     structures.py
# *
# *   Description:  This python file provides the classes needed to hold jira information
# *
# *   Revision History:
# *
# *   CQ#    Author           Date          Description of Change(s)
# *   -----  -------------    ----------    ------------------------------------------
# *          J. de la Fuente  01/30/2017    initial version based on synergy structures.py
# * TP-2842  E. Bernal        31/03/2017    Affects versions attribute and methods added
# * TP-20682 Julian Garcia    17/07/2018    Adding Domain & Sprint Methods
# ***********************************************************************************************
"""
import time


from cmlib import sanitize, util
from cmlib.sanitize import sanitizeString

SORT_ORDER = {
    'S-Showstopper':4,
    'A-Severe':     3,
    'B-Medium':     2,
    'C-Minor':      1,
    'N/A (for CR)': 0,
    None:           -1
}

class jira_ticket:
    """class for an object to handle jira tickets information related to the cm documentation
    """

    def __init__(self):
        """
        Structure of a Jira Ticket.
        """
        self.iProject = "<void>"
        self.iNumber = "<void>"
        self.iSummary = "<void>"
        self.iFtr = []
        self.iSubtasks = []
        self.iAttachment = []
        self.iStatus = ""
        self.iPriority = None
        self.iSeverity = None
        self.iDomain = None
        self.iSprint = []
        self.iModule = None
        self.iFree_string_a = "<void>"
        self.iFree_string_c = []
        self.iReviewLink = None
        self.iType = None
        self.ft_variant = None
        self.ft_planned_for_release = None
        self.ft_test_int_build_vers = None
        self.iTotal_worklog = util.VOID
        self.iIssuelinks = set()
        self.iCreated = None
        self.iRequesting_project = None
        self.iResponsible_project = None
        self.iSubmitting_team = None
        self.iReported_by_customer = None
        self.iStatusSummary = ""
        self.iFix_versions = []
        self.iAffects_versions = []
        self.iFml = None
        self.iParent = None
        self.iCr = ""
        self.time_spent = 0
        self.updated = None

    def add_issuelinks(self, links=None):
        """ Add IssueLinks to the iIssuelinks

        As part of the pre-processing check for inwardIssue and outwardIssue to sanitize its
        str values to avoid problems with encondings.
        """
        if not isinstance(links, list):
            return

        for link in links:
            for direction in ['inwardIssue', 'outwardIssue']:
                direction_issue = getattr(link, direction, None)
                if direction_issue:
                    fields = (f for f in dir(direction_issue.fields) if not f.startswith('_'))
                    for field in fields:
                        attr = getattr(direction_issue.fields, field)
                        if isinstance(attr, str):
                            attr = attr.encode('ascii', 'ignore').decode('ascii')
                            setattr(direction_issue.fields, field, attr)
            self.iIssuelinks.add(link)

    def add_ftr(self, aFtr):
        """
        add FTR to list
        """
        self.iFtr.append(aFtr)

    def add_subtask(self, aTask):
        """
        adds a task to the CR only if its not already there
        """
        if (aTask not in self.iSubtasks):
            self.iSubtasks.append(aTask)

    def get_project(self):
        """
        returns CR Project
        """
        return self.iProject

    def get_ftr(self):
        """
        returns the list of FTRs
        """
        return self.iFtr

    def get_ftr_str(self):
        '''

        :return:
        '''

        ftr_str = ' '.join([ftr.get_name() for ftr in self.iFtr])

        return ftr_str.strip()

    def get_attachment(self):
        return self.iAttachment

    def get_attachment_str(self):

        attachment_str = ' '.join(attachment for attachment in self.iAttachment)

        return attachment_str

    def get_number(self):
        """
        returns the CR number
        """
        return self.iNumber

    def get_display(self):
        if self.iProject != "<void>":
            return "{0}-{1}".format(self.iProject, self.iNumber)
        else:
            return "{0}".format(self.iNumber)

    def get_summary(self):
        """
        returns the CR Summary string
        """
        return self.iSummary

    def get_subtasks(self):
        """
        returns the list of subtasks related (relation does not come from jira query)
        """
        return self.iSubtasks

    def get_status(self):
        """
        get the status of the CR
        """
        return self.iStatus

    def get_status_summary(self):
        """
        get the status summary of a ticket
        """
        return self.iStatusSummary

    def get_priority(self):
        """
        get the priority of the CR
        """
        return self.iPriority

    def get_severity(self):
        """
        get the severity of the CR
        """
        return self.iSeverity


    def get_domain(self):
        """
        get the Domain of the CR
        """
        return self.iDomain


    def get_sprint(self):
        """
        get the sprint of the CR
        """
        return self.iSprint

    def get_module(self):
        """
        get the module of the CR
        """
        return self.iModule

    def get_free_string_a(self):
        """
        get free_string_a
        """
        return self.iFree_string_a

    def get_free_string_c(self):
        """
        list of free_string_c values
        """
        return self.iFree_string_c

    def get_review_link(self):
        """
        gets the review link
        """
        return self.iReviewLink

    def get_request_type(self):
        """
        get type of request
        """
        return self.iType

    def get_ft_variant(self):
        return self.ft_variant

    def get_ft_planned_for_release(self):
        return self.ft_planned_for_release

    def get_ft_test_int_build_vers(self):
        return self.ft_test_int_build_vers

    def get_issuelinks_srt(self, delimiter=' ,'):
        issuelinks_str = ''
        for issue in self.iIssuelinks:
            summary = issue.get_summary()[0:50]
            display = issue.get_display()
            status = issue.get_status()
            issue_str = "{0} : [{1}] {2}... {3}"
            issuelinks_str += issue_str.format(display, status, summary, delimiter)
        return issuelinks_str

    def get_total_worklog(self):
        return self.iTotal_worklog

    def get_creation_date_struct(self):
        """get the creation struct_time

        :rtype : time.struct_time
        """
        return self.get_date_struct(property='iCreated')

    def get_update_date_struct(self):
        """get the creation struct_time

        :rtype : time.struct_time
        """
        return self.get_date_struct(property='updated')

    def get_date_struct(self, property):
        creation_date = None
        date_format = '%Y-%m-%dT%H:%M:%S.%f%z'
        creation_date_str = sanitize.sanitizeString(getattr(self, property))
        if creation_date_str:
            creation_date = time.strptime(creation_date_str, date_format)
        return creation_date


    def get_creation_date_str(self):
        """get the creation date string

        :return:
        """
        return self.iCreated

    def get_submitting_team(self):
        return self.iSubmitting_team

    def get_requesting_project(self):
        return self.iRequesting_project

    def get_reported_by_customer(self):
        return self.iReported_by_customer

    def get_responsible_project(self):
        return self.iResponsible_project

    def get_customer(self):
        return self.iCustomer if self.iCustomer else "None"

    def get_fix_versions(self):
        """
        list of fixVersion elements
        """
        return self.iFix_versions

    def get_affects_versions(self):
        """
        list of fixVersion elements
        """
        return self.iAffects_versions

    def set_project(self, aProject):
        """
        set the CR Project
        """
        self.iProject = aProject

    def set_platform_module_name(self, aPlatformModule):
        """
        set the Platform Module Name
        """
        self.iPlatform_module_name = aPlatformModule

    def set_number(self, aNumber):
        """
        set the CR number
        """
        self.iNumber = aNumber

    def set_ftr(self, aFtr):
        """
        replace the list of FTRs with a given list
        """
        self.iFtr = aFtr

    def set_attachment(self, aAttachment):
        """
        replace the list of FTRs with a given list
        """
        self.iAttachment = aAttachment

    def set_status(self, aStatus):
        """
        set the status of the CR
        """
        self.iStatus = aStatus

    def set_status_summary(self, aStatusSummary):
        """
        set the status summary of a Defect
        """
        self.iStatusSummary = aStatusSummary

    def set_priority(self, aPriority):
        """
        set the priority of the CR
        """
        self.iPriority = sanitizeString(aPriority)

    def set_severity(self, aSeverity):
        """
        set the severity of the CR
        """
        self.iSeverity = sanitizeString(aSeverity)

    def set_domain(self, aDomain):
        """
        set the domain of the CR
        """
        self.iDomain = aDomain


    def set_module(self, aModule):
        """
        set the module of the CR
        """
        self.iModule = aModule

    def set_summary(self, aSummary):
        """
        sets the CR Summary string
        """
        self.iSummary = aSummary.encode('ascii', 'ignore').decode('ascii')

    def set_sprint(self, asprint: []):
        sprint = []
        if asprint:
            for item in asprint:
                item = item.split(',')
                name = str([x for x in item if 'name' in x]).strip("[]'").split('=')[1]
                sprint.append(name)

        self.iSprint = sprint


    def set_free_string_a(self, aString):
        self.iFree_string_a = aString

    def set_free_string_c(self, aList: []):
        self.iFree_string_c = aList

    def set_review_link(self, aString):
        self.iReviewLink = aString

    def set_request_type(self, aType):
        self.iType = aType

    def set_object_spec(self, aObject_spec):
        self.iObject_spec = aObject_spec

    def set_ft_variant(self, aft_variant):
        self.ft_variant = aft_variant

    def set_ft_planned_for_release(self, aft_planned_for_release):
        self.ft_planned_for_release = aft_planned_for_release

    def set_ft_test_int_build_vers(self, aft_test_int_build_vers):
        self.ft_test_int_build_vers = aft_test_int_build_vers

    def set_total_worklog(self, totalWorkLog):
        self.iTotal_worklog = totalWorkLog

    def set_creation_date(self, aDate):
        self.iCreated = aDate

    def set_update_date(self, date):
        self.updated = date

    def set_submitting_team(self, aTeam):
        self.iSubmitting_team = aTeam

    def set_fix_versions(self, aList: []):
        myList = []
        for aVersion in aList:
            myList.append(aVersion.name)
        self.iFix_versions = myList

    def set_affects_versions(self, aList: []):
        myList = []
        for aVersion in aList:
            myList.append(aVersion.name)
        self.iAffects_versions = myList

    def set_requesting_project(self, aProject):
        self.iRequesting_project = aProject

    def set_reported_by_customer(self, aReported):
        self.iReported_by_customer = aReported

    def determine_customer(self, aInternalProject):
        if self.iSubmitting_team == self.iRequesting_project:
            self.iCustomer = self.iRequesting_project
        elif self.iSubmitting_team == aInternalProject:
            self.iCustomer = self.iRequesting_project
        elif self.iSubmitting_team:
            self.iCustomer = self.iSubmitting_team
        else:
            self.iCustomer = self.iRequesting_project

    def __lt__(self, other):
        return SORT_ORDER[self.get_severity()] < SORT_ORDER[other.get_severity()]

    def __le__(self, other):
        return SORT_ORDER[self.get_severity()] <= SORT_ORDER[other.get_severity()]

    def __eq__(self, other):
        return SORT_ORDER[self.get_severity()] == SORT_ORDER[other.get_severity()]

    def __ne__(self, other):
        return SORT_ORDER[self.get_severity()] != SORT_ORDER[other.get_severity()]

    def __gt__(self, other):
        return SORT_ORDER[self.get_severity()] > SORT_ORDER[other.get_severity()]

    def __ge__(self, other):
        return SORT_ORDER[self.get_severity()] >= SORT_ORDER[other.get_severity()]

    def __str__(self):
        return_value = "Jira_ticket: {0}-{1:2}\tstatus: {2}\t Severity: {3}\t Domain:{4}\t Sprint: {5}\t Summary:{6}"
        return_value = return_value.format(self.iProject, self.iNumber,
                                           self.iStatus, self.iSeverity, self.iDomain, self.iSprint, self.iSummary)

        return return_value

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self
# End class jira_ticket


class JiraLink:
    """class for an object to handle jira links e.g. issuelinks
    """

    def __init__(self):
        """
        """
        self.iKey = None
        self.iRelation = ""
        self.iType = None
        self.iSummary = ""
        self.iPriority = None
        self.iStatus = None
        self.iLinkType = None

    def __str__(self):
        return_value = "JiraLink: {0}:{1}\tsummary: {2}\trelation:{3}"
        return_value = return_value.format(self.iKey, self.iType, self.iSummary, self.iRelation)

        return return_value
