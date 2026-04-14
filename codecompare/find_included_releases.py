#!/usr/bin/python2
#######################################################################
#
# Copyright Notice:
# Copyright (C) 2023
# Continental Automotive GmbH
# Alle Rechte vorbehalten. All Rights Reserved.
# The reproduction, transmission or use of this document or its
# contents is not permitted without express written authority.
# Offenders will be liable for damages.
# All rights, including rights created by patent grant or registration
# of a utility model or design, are reserved.
#
#######################################################################

""" find releases included in project manifest and all included OTP manifests """

__author__ = "Kurt Hanauer"
__version__ = "0.2.0"
__date__ = "2023-11-16"
__credits__ = "Copyright (C) 2023 Continental Automotive GmbH"

#######################################################################
#
# Module-History
#  Date        Author               Reason
#  2020-06-15  Kurt Hanauer         Initial version
#######################################################################

import json
import subprocess
import os
import sys
import csv
import argparse
import xml.etree.ElementTree as ET
from code_compare_utils import launch_command
from repo_versions_compare import load_repo, print_header

def parseargs():
    """ parse command line arguments

    Parameters
    ----------
    None

    Returns
    -------
    args:
        parser result argument list
    """
    parser = argparse.ArgumentParser(description="find releases included in project manifest and all included OTP manifests. Results will be available as html and csv files.")
    parser.add_argument('-p', action='store', dest='project', help="The project to search the included releases for (default is 'drt', 'otp' is also possible)", default='drt')
    parser.add_argument('-b', action='store', dest="branch", help="Project branch to get manifest from (can also be a version tag)")
    parser.add_argument('-o', action='store', dest="output_path", help="output path for resulting files (default is '.')", default='.')
    parser.add_argument('--host', action='store', dest="host_name", help="gerrit host name to connect to (for git commands and output links)", default="buic-scm-ias.contiwan.com")
    args=parser.parse_args()
    if (args.branch==None):
        parser.print_help()
        sys.exit(1)
    print(args)
    return args

