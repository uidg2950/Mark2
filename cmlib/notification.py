#!/usr/bin/python
"""
# *****************************************************************************
# *
# *  (c) 2016-2021 Continental Automotive Systems, Inc., all rights reserved
# *
# *  All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# *  Any reproduction of this material without written consent from
# *  Continental Automotive Systems, Inc. is strictly forbidden.
# *
# *  Filename:      notification.py
# *
# *  Description:   This file contains all email notification related classes
# *
# *****************************************************************************
"""
import codecs
import mimetypes
import os
import re
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid

from cmlib import sanitize
from cmlib.request import http_request, STATUS_CODES

COMMASPACE = ', '

rest_api_server = "qh00380vmx.qh.us.int.automotive-wan.com"
email_server = rest_api_server

email_defaults = {
    'reply_to': '07WWMGTPINT@conti.de',
    'build_user': 'Jenkins Automation',
    'build_user_email': 'evo_cm_admin.au_ww_sa@continental-corporation.com',
    'email_server': email_server,
    'email_port': 1025,
    'endpoint': '/api/sendmail'
}

cmlib_dir = os.path.realpath('.')
launchers = os.path.join(cmlib_dir, '.launchers')
if os.path.exists(launchers):
    cmlib_dir = launchers
cmlib_dir = os.path.normpath(cmlib_dir)

def map_images(text):
    """ Based on an html document as a string identify all images referenced as <img> """
    return_value = dict()
    images = re.findall(r'<img .+?/?>', text)
    for image in images:
        match = re.search('src="([^"]+?)"', image)
        path = match.group(1)
        key = os.path.basename(path)
        if key not in return_value:
            cid = make_msgid()
            # peel the <> off the cid for use in the html
            return_value.update({key: {'cid': cid[1:-1], 'path': path}})
        else:
            print('Already cached: ', key)

    return return_value

class Notification:
    """ Handles Email Notifications via SMTP """

    def __init__(self, sender_name, sender_email, send_to, filename, attachment_path=None,
                 server=None, port=0, aDomain=None, aEncoding=None):

        # defaults
        self._port = port if port else email_defaults['email_port']
        default_server = "http://{}:{}{}".format(email_defaults['email_server'],
                                                 self._port,
                                                 email_defaults['endpoint'])
        self._server = server if server else default_server
        self._domain = 'aumovio.com' if aDomain is None else ''
        self._encoding = 'utf-8' if aEncoding is None else aEncoding
        self._sender_name = sanitize.sanitizeString(sender_name)
        self._sender_email = sanitize.sanitizeEmail(sender_email, self._domain)
        self._send_to = []
        self._filename = sanitize.sanitizeString(filename)
        self._attachment = sanitize.sanitizeString(attachment_path)
        self._subject = '{}'.format(self._filename)
        self.images_cid = dict()

        if not isinstance(send_to, list):
            send_to = [send_to.strip() for send_to in send_to.split(',')]
        self.send_to = send_to

        # Distribution list, or config files should be used
        replyTo = ""
        reply_to = email_defaults['reply_to'].split(',')
        for i, reply in enumerate(reply_to):
            replyTo += reply + ", " if i < len(reply_to) - 1 else reply
        self._replyTo = replyTo

        # Force MIME
        content_type, encoding = mimetypes.guess_type(self._filename)
        if content_type is None or encoding is not None:
            # No guess could be made, or the file is encoded (compressed)
            # so use a generic bag-of-bits type.
            content_type = 'application/octet-stream'
        self.content_type = content_type
        self._maintype, self._subtype = self.content_type.split('/')

        # Forge the MIME message
        self.msg = MIMEMultipart('related')
        self.msg['To'] = self.send_to
        self.msg['From'] = '{} <{}>'.format(self._sender_name, self._sender_email)
        self.msg['Reply-To'] = self._replyTo

    @property
    def server(self):
        return self._server

    @property
    def domain(self):
        return self._domain

    @domain.setter
    def domain(self, value):
        self._domain = value

    @property
    def encoding(self):
        return self._encoding

    @encoding.setter
    def encoding(self, value):
        self._encoding = value

    @property
    def sender_name(self):
        return self._sender_name

    @property
    def sender_email(self):
        return self._sender_email

    @property
    def send_to(self):
        return COMMASPACE.join(self._send_to)

    @send_to.setter
    def send_to(self, value):
        """Convert from string into an email list

        Currently is only looking 1 level in deepness

        :param value:
        :return:
        """
        parsed_send_to = []
        email_config_dir = os.path.join(cmlib_dir, 'config/documents/notification')
        email_config_dir = os.path.realpath(email_config_dir)

        print("Looking for Destination(s) {} in {}".format(value, email_config_dir))
        distribution_files = {}
        for root, _, files in os.walk(email_config_dir):
            distribution_files = {filename: os.path.join(root, filename) for filename in files}

        for element in value:
            element = element.lower()
            if element in distribution_files:
                email_config_path = distribution_files[element]
                with open(email_config_path) as email_config_file:
                    recipient = email_config_file.read()
                    recipient_list = recipient.splitlines()
                    for recipient in recipient_list:
                        if recipient.startswith('#'):
                            pass  # Skipp comments
                        elif recipient.startswith('@'):
                            # TODO: avoid recursion
                            recipient = recipient[1:]
                            recipient_config_path = distribution_files[recipient]
                            with open(recipient_config_path) as recipient_config_file:
                                recipients = recipient_config_file.read().splitlines()
                                for sub_recipient in recipients:
                                    if sub_recipient.startswith('#')\
                                            or sub_recipient.startswith('@')\
                                            or sub_recipient in parsed_send_to:
                                        pass
                                    else:
                                        parsed_send_to.append(sub_recipient)
                        else:
                            parsed_send_to.append(recipient)
            else:
                parsed_send_to.append(element)

        email_values = [sanitize.sanitizeEmail(e, self._domain) for e in parsed_send_to]
        self._send_to = email_values

    @property
    def subject(self):
        """ Getter for private property subject """
        return self._subject

    @property
    def content(self):
        """ Drop the contents for the local filename into a str with the parsed images attached """
        with codecs.open(self._filename, "r", 'ascii', 'ignore') as file_src:
            content = file_src.read()  # email needs ascii

        # Tag images map
        if self.content_type == 'text/html':
            self.images_cid = map_images(content)

        return content

    @property
    def message(self):
        """ Get the whole text and replace images """
        # Calculate the contents
        content = self.content

        # Replace the references to images with cid calls
        for _, attr in self.images_cid.items():
            cid = attr['cid']
            path = attr['path']
            content = content.replace(path, 'cid:' + cid)

        # Set the content for the email with CID references
        mime_text = MIMEText(content, self._subtype)
        self.msg.attach(mime_text)

        # Append the CID base64 contents
        for image_name, attr in self.images_cid.items():
            image_path = attr['path']
            if os.path.exists(image_path):
                with open(image_path, 'rb') as img:
                    msg_image = MIMEImage(img.read())
                    msg_image.add_header('Content-ID', attr['cid'])
                    self.msg.attach(msg_image)
            else:
                print("Unable to locate [{}]: {}".format(image_name, image_path))

        return self.msg.as_string()

    @property
    def filename(self):
        """ Getter for private property filename """
        return self._filename

    @filename.setter
    def filename(self, value):
        """ Sets the filename """
        self._filename = value

    def send(self):
        """ Wrapper for sending the message """
        self.msg['Subject'] = self.subject
        email = {
           # TP-113845: remove sender in call api rest for email service
           # The configuration and credentials for the email service are going
           # to be used in the email service application. As practices of
           # microservices.
           # "sender_email": self._sender_email,
            "sent_to": self._send_to,
            "subject": self.subject
        }

        if self.content_type == "text/html":
            email['html'] = self.content
        else:
            email['text'] = self.content

        response = http_request(self._server, "POST", json=email)
        if response and response.status_code == STATUS_CODES['ok']:
            print("Successfully sent email!")
        else:
            print("Error: unable to send email...")
            print(response)

    def __str__(self):
        rstring = """
            Server:    {0}
            Sender:    {1}
            Reply-To:  {2}
            Send to:   {3}
            Subject:   {4}
            Filename:  {5}
            Attachment:  {6}
        """
        return rstring.format(self._server, self._sender_email, self._replyTo, self.send_to,
                              self.subject, self._filename, self._attachment)


