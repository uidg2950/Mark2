#!/usr/bin/python
"""
# ******************************************************************************
# *
# * (c) 2017-2025 Continental Automotive Systems, Inc., all rights reserved
# *
# * All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# * Any reproduction of this material without written consent from
# * Continental Automotive Systems, Inc. is strictly forbidden.
# *
# * Filename:    jira/util.py
# *
# * Description: Utilities for jira
# *
# ******************************************************************************
"""
import re

from cmlib.jira.structures import JiraLink
from cmlib import util

consumer_key = "python_jira"
jira_project = "Telematics Platform"
jira_server = 'https://ix.jira.automotive.cloud:443'
jira_server_id = '6f6045d6-ac75-396c-9b0d-e3c82f291d58'
TICKET_FORMAT_PATTERN = re.compile(r'(\w+-[1-9]\d*)')

JIRA_ORDER = {
    'Blocker': 4,
    'Critical': 3,
    'Major': 2,
    'Minor': 1,
    'Trivial': 0,
    None: -1
}

customer_projects = {}
customer_projects.update({'otp-1.y': ['Ford TCU B3']})
customer_projects.update({'otp-1.30.2.y': ['Subaru Gen1', 'Subaru Gen2']})
customer_projects.update({'otp-ipth-1.y': ['Ford TCU B2', 'Toyota Gen1']})
#Toyota GDCM with two names at Jira
customer_projects.update({'otp-mdm9x28-2.y': ['Daimler Ramses']})
customer_projects.update({'otp-mdm9x28-2.50.2.y': ['Toyota GDCM MY 19', 'Toyota GDCM MY19',
                                                   'Ford TCU B4', 'Subaru T19plus',
                                                   'HMC eCall Gen2', 'HMC eCall 2',
                                                   'AIVC SOP3', 'Geely SPA TCAM',
                                                   'Geely SPA TCAM (DG-056585)']})
customer_projects.update({'otp-mdm9x28-2.64.1.y': ['VCC TCAM VGM', 'PSA BSRF']})
customer_projects.update({'otp-mdm9x28-2.69.0.y': ['Daimler Ramses']})
customer_projects.update({'otp-mdm9x28-aivc-2.y': ['Renault AIVC']})
customer_projects.update({'otp-mdm9x50-2.y': ['Daimler Ramses']})
customer_projects.update({'otp-mdm9x50-sop-2.y': ['Daimler Ramses']})
customer_projects.update({'otp-mdm9x50-sop1-2.y': ['Daimler Ramses']})
customer_projects.update({'otp-framework-2.y': ['Daimler Ramses']})

invalid_status = ['concluded', 'duplicate', 'rejected']
invalid_types = ['ProgramEpic', 'Capability']


def readTime(strTime):
    """
    returns the corresponding time in seconds
    """
    intTime = int(strTime[:-1])
    if strTime[-1].lower() == "h":  # hours
        intTime = intTime * 60
    elif strTime[-1].lower() == "d":  # days
        intTime = intTime * 8 * 60

    return intTime


def getWorklog(aTicket):
    """
    return the time logged for a ticket
    in minutes
    """
    totalTime = 0
    for worklog in aTicket.worklog.worklogs:
        totalTime += readTime(worklog.timeSpent)

    return totalTime