class ManifestRetreiver(object):
    """class to retrieve project manifest content

    Args:
        object (class): base class
    """
    def __init__(self, gerrit_host="buic-scm-ias.contiwan.com", project="drt", gerrit_port="29418", manifest_repo=None):
        """Manifest retriever constructor: setting variables

        Args:
            gerrit_host (str, optional): Gerrit host. Defaults to "buic-scm-ias.contiwan.com".
            project (str, optional): project name. Defaults to "drt".
            gerrit_port (str, optional): Gerrit port. Defaults to "29418".
            manifest_repo (str, optional): manifest repo string. has to be used for manifests, which dont follow the 'p1/project/[project_name]/manifest' syntax. Defaults to None.
        """
        # globals defined for the user
        self.GERRIT_HOST="{}:{}".format(gerrit_host, gerrit_port)
        if manifest_repo == None:
            self.REPO="p1/project/{}/manifest".format(project)
        else:
            self.REPO=manifest_repo

    def get_manifest_content_from_file(self, file_path):
        """get the manifest contents from the given file path

        Args:
            file_path (str): file path. Full or relative to current directory

        Returns:
            Element: ET root element for this manifest
        """
        root = None
        if os.path.exists( file_path ):
            root = ET.parse(file_path).getroot()
        return root

    def remove_and_extend_projects(self, repo_list, list_removed, list_extend):
        """ remove and extent given repo list with the two other given lists
        handles remove-project and extend-project entries as stated in the given lists
        No return value, as these lists are passed by reference...

        Args:
            repo_list (list): root element list of this project's repos
            list_removed (list): list with elements to be removed
            list_extend (list): list with elements to be extended (replaces)
        """
        print_header("Remove and extend projects", 80)
        #list_removed = list_rm.findall("remove-project")
        if len(list_removed) > 0:
            for removed in list_removed:
                removed_name = removed.attrib['name']
                #print(f"Searching for {removed_name}")
                #elements = default_root.findall('project[@name="{}"]'.format(removed.attrib["name"]))
                elements = []
                for elem in repo_list:
                    if elem.attrib["name"] == removed_name:
                        elements.append(elem)
                if elements != None and len(elements) > 0:
                    for elem in elements:
                        print(f"removing {removed_name}")
                        repo_list.remove(elem)
                else:
                    print(f"WARNING: element to remove not found!")
        #list_extend = tree_extd.findall("extend-project")
        if len(list_extend) > 0:
            for extended in list_extend:
                extended_name = extended.attrib['name']
                #print(f"Searching for {extended_name}")
                #elements = default_root.findall('project[@name="{}"]'.format(extended.attrib["name"]))
                elements = []
                for elem in repo_list:
                    if elem.attrib["name"] == extended_name:
                        elements.append(elem)
                if elements != None and len(elements) > 0:
                    for elem in elements:
                        #elem.attrib['name'] = extended.attrib['name']
                        print(f"Replacing  {elem.attrib['revision']} with {extended.attrib['revision']} for {extended.attrib['name']}")
                        elem.set("revision", extended.attrib["revision"])
                        load_repo(self.GERRIT_HOST.split(':')[0], self.GERRIT_HOST.split(':')[1], extended.attrib['name'], extended.attrib['revision'], True, fetch=True)
                else:
                    print("Warning: project to extend not found!")


    def get_project_manifest_for_repo(self, branch, tag=None, consider_includes=False, manifest_commit_ref=None):
        """clone the manifest repo for this repo and return the contents as xml tree (root element)

        Args:
            branch (str): branch name
            tag (str, optional): targ name. Defaults to None.
            consider_includes (bool, optional): consider included manifests. Defaults to False.
            manifest_commit_ref (str, optional): Optional manifest commit ref to fetch. Important for Commits, which aren't merged yet. Defaults to None.

        Returns:
            Element: default_root, ET root element for the manfifest
            str: directory name for this manfifest repo containing branch_dir and tag
            str: project_rev, revision for the project manifest
        """
        print_header(" clone the manifest repo and return the contents as xml tree ", 80)
        branch_dir = branch.replace('/', '_')

        if tag == None:
            tag="HEAD"

        # clean command
        clean_command = "rm -rf manifest_repo_{}_{}".format(branch_dir,tag)
        ret_code, clean_result = launch_command( clean_command, True)

        # clone repo
        clone_command = "git clone ssh://{}/{} -b {} manifest_repo_{}_{}".format(self.GERRIT_HOST, self.REPO, branch, branch_dir, tag)
        ret_code, result = launch_command( clone_command, True)
        if ret_code != 0:
            print( "Error on {} command:\n{}".format( clone_command, result ))
            sys.exit(1)

        # switch to branch or commit
        if manifest_commit_ref == None:
            checkout_command = "cd manifest_repo_{}_{}; git fetch; git checkout {}".format(branch, tag, tag)
        else:
            checkout_command = "cd manifest_repo_{}_{}; git fetch ssh://{}/{} {} && git checkout FETCH_HEAD".format(branch, tag, self.GERRIT_HOST, self.REPO, manifest_commit_ref)
        ret_code, result = launch_command( checkout_command, True)
        if ret_code != 0:
            print( "Error on {} command:\n{}".format( clone_command, result ))
            sys.exit(1)

        # rev parse command
        rev_parse_cmd = "cd manifest_repo_{}_{}; git rev-parse HEAD".format(branch, tag)
        ret_code, project_rev = launch_command( rev_parse_cmd, True)
        if ret_code != 0:
            print( "Error on {} command:\n{}".format( rev_parse_cmd, result ))
            sys.exit(1)
        else:
            project_rev = project_rev.strip()

        # get manifest(s) content
        default_root = None
        #platform_overrides_root = None
        if os.path.exists( "manifest_repo_{}_{}/default.xml".format(branch_dir, tag)):
            manifest_default = "manifest_repo_{}_{}/default.xml".format(branch_dir, tag)
            default_root = ET.parse(manifest_default).getroot()
            if consider_includes == True:
                included_files = default_root.findall("include")
                for included_file in included_files:
                    file_name = included_file.attrib["name"]
                    tree = self.get_manifest_content_from_file(f"manifest_repo_{branch_dir}_{tag}/{file_name}")
                    # merge trees
                    default_root.extend(tree)

        # TEMP
        #ET.dump(default_root)
        # clean command
        #clean_command = "rm -rf manifest_repo_{}".format(branch_dir)
        #ret_code, clean_result = launch_command( clean_command, True)

        return default_root, "manifest_repo_{}_{}".format(branch_dir, tag), project_rev

    def get_otp_manifest_for_repo(self, otp_branch, dir='default'):
        """get the otp manifest for this project manfifest

        Args:
            otp_branch (str): branch name
            dir (str, optional): addition to git clone directory name. Defaults to 'default'.

        Returns:
            Element: default_root, ET root element for the otp manfifest
            str: directory name for this otp manfifest repo containing otp branch_dir and 'dir' string
            str: otp_rev, revision for the otp manifest
        """
        # clone repo
        otp_repo = "p1/project/otp/manifest"
        if os.path.exists("manifest_repo_otp_{}_{}".format(otp_branch, dir)):
            # clean command
            clean_command = "rm -rf manifest_repo_otp_{}_{}".format(otp_branch, dir)
            ret_code, clean_result = launch_command( clean_command, True)

        clone_command = "git clone ssh://{}/{} manifest_repo_otp_{}_{}".format(self.GERRIT_HOST, otp_repo, otp_branch, dir)
        ret_code, result = launch_command( clone_command, True)
        if ret_code != 0:
            print( "Error on {} command:\n{}".format( clone_command, result ))
            sys.exit(1)
        # switch to branch or commit
        checkout_command = "cd manifest_repo_otp_{}_{}; git checkout {}".format(otp_branch, dir, otp_branch)
        ret_code, result = launch_command( checkout_command, True)
        if ret_code != 0:
            print( "Error on {} command:\n{}".format( clone_command, result ))
            sys.exit(1)

        # rev parse command
        rev_parse_cmd = "cd manifest_repo_otp_{}_{}; git rev-parse HEAD".format(otp_branch, dir)
        ret_code, otp_rev = launch_command( rev_parse_cmd, True)
        if ret_code != 0:
            print( "Error on {} command:\n{}".format( rev_parse_cmd, result ))
            sys.exit(1)
        else:
            otp_rev = otp_rev.strip()

        # get manifest(s) content
        default_root = None
        if os.path.exists( "manifest_repo_otp_{}_{}/default.xml".format(otp_branch, dir)):
            manifest_default = "manifest_repo_otp_{}_{}/default.xml".format(otp_branch, dir)
            default_root = ET.parse(manifest_default).getroot()
            if default_root == None:
                print("No default_root found for {}!".format(otp_branch))
                sys.exit(1)
        else:
            print ( "default.xml not found!" )

        return default_root, "manifest_repo_otp_{}_{}".format(otp_branch, dir), otp_rev

    def get_otp_framework_manifest_for_repo(self, otp_framework_branch, otp_framework_revision):
        """get the otp framework manifest content from Gerrit

        Args:
            otp_framework_branch (str): branch name
            otp_framework_revision (str): revision

        Returns:
            Element: ET root element for the otp framework manifest
        """
        # clone repo
        otp_repo = "p1/project/otp-framework/manifest"
        if otp_framework_branch is not None:
            clone_command = "git clone ssh://{}/{} -b {ofb} manifest_repo_otp_fw_{ofb}".format(self.GERRIT_HOST, otp_repo, ofb=otp_framework_branch)
            print("FRMWK   Branch != None ")
        else:
            clone_command = "git clone ssh://{}/{}  manifest_repo_otp_fw_{ofb}".format(self.GERRIT_HOST, otp_repo, ofb=otp_framework_branch)
            print("FRMWK   Branch == None ")

        ret_code, result = launch_command( clone_command, True)
        if ret_code != 0:
            print( "Error on {} command:\n{}".format( clone_command, result ))
            sys.exit(1)

        # load revision
        rev_command = "cd manifest_repo_otp_fw_{}; git checkout {}".format(otp_framework_branch, otp_framework_revision)
        ret_code, rev_result = launch_command( rev_command, True )
        if ret_code != 0:
            print( "Error on {} command:\n{}".format( rev_command, rev_result ))
            sys.exit(1)

        # get manifest(s) content
        default_root = None
        if os.path.exists( "manifest_repo_otp_fw_{}/default-framework.xml".format(otp_framework_branch)):
            manifest_default = "manifest_repo_otp_fw_{}/default-framework.xml".format(otp_framework_branch)
            default_root = ET.parse(manifest_default).getroot()
        else:
            print ( "default-framework.xml not found!" )
        # clean command
        clean_command = "rm -rf manifest_repo_otp_fw_{}".format(otp_framework_branch)
        ret_code, clean_result = launch_command( clean_command, True)

        return default_root

    def get_otp_hal_manifest_for_repo(self, otp_hal_branch, otp_hal_revision):
        """get otp hal manifest content from Gerrit

        Args:
            otp_hal_branch (str): brnach name
            otp_hal_revision (str): revision

        Returns:
            Element: ET root element for otp hal manifest
        """
        # clone repo
        otp_repo = "p1/project/otp-hal/manifest"
        # clone_command = "git clone ssh://{}/{} -b {ohb} manifest_repo_otp_hal_{ohb}".format(self.GERRIT_HOST, otp_repo, ohb=otp_hal_branch)
        if otp_hal_branch is not None:
            clone_command = "git clone ssh://{}/{} -b {ohb} manifest_repo_otp_hal_{ohb}".format(self.GERRIT_HOST, otp_repo, ohb=otp_hal_branch)
            print("OTPHAL  Branch != None ")
        else:
            clone_command = "git clone ssh://{}/{}  manifest_repo_otp_hal_{ohb}".format(self.GERRIT_HOST, otp_repo, ohb=otp_hal_branch)
            print("OTPHAL  Branch == None ")
        ret_code, result = launch_command( clone_command, True)
        if ret_code != 0:
            print( "Error on {} command:\n{}".format( clone_command, result ))
            sys.exit(1)

        # load revision
        rev_command = "cd manifest_repo_otp_hal_{}; git checkout {}".format(otp_hal_branch, otp_hal_revision)
        ret_code, rev_result = launch_command( rev_command, True )
        if ret_code != 0:
            print( "Error on {} command:\n{}".format( rev_command, rev_result ))
            sys.exit(1)

        # get manifest(s) content
        default_root = None
        if os.path.exists( "manifest_repo_otp_hal_{}/default-hal.xml".format(otp_hal_branch)):
            manifest_default = "manifest_repo_otp_hal_{}/default-hal.xml".format(otp_hal_branch)
            default_root = ET.parse(manifest_default).getroot()
        else:
            print ( "default-hal.xml not found!" )
        # clean command
        clean_command = "rm -rf manifest_repo_otp_hal_{}".format(otp_hal_branch)
        ret_code, clean_result = launch_command( clean_command, True)

        return default_root

    def get_otp_revision_from_manifest(self, default_root):
        """extract otp revision from manfest xml

        Args:
            default_root (Element): ET root element project manifest

        Returns:
            str: revision
        """
        otp_element = default_root.findall(".//project[@name='p1/project/otp/manifest']")
        if len(otp_element) == 0:
            otp_element = default_root.findall(".//include-project[@name='p1/project/otp/manifest']")
        print( "Revision for otp manifest is {}\n".format(otp_element[0].get('revision') ))
        return otp_element[0].get('revision')

    def get_otp_framework_revision_from_manifest(self, default_otp_root):
        """extract otp framework revision from otp manfest xml

        Args:
            default_otp_root (Element): ET root element otp manifest

        Returns:
            str: revision
            str: upstream name or revision if empty
        """
        # <project groups="framework" name="p1/project/otp-framework/manifest" path="platform-framework/manifest" revision="69e931e75a007ae81c4c351ef2222b13c36aa659" upstream="otp-framework-mdm9x50-sop-1.1.0.0">
        otp_element = default_otp_root.findall(".//project[@name='p1/project/otp-framework/manifest']")
        if len(otp_element) == 0:
            otp_element = default_otp_root.findall(".//include-project[@name='p1/project/otp-framework/manifest']")
        # set upstream to branch if not given:
        # only return last part ('/') from revision:
        revision = otp_element[0].get('revision').rsplit('/')[-1]
        upstream = otp_element[0].get('upstream')
        if upstream == None:
            upstream = revision
        print( "Revision for otp framework manifest is {}".format(revision))
        print( "Upstream for otp framework manifest is {}\n".format(upstream))

        return revision, upstream

    def get_otp_hal_revision_from_manifest(self, default_otp_root):
        """extract otp hal revision from otp manfest xml

        Args:
            default_otp_root (Element): ET root element otp manifest

        Returns:
            str: revision
            str: upstream name or revision if empty
        """
        # <project groups="framework" name="p1/project/otp-framework/manifest" path="platform-framework/manifest" revision="69e931e75a007ae81c4c351ef2222b13c36aa659" upstream="otp-framework-mdm9x50-sop-1.1.0.0">
        otp_element = default_otp_root.findall(".//project[@name='p1/project/otp-hal/manifest']")
        if len(otp_element) == 0:
            otp_element = default_otp_root.findall(".//include-project[@name='p1/project/otp-hal/manifest']")
        # set upstream to branch if not given:
        revision = otp_element[0].get('revision').rsplit('/')[-1]
        upstream = otp_element[0].get('upstream')
        if upstream == None:
            upstream = revision
        print( "Revision for otp hal manifest is {}".format(revision))
        print( "Upstream for otp framework manifest is {}\n".format(upstream))
        return revision, upstream