class BuildNotification(Notification):
    """docstring for BuildNotification"""

    def __init__(self, sender_name, sender_email, send_to, filename, baseline_name, release_id,
                 configuration='success', attachment_path=None, smtp_server=None, domain=None,
                 encoding=None):
        super(BuildNotification, self).__init__(sender_name, sender_email, send_to, filename,
                                                attachment_path, smtp_server, domain, encoding)
        self._baseline = sanitize.sanitizeString(baseline_name)
        self._release = sanitize.sanitizeString(release_id)
        self._configuration = sanitize.sanitizeString(configuration)

        if release_id != 'failed' and self._configuration != 'failed':
            self._subject = "{0} - Baseline built: {1}".format(self._release, self._baseline)
        else:
            self._subject = "{0} - Baseline built, failed: {1}".format(self._release, self._baseline)

    @property
    def baseline(self):
        """ Getter for private property baseline """
        return self._baseline


class ReleaseNotification(Notification):
    """docstring for BuildNotification"""

    def __init__(self, sender_name, sender_email, send_to, filename, aBaseline, aRelease, aStatus,
                 server=None, aDomain=None, aEncoding=None):
        super(ReleaseNotification, self).__init__(sender_name, sender_email, send_to, filename,
                                                  server, aDomain, aEncoding)
        self._baseline = sanitize.sanitizeString(aBaseline)
        self._release = sanitize.sanitizeString(aRelease)
        self._status = sanitize.sanitizeString(aStatus)

        self._subject = "{0} - {1} SW available for INTERNAL TESTING"\
            .format(self._release, self._baseline)

    @property
    def baseline(self):
        return self._baseline


class ReportNotification(Notification):
    """docstring for ReportNotification"""

    def __init__(self, sender_name, sender_email, send_to, filename, aSubject, server=None,
                 aDomain=None, aEncoding=None):
        super(ReportNotification, self).__init__(sender_name, sender_email, send_to, filename,
                                                 server, aDomain, aEncoding)
        self._subject = sanitize.sanitizeString(aSubject)

    @property
    def subject(self):
        return self._subject