def readTicket(jira_ticket, fields, jira_query):
    """

    :param jira_ticket:
    :param fields:
    :param jira_query:
    :return:
    """
    print("Reading {}".format(jira_ticket.get_display()))

    if not fields:
        print('Cannot read values from {}'.format(jira_ticket))
        return jira_ticket

    jira_status_name = fields.status.name
    # jira_priority_name = fields.priority.name
    jira_summary = fields.summary
    jira_custom_review_link = jira_query.field_map['Review Link']
    jira_custom_integrated_into = jira_query.field_map['Integrated into']
    jira_custom_domain = jira_query.field_map['Domain/SubDomain']
    jira_custom_sprint = jira_query.field_map['Sprint']
    jira_custom_status_summary = jira_query.field_map['Status Summary']
    jira_issuetype_name = fields.issuetype.name
    jira_ticket.set_status(jira_status_name)
    # jira_ticket.set_priority(jira_priority_name)
    jira_ticket.set_summary(jira_summary)


    try:
        jira_ticket.set_review_link(getattr(fields, jira_custom_review_link))
    except Exception:
        jira_ticket.iReviewLink = ""

    jira_ticket.set_request_type(jira_issuetype_name)

    # Dates
    jira_ticket.set_creation_date(fields.created)

    updated_attribute = jira_query.field_map['Updated']
    jira_ticket.set_update_date(getattr(fields, updated_attribute))
    # End: dates

    try:
        jira_ticket.set_free_string_c(getattr(fields, jira_custom_integrated_into))
    except Exception:
        jira_ticket.set_free_string_c([])

    try:
        jira_ticket.set_domain(getattr(fields, jira_custom_domain))
    except Exception:
        jira_ticket.iDomain = ""

    try:
        jira_ticket.set_sprint(getattr(fields, jira_custom_sprint))
    except Exception:
        jira_ticket.set_sprint([])

    try:
        req_proj_cust_id = jira_query.field_map.get('Requesting Project/s', None)
        if req_proj_cust_id and getattr(fields, req_proj_cust_id):
            jira_ticket.set_requesting_project(getattr(fields, req_proj_cust_id).value)
        else:
            jira_ticket.set_requesting_project('')
    except AttributeError:
        jira_ticket.set_requesting_project('')

    try:
        submt_team_cust_id = jira_query.field_map.get('Submitting Team', None)
        if submt_team_cust_id and getattr(fields, submt_team_cust_id):
            jira_ticket.set_submitting_team(getattr(fields, submt_team_cust_id).value)
        else:
            jira_ticket.set_submitting_team('')
    except AttributeError:
        # print("AttributeError in {}".format(submt_team_cust_id))
        jira_ticket.set_submitting_team('')

    try:
        rep_by_cust_id = jira_query.field_map.get('Reported by Customer', None)
        if rep_by_cust_id and getattr(fields, rep_by_cust_id):
            jira_ticket.set_reported_by_customer(getattr(fields, rep_by_cust_id).value)
        else:
            jira_ticket.set_reported_by_customer('')
    except AttributeError:
        jira_ticket.set_reported_by_customer('')

    try:
        jira_ticket.set_fix_versions(fields.fixVersions)
    except Exception:
        jira_ticket.iFix_versions = []

    try:
        jira_ticket.set_affects_versions(fields.versions)
    except Exception:
        jira_ticket.iAffects_versions = []

    try:
        fml_id = jira_query.field_map.get('Feature Maturity Level', None)
        jira_ticket.iFml = (
            str(getattr(fields, fml_id))
            if fml_id and getattr(fields, fml_id)
            else None
        )
    except Exception:
        print("Error reading Feature Maturity Level")
        jira_ticket.iFml = None

    try:
        severity_id = jira_query.field_map.get('Severity', None)
        severity_value = getattr(fields, severity_id).value if severity_id else None
        jira_ticket.set_severity(severity_value)
    except Exception:
        # print("Exception reading severity for {}".format(temp_change.get_display()))
        jira_ticket.set_severity(None)

    # Add outwardIssue
    jira_ticket.add_issuelinks(fields.issuelinks)

    if hasattr(fields, "parent"):
        jira_ticket.iParent = fields.parent.key

    if hasattr(fields, "subtasks"):
        if fields.subtasks:
            for subtask in fields.subtasks:
                jira_ticket.add_subtask(subtask.key)
        else:
            print("No subtasks for {}".format(jira_ticket.get_display()))

    epic_id = jira_query.field_map['Epic Link']
    try:
        jira_ticket.iEpic = getattr(fields, epic_id)
    except AttributeError:
        print("AttributeError for Epic Link:{}".format(epic_id))
        jira_ticket.iEpic = ""

    # FIXME: Temporary "by pass" due Jira Migration
    try:
        cr_id = jira_query.field_map['Change Request']
        jira_ticket.iCr = ""
    except KeyError:
        util.debug("No 'Change Request' field available")

    if jira_issuetype_name == "Epic":
        try:
            cr_id = jira_query.field_map.get('Change Request', None)
            cr = getattr(fields, cr_id) if cr_id else None
            if cr:
                for element in cr:
                    if jira_ticket.iCr == "":
                        jira_ticket.iCr = element.value
                    else:
                        jira_ticket.iCr = ",".join([jira_ticket.iCr, element.value])
        except AttributeError:
            print("AttributeError for Change Request")
            jira_ticket.iCr = ""

    try:
        resp_proj_id = jira_query.field_map.get('Responsible Project', None)
        jira_ticket.iResponsible_project = str(getattr(fields, resp_proj_id)) if (
            resp_proj_id) else None
    except AttributeError:
        print("AttributeError for Responsible Project")
        jira_ticket.iResponsible_project = ''

    try:
        time_spent_attribute = jira_query.field_map.get('Time Spent', None)
        jira_ticket.time_spent = getattr(fields, time_spent_attribute) if (
            time_spent_attribute) else None
    except AttributeError:
        jira_ticket.time_spent = 0

    #Status Summary
    try:
        jira_ticket.set_status_summary(getattr(fields, jira_custom_status_summary))
    except AttributeError:
        print("AttributeError for Status Summary:{}".format(jira_custom_status_summary))

    return jira_ticket