class OutputWriter(object):
    """class which is able to create html and/or csv output for the namifest contents

    Args:
        object (class): base class
    """
    def __init__(self, output_path, gerrit_host="buic-scm-ias.contiwan.com", gerrit_port="8443"):
        """constructor. setting needed vairables and creates output directory

        Args:
            output_path (str): path, where to write the requested output files
            gerrit_host (str, optional): Gerrit host. Defaults to "buic-scm-ias.contiwan.com".
            gerrit_port (str, optional): Gerrit port. Defaults to "8443".
        """
        self.output_path = output_path
        self.GERRIT_HOST="{}:{}".format(gerrit_host, gerrit_port)
        if os.path.exists(output_path) == False:
            os.makedirs(output_path, exist_ok=True)

    def _create_table_row(self, project):
        """create a table row for for the given project/repo name

        Args:
            project (Element): ET element refering to that project entry

        Returns:
            str: html table row
        """
        html = "<tr>"
        name_link = self.create_url_for_name_field(project.get('name'))
        html += '<td><a href="{}">{}</a></td>'.format(name_link, project.get('name'))
        html += '<td>{}</td>'.format(project.get('path'))
        if project.get('revision')!=None:
            revision_link = self.create_url_for_revision(project.get('name'), project.get('revision'))
            html += '<td><a href="{}">{}</a></td>'.format(revision_link, project.get('revision'))
        else:
            revision_link = self.create_url_for_revision(project.get('name'), 'master' )
            html += '<td><a href="{}">{}</a></td>'.format(revision_link, 'master')
        if project.get('upstream')!=None:
            upstream_link = self.create_url_for_upstream(project.get('name'), project.get('upstream'))
            html += '<td><a href="{}">{}</a></td>'.format(upstream_link, project.get('upstream'))
        else:
            html += ('<td></td>')
        if project.get('groups')!=None:
            html += '<td>{}</td>'.format(project.get('groups'))
        else:
            html += ('<td></td>')
        html += "</tr>\n"
        return html


    def write_manifest_contents_html(self, output_file_name, root):
        """create html file with manifest contents

        Args:
            output_file_name (str): file name of output html file
            root (Element): ET root element with all the manifest content
        """
        html = "<html>\n"
        html += "<br><b>{}</b><br><br>\n".format(output_file_name)
        html += '<table border="1">\n'
        html += "<tr><th>name</th><th>path</th><th>revision</th><th>upstream</th><th>groups</th></tr>\n"

        for included_project in root.findall('include-project'):
            html += self._create_table_row(included_project)

        for project in root.findall('project'):
            html += self._create_table_row(project)
        html += "</table>\n</html>\n"

        mode = 'w'
        outputFile = open("{}/{}".format(self.output_path, output_file_name), mode)
        outputFile.write( html )
        outputFile.close()

    def write_manifest_contents_file(self, output_file_name, root ):
        """writes the manifest contents to a file in CSV style

        Args:
            output_file_name (str): ouput file name (csv file name)
            root (Element): ET root element with all the manifest content
        """
        mode = 'w'
        delim = ';'
        if sys.version_info.major < 3:
            mode += 'b+'
            outputFile = open("{}/{}".format(self.output_path, output_file_name), mode)
        else:
            outputFile = open("{}/{}".format(self.output_path, output_file_name), mode, newline='', encoding='utf-8')

        outputWriter = csv.writer(outputFile, delimiter=delim)

        outputWriter.writerow( ["name", "path", "revision", "rev link", "upstream", "upstream link", "groups"] )

        for project in root.findall('project'):
            attribs = []
            attribs.append( self.create_excel_link_for_name_field(project.get('name')) )
            attribs.append( project.get('path') )
            if project.get('revision')!=None:
                attribs.append( project.get('revision') )
                attribs.append( self.create_url_for_revision(project.get('name'), project.get('revision')) )
            else:
                attribs.append( 'master' )
                attribs.append( self.create_url_for_revision(project.get('name'), 'master' ) )
            if project.get('upstream')!=None:
                attribs.append( project.get('upstream') )
                attribs.append( self.create_url_for_upstream(project.get('name'), project.get('upstream')) )
            else:
                attribs.append( '' )
                attribs.append( '' )
            if project.get('groups')!=None:
                attribs.append( project.get('groups') )
            else:
                attribs.append( '' )

            outputWriter.writerow(attribs)

        outputFile.close()

    def create_excel_link(self, url, field_name):
        """create an excel link out ot the given url

        Args:
            url (str): base url
            field_name (str): Excel field name for the link

        Returns:
            str: result Excel link
        """
        """ format for name field link is:
        https://buic-scm-rbg.contiwan.com:8443/#/admin/projects/p1/package/qualcomm/qcom-mdm9x50-le-2-3-modem
        """
        link = "=HYPERLINK(\"{}\";\"{}\")".format( url, field_name)
        return link

    def create_excel_link_for_name_field(self, name):
        """create an excel link for the name field out ot the given url

        Args:
            url (str): base url
            name (str): Excel name field name for the link

        Returns:
            str: result Excel link
        """
        """ format for name field link is:
        https://buic-scm-rbg.contiwan.com:8443/#/admin/projects/p1/package/qualcomm/qcom-mdm9x50-le-2-3-modem
        """
        name_url = "https://{}/#/admin/projects/{}".format( self.GERRIT_HOST, name )
        name_link = "=HYPERLINK(\"{}\";\"{}\")".format( name_url, name)
        return name_link

    def create_url_for_name_field(self, name):
        """create a Gerrit url for the name field in a html table

        Args:
            name (str): name string for the Gerrit url

        Returns:
            str: name_url, resulting url for name field
        """
        """ format for name field link is:
        https://buic-scm-rbg.contiwan.com:8443/#/admin/projects/p1/package/qualcomm/qcom-mdm9x50-le-2-3-modem
        """
        name_url = "https://{}/#/admin/projects/{}".format( self.GERRIT_HOST, name )
        return name_url

    def create_url_for_upstream(self, name, upstream):
        """create a Gerrit url for the upstream field in a html table

        Args:
            name (str): name string for Gerrit needed for the url
            upstream (str): upstream string for Gerrit link

        Returns:
            str: upstream_url, resulting url for upstream field
        """
        """ format for upstream link is:
        https://buic-scm-rbg.contiwan.com:8443/gitweb?p=p1%2Fpackage%2Fqualcomm%2Fqcom-mdm9x50-le-2-3-modem.git;a=shortlog;h=refs%2Fheads%2Fr00080.1_cas
        """
        upstream_url = "https://{}/gitweb?p={}.git;a=shortlog;h={}".format( self.GERRIT_HOST, name, upstream )
        return upstream_url

    def create_url_for_revision(self, name, revision):
        """create a Gerrit url for the revision field in a html table

        Args:
            name (str): name string for Gerrit needed for the url
            revision (str): revision for Gerrit link

        Returns:
            str: revision_url, resulting url for upstream field
        """
        """ format for revision link is:
        https://buic-scm-rbg.contiwan.com:8443/gitweb?p=p1/package/qualcomm/qcom-mdm9x50-le-2-3-modem.git;a=commit;h=575cdf1cc794fc0ead0f4c663879274775356210
        """
        revision_url = "https://{}/gitweb?p={}.git;a=commit;h={}".format( self.GERRIT_HOST, name, revision )
        return revision_url

