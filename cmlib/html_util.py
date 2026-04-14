#!/usr/bin/python
# *****************************************************************************
# *
# *  (c) 2024-2025 Continental Automotive Systems, Inc., all rights reserved
# *
# *  All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *  Any reproduction of this material without written consent from
# *  Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *   Filename: html_util.py
# *
# *   Description:  utility functions for creating html page elements
# *
# *
# *****************************************************************************

import re
import os

# hardcoded Gerrit server link. Only used to create the html links inside the resulting Email:
gerrit_host = "buic-scm-dpk.contiwan.com:8443"
# list of repos, for which entries will be skipped:
repo_skip_list = [ "p1/project/otp-framework/manifest", "p1/project/otp-hal/manifest"]

def create_html_link_entry(full_link, text=None):
    """create a html link out of the given full link text
     Args:
        full_link (str): http link
        text (str): text for http link, if different

    Returns:
        str: html(str): html link
    """
    link_text = full_link if text == None else text
    html = '<a href="{}">{}</a>'.format(full_link, link_text)
    return html

def create_table_row(repo, revision, ticket, description):
    """create a table row for for the given project/repo name

    Args:
        repo (str): repo name
        revision (str): revision for Gerrit link
        ticket (str): ticket name for Jira link
        description (str): ticket description text

    Returns:
        str: html table row
    """

    html = "<tr>"
    repo_link = create_url_for_repo_field(gerrit_host, repo)
    html += '<td><a href="{}">{}</a></td>'.format(repo_link, repo)
    revision_link = create_url_for_revision(gerrit_host, repo, revision)
    html += '<td><a href="{}">{}</a></td>'.format(revision_link, revision)
    jira_link = create_ticket_link(ticket)
    html += '<td><a href="{}">{}</a></td>'.format(jira_link, ticket)
    html += '<td>{}</td>'.format(description)
    html += "</tr>\n"
    return html

def create_ticket_link(jiraticket):
    """ create a link to Jira

    Args:
        jiraticket (str): Jira ticket name

    Returns:
        str: jira_link, the resulting link to Jira
    """
    jira_link = "https://jira.vni.agileci.conti.de/browse/{}".format(jiraticket)
    return jira_link

def create_url_for_repo_field(gerrit_host, repo):
    """create a Gerrit url for the name field in a html table

    Args:
        gerrit_host (str): full Gerrit host name (hostname:port)
        repo (str): name string for the Gerrit url

    Returns:
        str: name_url, resulting url for name field
    """
    """ format for name field link is:
    https://buic-scm-fr.contiwan.com:8443/#/admin/projects/p1/package/qualcomm/qcom-mdm9x50-le-2-3-modem
    """
    name_url = "https://{}/#/admin/projects/{}".format( gerrit_host, repo )
    return name_url

def create_url_for_revision(gerrit_host, repo, revision):
    """create a Gerrit url for the revision field in a html table

    Args:
        gerrit_host: full Gerrit host name (hostname:port)
        repo (str): name string for Gerrit needed for the url
        revision (str): revision for Gerrit link

    Returns:
        str: revision_url, resulting url for upstream field
    """
    """ format for revision link is:
    https://buic-scm-fr.contiwan.com:8443/gitweb?p=p1/package/qualcomm/qcom-mdm9x50-le-2-3-modem.git;a=commit;h=575cdf1cc794fc0ead0f4c663879274775356210
    """
    revision_url = "https://{}/gitweb?p={}.git;a=commit;h={}".format( gerrit_host, repo, revision )
    return revision_url

def create_html_table(list_of_changes):
    """create html table from the change list

    Args:
        list_of_changes (list): list of changes with repo, revision, ticket, description in one list entry, divided by 'tab' character

    Return:
        html: table as html element
    """
    html = ""
    html += '<table border="1">\n'
    html += "<tr><th>name</th><th>commit</th><th>ticket</th><th>description</th></tr>\n"
    for line in list_of_changes:
        # skip the notification lines for hal and framework in the table... (repo_skip_list)
        fields = line.split('\t')
        repo = fields[0].strip()
        if not repo in repo_skip_list:
            html += create_table_row(repo, fields[1].strip(), fields[2].strip(), fields[3].strip())
        else:
            print("Repo entry for {} was skipped!".format(repo))
    html += "</table>\n"
    return html

def create_list_of_changes(release_path):
    """create a list of changes from the given release path change-summary.txt file

    Args:
        release_path (str): path to release folder. Must contain change-summary.txt

    Returns:
        list: list of changes with tab seperated lines containing repo, revision, ticket, description. An empty list on error, or if there are no changes
        str: changes_since, as it's indicating the change 'since' line, which is very important to understand what the returned list is all about...
    """
    changes_since = "unknown"
    regex_since = r"^Change summary (since [^ ]*).*$"
    change_summary_file = "{}/change-summary.txt".format(release_path)
    list_of_changes = []
    repo_regex = r"^Repo: ((.*)( \(Added\))?)$"
    repo_r = re.compile(repo_regex)
    commit_line_regex = r"^  ([0-9a-z]{7}) ([^:]*): (.*)$"
    commit_line_r = re.compile(commit_line_regex)
    if os.path.exists(change_summary_file) == True:
        file_size = os.path.getsize(change_summary_file)
        if file_size > 0:
            with open(change_summary_file) as change_file:
                lines = change_file.readlines()
                headline_match = re.match(regex_since, lines[0])
                if headline_match != None:
                    changes_since = headline_match.group(1)
                repo = None
                commitId = None
                ticket = None
                description = None
                for line in lines:
                    # parse 'Repo' line
                    if line.startswith("Repo:"):
                        try:
                            repo = repo_r.match(line).group(1)
                        except Exception as e:
                            repo = "Parser error"
                    # check for tickets in line
                    elif commit_line_r.match(line) != None:
                        # parse and divide lines...
                        try:
                            matches = commit_line_r.match(line)
                            commitId = matches.group(1)
                            ticket = matches.group(2)
                            description = matches.group(3)
                        except Exception as e:
                            commitId = "Parser error" if commitId == None else commitId
                            ticket = "Parser error" if ticket == None else ticket
                            description = "Parser error" if description == None else description
                        list_of_changes.append("{}\t{}\t{}\t{}".format(repo, commitId, ticket, description))
                        commitId = ticket = description = None
        else:
            print("File {} is empty! No changes found!".format(change_summary_file))
    else:
        print("Import file {} not found!".format(change_summary_file))
    print("List of changes:\n{}".format(list_of_changes))
    return list_of_changes, changes_since