def readLink(issue):
    temp_link = JiraLink()
    if issue:
        if hasattr(issue, "inwardIssue"):
            print(" inwardIssue found!")
            anIssue = issue.inwardIssue
            relation = issue.type.inward
            issueType = "inwardIssue"
        elif hasattr(issue, "outwardIssue"):
            print(" outwardIssue found!")
            anIssue = issue.outwardIssue
            relation = issue.type.outward
            issueType = "outwardIssue"
        else:
            print("Not Identified!")
            anIssue = None
            relation = ""
            issueType = None

        if anIssue:
            temp_link.iKey = anIssue.key
            temp_link.iType = anIssue.fields.issuetype.name
            temp_link.iSummary = anIssue.fields.summary
            temp_link.iRelation = relation
            temp_link.iLinkType = issueType
    return temp_link

def move_ticket_to(ticket, source, target):
    '''
    Moves a jira_ticket from a source list to a target list

    :param ticket: a jira ticket
    :param source: a list of jira tickets
    :param target: a list of jira tickets
    '''
    target.append(ticket)
    for n, aTicket in enumerate(source):
        if aTicket.get_display() == ticket.get_display():
            source.pop(n)

    return source, target
#End move_tickets_to

def get_item_from(ticket_id, aList):
    '''
    Gets a jira_ticket from a list of jira ticket

    :param ticket_id: a jira ticket id e.g. TP-1234
    :param aList: a list of jira tickets
    '''
    ticket_analyzed = None
    for item in aList:
        if item.get_display() == ticket_id:
            ticket_analyzed = item

    return ticket_analyzed
#End get_item_from

def get_ticket_list_name(ticket_id, tickets_invalid_type, tickets_to_update, \
    tickets_ready, tickets_to_review):
    '''
    Verifies if a ticket is included in any of the lists

    :param ticket_id: id of the jira ticket to be looked for
    :param tickets_invalid_type: list of jira tickets of invalid type
    :param tickets_to_update: list of jira tickets to be updated
    :param tickets_ready: list of jira tickets already correct
    :param tickets_to_review: list of jira tickets that needs to be reviewed
    :return: the ticket that was looked for or None
    :return: a string representation of the list that contain the ticket
             or an empty string
    '''
    ticket_analyzed = None
    old_ticket_type = ""
    if ticket_id in [x.get_display() for x in tickets_invalid_type]:
        ticket_analyzed = get_item_from(ticket_id, tickets_invalid_type)
        old_ticket_type = "invalid"
    elif ticket_id in [x.get_display() for x in tickets_to_update]:
        ticket_analyzed = get_item_from(ticket_id, tickets_to_update)
        old_ticket_type = "to_update"
    elif ticket_id in [x.get_display() for x in tickets_ready]:
        ticket_analyzed = get_item_from(ticket_id, tickets_ready)
        old_ticket_type = "ready"
    elif ticket_id in [x.get_display() for x in tickets_to_review]:
        ticket_analyzed = get_item_from(ticket_id, tickets_to_review)
        old_ticket_type = "to_review"

    return ticket_analyzed, old_ticket_type