class IncludedReleases(object):
    """class combining reading of manifests and writing of it's complete content

    Args:
        object (class): base class
    """
    def __init__(self, manifestRetriever, outputWriter, project_name, version_branch, version_tag=None, consider_included_mfsts=False, commit_ref=None ) -> None:
        """constructor: variable initialisation

        Args:
            manifestRetriever (class): instance of ManifestRetriever class
            outputWriter (class): instance of OutputWriter class
            project_name (str): the name of the handled project
            version_branch (str): manifest branch as string
            version_tag (str, optional): manfest tag string. Defaults to None.
            consider_included_mfsts (bool, optional): option to also handle included manifests (<include...). Defaults to False.
            commit_ref (str, optional): commit reference to fetch. Defaults to None.
        """
        self.manifestRetriever = manifestRetriever
        self.outputWriter = outputWriter
        self.project_name = project_name
        self.version_branch = version_branch
        self.version_tag = version_tag
        self.consider_included_mfsts = consider_included_mfsts
        self.commit_ref = commit_ref
        self.project_rev = None
        self.project_manifest_location = None
        self.otp_rev =  None
        self.otp_manifest_location = None
        self.projects = []
        self.default_project_root = None
        self.default_otp_root = None
        self.otp_hal_root = None
        self.otp_framework_root = None

    def getProjectRev(self):
        """get project revision

        Returns:
            str: project revision
        """
        return self.project_rev

    def getProjectManifestLocation(self):
        """get the project manifest location (path)

        Returns:
            str: project manifest location
        """
        return self.project_manifest_location

    def getOtpRev(self):
        """get otp revision

        Returns:
            str: otp revision
        """
        return self.otp_rev

    def getOtpManifestLocation(self):
        """get the otp manifest location (path)

        Returns:
            str: otp manifest location
        """
        return self.otp_manifest_location

    def getProjectsList(self):
        """get the full list of projects/repos included in the manifest

        Returns:
            list: projects/repos as list
        """
        return self.projects

    def getDefaultOtpRoot(self):
        """get the otp root Element tree

        Returns:
            Element: ET root element for the otp manifest
        """
        return self.default_otp_root

    def getOtpHalRoot(self):
        """get the otp hal root Element tree

        Returns:
            Element: ET root element for the otp hal manifest
        """
        return self.otp_hal_root

    def getOtpFrameworkRoot(self):
        """get the otp framework root Element tree

        Returns:
            Element: ET root element for the otp framework manifest
        """
        return self.otp_framework_root

    def getDefaultProjectRoot(self):
        """get the project root Element tree

        Returns:
            Element: ET root element for the project manifest
        """
        return self.default_project_root

    def processProjectManifest(self, dir="default"):
        """complete processing of the project manifest contents including creating the xml trees out of the manifest.
        for the output part, there are currently only html pages created, no csv files!

        Args:
            dir (str, optional): optional ending for the directories. Very useful for later compare operations. Defaults to "default".

        Returns:
            list: resulting projects/repos list
        """
        # get informations for base repo version
        if self.project_name != "otp":
            self.default_project_root, self.project_manifest_location, self.project_rev = self.manifestRetriever.get_project_manifest_for_repo(self.version_branch, self.version_tag, consider_includes=self.consider_included_mfsts, manifest_commit_ref=self.commit_ref)
            #self.outputWriter.write_manifest_contents_file("included_releases_project_{}.csv".format(project_branch), default_project_root)
            self.outputWriter.write_manifest_contents_html("included_releases_{}_{}.html".format(self.version_branch, self.version_tag), self.default_project_root)
            otp_branch = self.manifestRetriever.get_otp_revision_from_manifest(self.default_project_root)
        else:
            otp_branch = self.version_branch
            self.default_project_root = None
        self.default_otp_root, self.otp_manifest_location, self.otp_rev = self.manifestRetriever.get_otp_manifest_for_repo(otp_branch, dir)
        #new_ouputWriter.write_manifest_contents_file("included_releases_otp_{}.csv".format(new_otp_branch), new_default_otp_root)
        self.outputWriter.write_manifest_contents_html("included_releases_otp_{}.html".format(otp_branch), self.default_otp_root)
        otp_framework_revision, otp_framework_upstream = self.manifestRetriever.get_otp_framework_revision_from_manifest(self.default_otp_root)
        self.otp_framework_root = self.manifestRetriever.get_otp_framework_manifest_for_repo(otp_framework_upstream, otp_framework_revision)
        #self.outputWriter.write_manifest_contents_file("included_releases_otp_framework_{}_{}.csv".format(otp_framework_upstream, otp_framework_revision), otp_framework_root )
        self.outputWriter.write_manifest_contents_html("included_releases_otp_framework_{}_{}.html".format(otp_framework_upstream, otp_framework_revision), self.otp_framework_root )
        otp_hal_revision, otp_hal_upstream = self.manifestRetriever.get_otp_hal_revision_from_manifest(self.default_otp_root)
        self.otp_hal_root = self.manifestRetriever.get_otp_hal_manifest_for_repo(otp_hal_upstream, otp_hal_revision)
        #self.outputWriter.write_manifest_contents_file("included_releases_otp_hal_{}_{}.csv".format(otp_hal_upstream, otp_hal_revision), otp_hal_root )
        self.outputWriter.write_manifest_contents_html("included_releases_otp_hal_{}_{}.html".format(otp_hal_upstream, otp_hal_revision), self.otp_hal_root )
        # fill resulting projects list
        self.projects = []
        if self.default_project_root != None:
            self.projects.extend( self.default_project_root.findall("include-project"))
            self.projects.extend( self.default_project_root.findall("project"))
        if self.consider_included_mfsts == True:
            self.projects.extend( self.default_otp_root.findall("include-project"))
            self.projects.extend( self.default_otp_root.findall("project"))
            self.projects.extend( self.otp_framework_root.findall("project"))
            self.projects.extend( self.otp_hal_root.findall("project"))
        if self.default_project_root != None:
            repos_rm = self.default_project_root.findall("remove-project")
            repos_extd = self.default_project_root.findall("extend-project")
            self.manifestRetriever.remove_and_extend_projects(self.projects, repos_rm, repos_extd)
        return self.projects

    def printDuplicates(self):
        """prints a list of duplicate projects/repos in the project list. Useful for analysis of bugs...
        """
        for project in self.projects:
            p_name = project.get('name')
            p_rev = project.get('revision')
            first_hit = True
            for base_project in self.projects:
                if p_name == base_project.get('name') and p_rev == base_project.get('revision'):
                    if first_hit == True:
                        first_hit = False
                    else:
                        print("{}, {} is duplicate!".format(p_name, p_rev))

