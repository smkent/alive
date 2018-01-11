from __future__ import print_function

from email.message import Message
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.encoders import encode_base64
import mimetypes
import os
import subprocess
import sys
import traceback

import gnupg

# https://tools.ietf.org/html/rfc4880#section-9.4
OPENPGP_HASH_ALGORITHMS = {
    1: 'MD5',
    2: 'SHA1',
    3: 'RIPEMD160',
    8: 'SHA256',
    9: 'SHA384',
    10: 'SHA512',
    11: 'SHA224',
}


class EmailMessage(object):
    def __init__(self, sender, to, subject, message,
                 cc=None, bcc=None, attachments=[], sign=False,
                 sign_fallback=False,
                 message_type='plain',
                 message_encoding='us-ascii',
                 flowed=False,
                 attach_errors=False):
        self.to = self._addrs_to_list(to)
        self.cc = self._addrs_to_list(cc)
        self.bcc = self._addrs_to_list(bcc)
        self.sender = sender
        self.subject = subject
        self.email = MIMEMultipart()
        self.sign = sign
        self.sign_fallback = sign_fallback
        self.attach_errors = attach_errors
        self._errors = []
        self._email_string = None
        text = MIMEText(message, message_type, message_encoding)
        if flowed:
            old_content_type = text['Content-Type']
            del text['Content-Type']
            text['Content-Type'] = old_content_type + '; format="flowed"'
        self.email.attach(text)
        attach_errors_list = []
        for filename in self._generate_attachments(attachments):
            try:
                self.attach_file(filename)
            except:
                if not self.attach_errors:
                    raise
                attach_errors_list.append(traceback.format_exc())
        for attach_error in attach_errors_list:
            self._attach_error(attach_error)

    def __str__(self):
        if not self._email_string:
            if self.sign:
                self._sign_message()
            self.email['From'] = self.sender
            self.email['To'] = self._addrs_to_str(self.to)
            if self.cc:
                self.email['Cc'] = self._addrs_to_str(self.cc)
            if self.bcc:
                self.email['Bcc'] = self._addrs_to_str(self.bcc)
            self.email['Subject'] = self.subject
            self._email_string = self.email.as_string()
        return self._email_string

    def _generate_attachments(self, attachments):
        for attachment in attachments:
            if os.path.isdir(attachment):
                for filename in os.listdir(attachment):
                    if filename.startswith('.'):
                        continue
                    file_path = os.path.join(attachment, filename)
                    if os.path.isfile(file_path):
                        yield file_path
            else:
                yield attachment

    def attach_file(self, filename):
        mimetype, encoding = mimetypes.guess_type(filename)
        mimetype = mimetype or 'application/octet-stream'
        mimetype = mimetype.split('/', 1)
        fp = open(filename, 'rb')
        attachment = MIMEBase(mimetype[0], mimetype[1])
        attachment.set_payload(fp.read())
        fp.close()
        encode_base64(attachment)
        attachment.add_header('Content-Disposition', 'attachment',
                              filename=os.path.basename(filename))
        self.email.attach(attachment)

    def attach_text_as_file(self, text, filename='attachment.txt',
                            mimetype='text/plain'):
        mimetype = mimetype.split('/', 1)
        attachment = MIMEBase(mimetype[0], mimetype[1])
        attachment.set_payload(text)
        encode_base64(attachment)
        attachment.add_header('Content-Disposition', 'attachment',
                              filename=filename)
        self.email.attach(attachment)

    def send(self):
        content = str(self)
        sendmail_process = subprocess.Popen(['/usr/sbin/sendmail', '-t',
                                             '-f', self.sender],
                                            stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
        if not isinstance(content, bytes):
            content = bytes(str(content), 'UTF-8')
        sendmail_process.stdin.write(content)
        return sendmail_process.communicate()

    def _addrs_to_list(self, addrs):
        if not addrs:
            return []
        return list(addrs) if isinstance(addrs, (list, dict)) else [addrs]

    def _addrs_to_str(self, addrs):
        return ', '.join(addrs)

    def _sign_message(self):
        try:
            gnupg_dir = os.path.join(os.path.expanduser('~'), '.gnupg')
            if not os.path.isdir(gnupg_dir):
                raise Exception('{} does not exist'.format(gnupg_dir))
            gnupg_options = []
            if not sys.stdout.isatty():
                gnupg_options.append('--pinentry-mode=cancel')
            gpg = gnupg.GPG(gnupghome=gnupg_dir, options=gnupg_options)
            text_to_sign = self.email.as_string().replace('\n', '\r\n')
            signature = gpg.sign(text_to_sign, detach=True)
            if not signature:
                raise Exception('Email signature creation failed!')
            signature_attachment = Message()
            signature_attachment['Content-Type'] = \
                'application/pgp-signature; name="signature.asc"'
            signature_attachment['Content-Description'] = 'Digital signature'
            signature_attachment.set_payload(str(signature))
            algorithm_str = \
                OPENPGP_HASH_ALGORITHMS.get(int(signature.hash_algo))
            if not algorithm_str:
                raise Exception('Email signature created with unknown hash '
                                'algorithm type {}'
                                .format(signature.hash_algo))
            signed_email = MIMEMultipart(
                _subtype='signed',
                protocol='application/pgp-signature',
                micalg='pgp-{}'.format(algorithm_str.lower()))
            signed_email.attach(self.email)
            signed_email.attach(signature_attachment)
            self.email = signed_email
        except Exception as e:
            if not self.sign_fallback:
                if self.attach_errors:
                    self._attach_error(traceback.format_exc())
                else:
                    raise
            print('WARNING: {}'.format(e), file=sys.stderr)

    def _attach_error(self, error):
        error_attachment = MIMEBase('text', 'plain')
        error_attachment.add_header('Content-Disposition', 'attachment',
                                    filename='error.txt')
        error_attachment.set_payload(error)
        self.email.attach(error_attachment)
