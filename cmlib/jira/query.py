#!/usr/bin/python
"""
# ******************************************************************************
# *
# *   (c) 2025 Aumovio , all rights reserved
# *
# *   All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *   Any reproduction of this material without written consent from
# *   Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename:    query.py
# *
# *   Description: This file contains the class for accessing Jira issues
# *                ( Conmod Project Version )
# *                This script requires JIRA python module.
# *
# ****************************************************************************
"""
import getpass
import os

from jira import JIRA, JIRAError
from cmlib.jira.util import jira_server, jira_pat, customer_projects
from cmlib.jira.util import invalid_types, readTicket, readLink
from cmlib.jira.util import get_platform_from_release, get_excluded_components
from cmlib.jira.structures import jira_ticket

class Query:
    """ """

    def __init__(self):

        self._jira_pat = jira_pat
        headers = JIRA.DEFAULT_OPTIONS["headers"].copy()
        headers["Authorization"] = "Bearer {}".format(self._jira_pat)

        try:
            self.client = JIRA(server=jira_server, options={"headers": headers})
            self.field_map = {field['name']: field['id'] for field in self.client.fields()}
        except JIRAError as jira_error:
            print("ERROR {}: {}".format(jira_error.status_code, jira_error.url))
            self.client = None

    def _update_ticket(self, ticket, fields):
        try:
            status_name = ticket.fields.status.name
            if status_name == 'Closed':
              print('Issue Closed. Proceed with Transition')
              transitions = self.client.transitions(ticket)
              edit_id = next(t for t in transitions if t['name'] == 'Edit Fields')['id']
              self.client.transition_issue(ticket.id, edit_id, fields=fields)
            else:
              print('Ticket in {} State. Procceed with regular change'.format(status_name))
              ticket.update(fields=fields)

        except JIRAError as e:
           print("ERROR: {}:{}".format(e.status_code, e.text))
           return False
        return True

    def update_fix_version(self, ticket_id, baseline):
        try:
            ticket = self.client.issue(ticket_id)
            project = ticket.fields.project

            fixVersions = ticket.fields.fixVersions
            existing_versions = self.client.project_versions(project)

            baseline_version = None
            for version in existing_versions:
               if version.name == baseline:
                 baseline_version = version;
                 break;

            if not baseline_version:
              print('Version {} not found. Create Jira version object'.format(baseline))
              baseline_version=self.client.create_version(baseline, project)

            if baseline_version in fixVersions:
              print('Version {} already specified'.format(baseline_version))
              return

            print('Baseline {} not found in existing versions. Updating list'.format(baseline_version))
            versionsSerialization = []
            versionsSerialization.append({'name':baseline_version.name})
            for version in fixVersions:
                versionsSerialization.append({'name':version.name})
            self._update_ticket(ticket, {'fixVersions':versionsSerialization})

        except JIRAError as e:
            print("ERROR: {}:{}".format(e.status_code, e.text))
            return False
        return True

    def get_ticket_info(self, ticket_id):
        try:
            ticket = self.client.issue(ticket_id)
            result = ticket.fields
            #result = ticket.raw['fields'] -> List all available fields
        except JIRAError as e:
            print("ERROR: {}:{}".format(e.status_code, e.text))
            result = None

        return result

    def get_ticket_raw(self, ticket_id):
        try:
            ticket = self.client.issue(ticket_id)
            result = ticket
        except JIRAError as e:
            print("ERROR: {}:{}".format(e.status_code, e.text))
            result = None

        return result

    def get_ticket_labels(self, issue):
        try:
            ticket = self.get_ticket_raw(issue)
            custom_field_id = self.field_map['Labels']
            labels_list = ticket.raw['fields'][custom_field_id]
        except JIRAError as e:
            print("ERROR: {}:{}".format(e.status_code, e.text))
            labels_list = None

        return labels_list

    def get_links_info(self, issue):
        try:
            remote_links = self.client.remote_links(issue)
        except JIRAError as e:
            print("ERROR: {}:{}".format(e.status_code, e.text))
            remote_links = None

        return remote_links

    def add_link_to_issue(self, issue, change_url, description):
        try:
            print("Add link to issue {} {} {}", change_url, description, issue)
            remote_link = self.client.add_simple_link(issue, { "url": change_url, "title": description, "Link Text": description})
        except JIRAError as e:
            print("ERROR: {}:{}".format(e.status_code, e.text))
            remote_link = None

        return remote_link

    def update_link(self, ticket_id, link_id, change_url, description):
        try:
            remote_link = self.client.remote_link(ticket_id, link_id)
            remote_link.update({ "url": change_url, "title": description, "Link Text": description})
        except JIRAError as e:
            print("ERROR: {}:{}".format(e.status_code, e.text))
            remote_link = None

        return remote_link

    def update_ticket_labels(self, issue, fsc=[]):
        result = False
        ticket = self.get_ticket_raw(issue)
        custom_field_id = self.field_map['Labels']

        print("Updating Ticket Lables field -> {}".format(fsc))

        if ticket and custom_field_id in dir(ticket.fields):
            try:
                self._update_ticket(ticket, {custom_field_id: fsc})
                result = True
            except JIRAError as jira_error:
                print("ERROR: {}:{}".format(jira_error.status_code, jira_error.text))
        else:
            print("Field {} is not available for {}".format(custom_field_id, ticket))

        return result

    def search_tickets(self, search=None, simple_search=False):
        '''
        Conmod Project version - Update for a simple search, # issues found
        '''

        ticket_list = []
        if search:
            print("Search: {}".format(search))
            tickets = []
            try:
                total = 0
                obtained = 500

                while obtained == 500:
                    print("Obtaining tickets starting at {}".format(total))
                    issues = self.client.search_issues(jql_str=search, startAt=total, maxResults=obtained)
                    tickets += issues
                    obtained = len(issues)
                    total += obtained

                print("Found {} tickets".format(obtained))

            except JIRAError as e:
                print("ERROR: {}:{}".format(e.status_code, e.text))
            except ValueError as err:
                print("ERROR: {}".format(str(err)))

            if simple_search is False:
                for aTicket in tickets:
                    temp_ticket = jira_ticket()
                    ticket_project, ticket_number = str(aTicket).split('-')
                    temp_ticket.set_project(ticket_project)
                    temp_ticket.set_number(ticket_number)
                    temp_ticket = readTicket(temp_ticket, aTicket.fields, self)
                    ticket_list.append(temp_ticket)
            else:
                ticket_list = tickets
        else:
            print("No search received!")

        return ticket_list

    def get_tickets_by_integrated_into(self, integrated_into, project='Telematics Platform'):
        search_template = r'''project = "{project}" AND "Integrated into" = "{integrated}" AND ( type in (
        "Defect", "Story", "Sub-task") OR (type = "Epic" AND epictype != "Feature" AND (component 
        is EMPTY OR component not in ("TP_NonFeature")) )) AND "Responsible Project" =
        "{project}" AND (Resolution is EMPTY OR Resolution not in (Duplicate, Rejected))'''
        search = search_template.format(integrated=integrated_into, project=project)

        return self.search_tickets(search)

    def exclude_components(self, excluded_components=[]):
        mysearch = ""
        for excluded in excluded_components:
            if excluded == 'TVIP':
                mysearch += ' AND "Domain/SubDomain" not in (TVIP)'
            if excluded == 'HAL':
                mysearch += ' AND labels not in (HAL)'
        return mysearch

    def get_remaining_tickets(self, aVariant, aProject='Telematics Platform', aOtpRelease=None):
        search = r'project = "{}" AND type = "Defect" AND status not in (Done,Delivered,Approved,Closed) AND ' \
                 r'Variant in ({}) AND "Responsible Project" = "{}" AND ' \
                 r'(Resolution is EMPTY OR Resolution not in (Duplicate, Rejected))'
        search = search.format(aProject, aVariant, aProject)
        if aOtpRelease:
            search += ' AND (Branch is EMPTY OR Branch in ("{}"))'.format(aOtpRelease)
            excluded_components = get_excluded_components(aOtpRelease)
            if excluded_components:
                search += self.exclude_components(excluded_components)
        return self.search_tickets(search)

    def get_pd_tickets(self, aOtpRelease, aVariant=None, aProject='Telematics Platform'):
        ticket_list = []
        for cp in customer_projects[aOtpRelease]:
            #Requesting Project
            search = r'project = "{project}" AND status not in (Closed,Releasing) AND "Requesting Project" = "{cp}" AND type in ("Defect", "Epic") AND ( Resolution is EMPTY OR Resolution not in (Duplicate, Rejected)) AND "Responsible Project" = "{project}"'.format(
                project=aProject, cp=cp)
            if aVariant:
                search += ' AND Variant in ({})'.format(aVariant)

            excluded_components = get_excluded_components(aOtpRelease)
            if excluded_components:
                excluded_search = self.exclude_components(excluded_components)
                search += excluded_search
            else:
                excluded_search = ""

            ticket_list.extend(self.search_tickets(search))

            #Submitting Team
            search = r'project = "{project}" AND status not in (Closed,Releasing) AND "Submitting Team" = "{cp}" AND type in ("Defect", "Epic") AND ( Resolution is EMPTY OR Resolution not in (Duplicate, Rejected)) AND "Responsible Project" = "{project}"'.format(
                project=aProject, cp=cp)

            if aVariant:
                search += ' AND Variant in ({})'.format(aVariant)

            search += excluded_search

            # This is to avoid duplicating tickets from Requesting Project
            st_tickets = self.search_tickets(search)
            if st_tickets:
                for st_ticket in st_tickets:
                    print("Checking {}".format(st_ticket.get_display()))
                    if st_ticket not in ticket_list:
                        print("Appending {}".format(st_ticket))
                        ticket_list.append(st_ticket)
                    else:
                        print("{} already included.".format(st_ticket.get_display()))

        return ticket_list

    def get_customer_tickets(self, aOtpRelease, aVariant=None, aProject='Telematics Platform'):
        search = r'project = "{project}" AND status not in (Closed,Releasing) ' \
            'AND type in ("Defect", "Epic") ' \
            'AND ( Resolution is EMPTY OR Resolution not in (Duplicate, Rejected)) '\
            'AND ("Reported by Customer" = Yes) '\
            'AND "Responsible Project" = "{project}"'.format(project=aProject)
        if aVariant:
            search += ' AND Variant in ({})'.format(aVariant)

        excluded_components = get_excluded_components(aOtpRelease)
        if excluded_components:
            excluded_search = self.exclude_components(excluded_components)
            search += excluded_search

        return self.search_tickets(search)

    def get_programEpic_tickets(self, aRelease, aProject='Telematics Platform'):
        search = r'project = "{project}" AND type in ("Epic") AND epictype = "Feature" AND fixVersion in versionMatch("{release}*") AND (resolution != Rejected OR resolution is EMPTY) AND "Responsible Project" = "{project}"'.format(
            project=aProject, release=aRelease)

        return self.search_tickets(search)

    def get_epic_link(self, ticket_id, project='Telematics Platform'):
        search = r'project = "{}" AND "Epic Link" = {ticket}'.format(project, ticket=ticket_id)

        return self.search_tickets(search)

    def get_programEpics_major(self, aRelease, aProject='Telematics Platform'):

        if aRelease != "":
            # Calculate major release
            major = (aRelease.split("."))[0]
            search = r'project = "{project}" AND type in ("Epic") AND epictype = "Feature" AND fixVersion in versionMatch("{major}.*") AND status not in (Releasing,Closed) AND (resolution != Rejected OR resolution is EMPTY) AND "Responsible Project" = "{project}"'.format(
                project=aProject, major=major)
        else:
            search = r'project = "{project}" AND type in ("Epic") AND epictype = "Feature" AND fixVersion is not EMPTY AND status not in (Releasing,Closed) AND (resolution != Rejected OR resolution is EMPTY) AND "Responsible Project" = "{project}"'.format(
                project=aProject)

        return self.search_tickets(search)

    def get_pr_by_affected_testcase(self, aTestcase_id, aSW_variant, aProject='Telematics Platform'):
        # Query for TVIP requires Domain/SubDomain = TVIP and exclude de variant field
        if aSW_variant.__contains__('TVIP'):
            variant_statement = ' AND "Domain/SubDomain" = TVIP'
        else:
            variant_statement = ' AND (Variant is EMPTY OR Variant in ({sw_variant}))'.format(sw_variant=aSW_variant)

        search = r'project = "{project}" AND type in ("Defect","Epic", Story) AND ' \
                 r'"Affected Testcase ID" ~ {testcase_id} AND status not in (Delivered, Closed, Done, Releasing)' \
                 r'{variant_statement}'
        search = search.format(project=aProject, testcase_id=aTestcase_id, variant_statement=variant_statement)

        return self.search_tickets(search)

    def get_showstoppers_since(self, baseline_date, release="otp-1.y", aProject='Telematics Platform'):
        '''
        '''
        platform = get_platform_from_release(release)
        search = r'project = "{project}" AND type in ("Defect") and Severity = "S-Showstopper" AND "Variant" in ({platform}) AND created >= "{date}"  AND (resolution is EMPTY OR resolution not in ("Cannot Reproduce",Rejected,Duplicate,"Won\'t Solve" )) AND "Responsible Project" = "{project}"  AND (Branch is EMPTY OR Branch in ("{release}"))'.format(
            project=aProject, platform=platform, date=baseline_date.strftime('%Y/%m/%d %H:%M'), release=release)

        return self.search_tickets(search)

    def get_severity_all(self, severity, release="otp-mdm9x28-2.y", aProject='TP'):
        '''
        '''
        # Query for TVIP requires Domain/SubDomain = TVIP and exclude de variant field
        platform = get_platform_from_release(release)
        tvip_modifier = '' if platform.__contains__('TVIP') else '!'
        variant_statement = '' if platform.__contains__('TVIP') else ' AND Variant in ({})'.format(platform)

        search = r'project = "{project}" AND issuetype = Defect AND Severity = "{severity}"  AND "Responsible Project" in ("Telematics Platform") AND resolution is EMPTY{variant_statement} AND "Domain/SubDomain" != Modem_Cert AND "Domain/SubDomain" {tvip_modifier}= TVIP ORDER BY severity ASC, created DESC'.format(
            project=aProject, severity=severity, platform=platform, variant_statement=variant_statement, tvip_modifier=tvip_modifier)
        return self.search_tickets(search)

    def get_blocking_issues(self, aProject='Telematics Platform', release="otp-mdm9x28-2.y"):
        platform = get_platform_from_release(release)
        search = r'project = "{project}" AND resolution is EMPTY and type = Defect and Variant in ({platform}) and ((Severity = S-Showstopper) or (labels = rrr_{platform_modifier}_blocker))'.format(
            project=aProject, platform=platform, platform_modifier=platform.lower())
        return self.search_tickets(search)

    def update_Integrated_into(self, issue, fsc=[]):
        result = False
        ticket = self.get_ticket_raw(issue)
        custom_field_id = self.field_map['Integrated into']

        if ticket and custom_field_id in dir(ticket.fields):
            try:
                ticket.update(fields={custom_field_id: fsc})
                result = True
            except JIRAError as jira_error:
                print("ERROR: {}:{}".format(jira_error.status_code, jira_error.text))
        else:
            print("Field {} is not available for {}".format(custom_field_id, ticket))

        return result

    def get_parents(self, a_ticket: jira_ticket):
        parents = []
        if a_ticket.iParent:
            parents.append(a_ticket.iParent)
        else:
            print("{} has no owner".format(a_ticket.get_display()))
        if a_ticket.iEpic:
            parents.append(a_ticket.iEpic)
        else:
            print("{} has no Epics".format(a_ticket.get_display()))

        if a_ticket.iIssuelinks:
            print("Checking issues linked to {}".format(a_ticket.get_display()))
            for issue in a_ticket.iIssuelinks:
                link = readLink(issue)
                if link.iKey:
                    if link.iRelation == "Child of":
                        parents.append(link.iKey)
                    elif link.iRelation == "Epic Link":
                        parents.append(link.iKey)
                    else:
                        print("Ignoring \"{}\" as a parent".format(link))
                else:
                    print("issue {} could not be decoded".format(issue))
        else:
            print("Ticket {} without links".format(a_ticket.get_display()))

        return parents

    def get_descendants(self, a_ticket: jira_ticket):
        descendants = []
        if a_ticket.iSubtasks:
            descendants.extend(a_ticket.iSubtasks)
        else:
            print("{} has no subtasks".format(a_ticket.get_display()))

        if a_ticket.iIssuelinks:
            print("Checking issues linked to {}".format(a_ticket.get_display()))
            for issue in a_ticket.iIssuelinks:
                link = readLink(issue)
                if link.iKey:
                    if link.iRelation == "Parent of":
                        descendants.append(link.iKey)
                    else:
                        print("Ignoring \"{}\" as a descendent".format(link))
                else:
                    print("issue {} could not be decoded".format(issue))
        else:
            print("Ticket {} without links".format(a_ticket.get_display()))

        if a_ticket.iType == "Epic":
            print("Getting Epic links...")
            epiclinks = self.get_epic_link(a_ticket.get_display())
            if epiclinks:
                print("Epic links found!")
                descendants.extend([x.get_display() for x in epiclinks])
            else:
                print("No Epic links found!")

        return descendants

    def analyze_integrated_into(self, key, release_id, baseline_name, aParent=False, aNew=True):
        myresult = {
            'tickets_invalid_type' : None,
            'tickets_ready' : None,
            'tickets_to_review' : None,
            'tickets_to_update' : None,
            'valid_tickets' : None,
            'not_in_db' : None
        }

        if aNew:
            print("Analyzing {}".format(key))
            cr_info = self.get_ticket_info(key)
            if cr_info == [''] or not cr_info:
                print("Information of {} could not be obtained".format(key))
                myresult['not_in_db'] = key
                return myresult

            myresult['valid_tickets'] = key

            temp_ticket = jira_ticket()
            ticket_project, ticket_number = key.split('-')
            temp_ticket.set_project(ticket_project)
            temp_ticket.set_number(ticket_number)
            temp_ticket = readTicket(temp_ticket, cr_info, self)

        else:
            temp_ticket = key
            print("Analyzing {}".format(temp_ticket.get_display()))

        integrated_into = temp_ticket.get_free_string_c()
        request_type = temp_ticket.get_request_type()
        if request_type in invalid_types:
            myresult['tickets_invalid_type'] = temp_ticket
            print("Ticket type invalid: {0},{1}".format(key, request_type))
        elif not integrated_into:
            # The ticket is candidate to be updated
            temp_ticket.set_free_string_c([baseline_name])
            myresult['tickets_to_update'] = temp_ticket
            print("Ticket to be updated: {0},{1}".format(key, ""))
        elif baseline_name in integrated_into:
            # The ticket is already correct
            myresult['tickets_ready'] = temp_ticket
            print("Ticket correct: {0},{1}".format(key, integrated_into))
        elif release_id in integrated_into:
            # The ticket is candidate to be updated
            print("Ticket to be updated: {0},{1}".format(key, integrated_into))
            for n, free_string_c in enumerate(integrated_into):
                if free_string_c == release_id:
                    integrated_into[n] = baseline_name
            temp_ticket.set_free_string_c(integrated_into)
            myresult['tickets_to_update'] = temp_ticket
        elif aParent:
            # The parent will be updated
            print("Parent Ticket to be updated: {0},{1}".format(key, integrated_into))
            integrated_into.append(baseline_name)
            temp_ticket.set_free_string_c(integrated_into)
            myresult['tickets_to_update'] = temp_ticket
        else:
            # The ticket needs to be reviewed
            print("Ticket to be reviewed: {0},{1}".format(key, integrated_into))
            myresult['tickets_to_review'] = temp_ticket

        return myresult