if __name__ == '__main__':
    """main function. Can be called directly with all needed parameters. Will generate html and csv output files for the given project manifest
    """
    # get input and output file
    args = parseargs()
    manifestRetreiver = ManifestRetreiver(args.host_name, args.project)
    ouputWriter = OutputWriter(args.output_path, args.host_name)

    if args.project != "otp":
        default_root, platform_overrides_root = manifestRetreiver.get_project_manifest_for_repo(args.branch)
        ouputWriter.write_manifest_contents_file("included_releases_{}_{}_default.csv".format(args.branch, args.project), default_root)
        ouputWriter.write_manifest_contents_html("included_releases_{}_{}_default.html".format(args.branch, args.project), default_root)
        if platform_overrides_root != None:
            ouputWriter.write_manifest_contents_file("included_releases_{}_{}_platform_overrides.csv".format(args.branch, args.project), platform_overrides_root)
            ouputWriter.write_manifest_contents_html("included_releases_{}_{}_platform_overrides.html".format(args.branch, args.project), platform_overrides_root)

        otp_branch = manifestRetreiver.get_otp_revision_from_manifest(default_root)
    else:
        otp_branch = args.branch

    default_otp_root, default_otp_path, default_otp_rev = manifestRetreiver.get_otp_manifest_for_repo(otp_branch)
    ouputWriter.write_manifest_contents_file("included_releases_{}_otp_{}.csv".format(args.branch, otp_branch), default_otp_root)
    ouputWriter.write_manifest_contents_html("included_releases_{}_otp_{}.html".format(args.branch, otp_branch), default_otp_root)

    otp_framework_revision, otp_framework_upstream = manifestRetreiver.get_otp_framework_revision_from_manifest(default_otp_root)
    otp_framework_root = manifestRetreiver.get_otp_framework_manifest_for_repo(otp_framework_upstream, otp_framework_revision)
    ouputWriter.write_manifest_contents_file("included_releases_{}_otp_framework_{}_{}.csv".format(args.branch, otp_framework_upstream, otp_framework_revision), otp_framework_root )
    ouputWriter.write_manifest_contents_html("included_releases_{}_otp_framework_{}_{}.html".format(args.branch, otp_framework_upstream, otp_framework_revision), otp_framework_root )

    otp_hal_revision, otp_hal_upstream = manifestRetreiver.get_otp_hal_revision_from_manifest(default_otp_root)
    otp_hal_root = manifestRetreiver.get_otp_hal_manifest_for_repo(otp_hal_upstream, otp_hal_revision)
    ouputWriter.write_manifest_contents_file("included_releases_{}_otp_hal_{}_{}.csv".format(args.branch, otp_hal_upstream, otp_hal_revision), otp_hal_root )
    ouputWriter.write_manifest_contents_html("included_releases_{}_otp_hal_{}_{}.html".format(args.branch, otp_hal_upstream, otp_hal_revision), otp_hal_root )