def get_parents(tickets, valid_tickets, tickets_invalid_type, tickets_to_update,\
    tickets_ready, tickets_to_review, not_in_db_tickets, release_id, baseline_name, handler):
    '''

    :param tickets:
    :param valid_tickets:
    :param tickets_invalid_type:
    :param tickets_to_update:
    :param tickets_ready:
    :param tickets_to_review:
    :param not_in_db_tickets:
    :param release_id:
    :param baseline_name:
    :param handler:
    :return:
    '''
    jira_query = handler

    for ticket in tickets:
        print("Looking for parents of:{}".format(ticket))
        parents = jira_query.get_parents(ticket)
        if not parents:
            continue

        for parent_id in parents:
            print("Verifying if {} already analyzed".format(parent_id))
            ticket_analyzed, old_ticket_type = get_ticket_list_name(parent_id, \
                tickets_invalid_type, tickets_to_update, tickets_ready, tickets_to_review)

            if ticket_analyzed:
                print("{} analyzed as {}".format(parent_id, old_ticket_type))
            else:
                print("{} not found in analyzed tickets.".format(parent_id))

            if old_ticket_type != "invalid":
                if ticket_analyzed:
                    myresult = jira_query.analyze_integrated_into(
                        ticket_analyzed, release_id, baseline_name, aParent=True, aNew=False)
                else:
                    myresult = jira_query.analyze_integrated_into(
                        parent_id, release_id, baseline_name, aParent=True)
                if myresult['tickets_invalid_type']:
                    invalid_type = myresult['tickets_invalid_type']
                    if old_ticket_type == "":
                        tickets_invalid_type.append(invalid_type)
                    else:
                        print("WARNING: Unexpected {} previously {} now {}".format(parent_id, old_ticket_type, "invalid"))
                elif myresult['tickets_to_update']:
                    to_update = myresult['tickets_to_update']
                    if old_ticket_type == "ready":
                        tickets_ready, tickets_to_update = move_ticket_to(to_update, tickets_ready, tickets_to_update)
                        print("Ticket {} to be updated for {}".format(to_update.get_display(), baseline_name))
                    elif old_ticket_type == "to_review":
                        tickets_to_review, tickets_to_update = move_ticket_to(to_update, tickets_to_review, tickets_to_update)
                        print("Ticket {} to be updated for {}".format(to_update.get_display(), baseline_name))
                    elif old_ticket_type == "to_update":
                        for n, aTicket in enumerate(tickets_to_update):
                            if to_update.get_display() == aTicket.get_display():
                                intInto = to_update.get_free_string_c()
                                tickets_to_update[n].set_free_string_c(intInto)
                        print("Ticket {} to be updated for {}".format(to_update.get_display(), baseline_name))
                    elif old_ticket_type == "":
                        tickets_to_update.append(to_update)
                        print("Ticket {} to be updated for {}".format(to_update.get_display(), baseline_name))
                    else:
                        print("WARNING: Unexpected ticket_type {}!".format(old_ticket_type))
                elif myresult['tickets_ready']:
                    ready = myresult['tickets_ready']
                    if old_ticket_type == "":
                        tickets_ready.append(ready)
                        print("Ticket {} ready for {}".format(ready.get_display(), baseline_name))
                    elif old_ticket_type in ["ready", "to_review", "to_update"]:
                        print("Ticket {} ready for {}".format(ready.get_display(), baseline_name))
                    else:
                        print("WARNING: Unexpected ticket_type {}!".format(old_ticket_type))

                elif myresult['tickets_to_review']:
                    to_review = myresult['tickets_to_review']
                    if old_ticket_type == "":
                        tickets_to_review.append(to_review)
                    elif old_ticket_type in ["to_review", "to_update"]:
                        print("Ticket {} to be reviewed for {}".format(to_review.get_display(), baseline_name))
                    elif old_ticket_type == "ready":
                        tickets_ready, tickets_to_review = move_ticket_to(to_review, tickets_ready, tickets_to_review)
                        print("Ticket {} to be reviewed for {}".format(to_review.get_display(), baseline_name))
                    else:
                        print("WARNING: Unexpected ticket_type {}!".format(old_ticket_type))
                elif myresult['not_in_db']:
                    not_in_db_tickets.append(myresult['not_in_db'])
                if myresult['valid_tickets']:
                    prospect = {'ticket': parent_id, 'parent': True, 'baseline': baseline_name}
                    valid_tickets.append(prospect)
            else:
                print('Ticket {} invalid! Ignoring it'.format(parent_id))
    return valid_tickets, tickets_invalid_type, tickets_to_update, tickets_ready, tickets_to_review, not_in_db_tickets

def get_platform_from_release(release_id=None):
    platforms_map = {
        'Tvip': "TVIP",
        'otp-mdm9x28-2.y': "BELL",
        'otp-mdm9x28-2.50.2.y': "BELL",
        'otp-mdm9x28-2.64.1.y': "BELL",
        'otp-mdm9x28-2.69.0.y': "BELL",
        'otp-mdm9x28-aivc-2.y': "AIVC-SOP1",
        'otp-mdm9x50-2.y': "WATSON",
        'otp-mdm9x50-sop-2.y': "WATSON",
        'otp-mdm9x50-sop1-2.y': "WATSON",
        'otp-sa415m-2.y': "FERMI_VuC_4.5G",
        'otp-sa415m-3.y': "FERMI_AP_4.5G",
        'otp-sa515m-3.y': "FERMI_AP_5G",
        'otp-sa515m-thick-3.y': "FERMI_5G",
        'otp-framework-2.y': "BELL, WATSON"
    }
    return platforms_map.get(release_id, "EDISON")

def get_excluded_components(release_id=None):
    components_map = {
        'otp-framework-2.y': ['TVIP', 'HAL']
    }
    return components_map.get(release_id, None)


def check_jira_tickets(ticket_list):
    from cmlib.jira.query import Query
    jira_querier = Query()
    included_changes = {}
    accepted_review = True
    if jira_querier.client:           # Verify if there's connection with JIRA
        for ticket_id in ticket_list:
            print('Checking for {}'.format(ticket_id))
            if TICKET_FORMAT_PATTERN.match(ticket_id):
                task = jira_querier.get_ticket_info(ticket_id)
                if task and task != ['']:
                    included_changes[ticket_id] = task.status.name
                else:
                    included_changes[ticket_id] = 'Invalid'
            else:
                util.debug("Unrecognized ticket format: {}".format(ticket_id))
        # End JIRA connection

        ##
        ## First verdict validation
        ##
        # 1) Ticket status
        tickets_status = ''     # Default values
        status_check = util.CHECK    # Default values
        if included_changes:
            for ticket, status in included_changes.items():
                issue_type = task.issuetype.name
                if issue_type not in ['Enabler', 'EnablerStory']:
                    if 'Subtask' in issue_type and status in ['In Work', 'In Progress', 'In Analysis']:
                        # Check if ticket parent is an Enabler Story
                        task_ticket = jira_ticket()
                        ticket_project, ticket_number = ticket.split('-')
                        task_ticket.set_project(ticket_project)
                        task_ticket.set_number(ticket_number)
                        task_ticket = readTicket(task_ticket, task, jira_querier)
                        task_parent = jira_querier.get_parents(task_ticket)
                        task_parent_info = jira_querier.get_ticket_info(task_parent[0])
                        if task_parent_info.issuetype.name == 'EnablerStory':
                            status_check = util.BLANK
                            accepted_review = False
                            tickets_status += ticket + ' parent: {}, ' \
                                                       'is an Enabler Story\n'.format(task_parent[0])
                    else:
                        if status not in ['Approval', 'In Progress', 'In Analysis']:
                            status_check = util.BLANK
                            accepted_review = False
                            tickets_status += ticket + ' is not in WIP [current: {}, ' \
                                                       'expected: In Progress/Approval/In Analysis]\n'.format(status)
                        else:
                            tickets_status += ticket + ' is OK\n'
                else:
                    status_check = util.BLANK
                    accepted_review = False
                    tickets_status += ticket + ' is an Enabler ' \
                                               '[current: {}, expected: Story]\n'.format(issue_type)
        else:
            tickets_status = 'No valid Jira ticket was found'
            status_check = util.BLANK
            accepted_review = False
    else:
        tickets_status = 'Failed connection with JIRA'
        status_check = util.BLANK
        accepted_review = False

    return [tickets_status, status_check, accepted_review]

def update_jira_link(ticket_list, change_url, commit_title):
    if ticket_list is None or change_url is None or commit_title is None:
        tickets_status = 'Failure of init arguments'
        status_check = util.BLANK
        accepted_review = False
        return [tickets_status, status_check, accepted_review]

    from cmlib.jira.query import Query
    import re

    def normalize_gerrit_link(url_link):
        return re.sub(r'buic-scm.*?[.]automotive-wan|buic-scm.*?[.]contiwan', 'buic-scm-###.automotive-wan', url_link)

    jira_querier = Query()
    accepted_review = True
    tickets_status = ''
    status_check = util.CHECK
    if jira_querier.client:           # Verify if there's connection with JIRA
        for ticket_id in ticket_list:
            print('Checking for {} creating link to {} with title {}'.format(ticket_id, change_url, commit_title))
            external_links = jira_querier.get_links_info(ticket_id)
            found = False

            for link in external_links:
                url = link.raw["object"]["url"]
                title = link.raw["object"]["title"]
                print('Got link Info {} {} {}'.format(url, title, link.id))
                if normalize_gerrit_link(url) == normalize_gerrit_link(change_url):
                    found = True
                    if not (title == commit_title):
                        result = jira_querier.update_link(ticket_id, link.id, change_url, commit_title)
                        if (result is None):
                            tickets_status = 'Failed to update Jira link'
                            status_check = util.BLANK
                            accepted_review = False
                    break;
            if not found:
                result = jira_querier.add_link_to_issue(ticket_id, change_url, commit_title)
                if (result is None):
                    tickets_status = 'Faailed to create Jira link'
                    status_check = util.BLANK
                    accepted_review = False
    else:
        tickets_status = 'Failed connection with JIRA'
        status_check = util.BLANK
        accepted_review = False

    return [tickets_status, status_check, accepted_review]
