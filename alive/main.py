from __future__ import print_function

import argparse
import os
import pwd
import socket
import sys
import traceback

from .config import Config
from .config import DEFAULT_CONFIG_DIR
from .email_message import EmailMessage
from .sources import SOURCES


DEFAULT_EMAIL_SUBJECT = 'Safety information message'


class Alive(object):
    def __init__(self):
        self.args = None
        self._config = None

    def _add_global_arguments(self, argument_parser):
        argument_parser.add_argument(
            '-c', '--config-dir', metavar='dir', default=DEFAULT_CONFIG_DIR,
            help='Configuration directory (default: %(default)s)')
        argument_parser.add_argument(
            '-d', '--debug', action='store_true',
            help='Debug mode (don\'t send email)')

    @property
    def config(self):
        if not self._config:
            self._config = Config(self.args.config_dir)
        return self._config

    def check(self):
        ap = argparse.ArgumentParser()
        self._add_global_arguments(ap)
        # List loaded sources
        loaded_sources = {
            source.name: source
            for source in SOURCES
        }
        all_sources_choice = 'all'
        ap.add_argument('source', metavar='source',
                        nargs='*',
                        default=all_sources_choice,
                        choices=([all_sources_choice] +
                                 list(loaded_sources.keys())),
                        help=('Source(s) to check (default: %(default)s, '
                              'choices: %(choices)s)'))
        self.args = ap.parse_args()
        if self.args.source == all_sources_choice:
            self.args.source = loaded_sources
        for source in self.args.source:
            for source_text, is_test in \
                    loaded_sources[source](self.config).check():
                self._send_email(source_text, is_test)

    def main(self):
        ap = argparse.ArgumentParser()
        self._add_global_arguments(ap)
        ap.add_argument('message', metavar='message', nargs='*',
                        default='',
                        help='Message to send')
        ap.add_argument('-t', '--test', dest='test', action='store_true',
                        help='Test (send outgoing message to sender only)')
        self.args = ap.parse_args()
        user_name = pwd.getpwuid(os.getuid())[0]
        source_text = ('An interactive command run by the user {} on the '
                       'computer {}'
                       .format(user_name, socket.gethostname()))
        if self.args.message:
            source_text += os.linesep.join([
                ' with the following text: ',
                '',
                ' '.join(self.args.message or '')
            ])
        self._send_email(source_text, self.args.test)

    def _prepend_to_message(self, message, prepend_text):
        return os.linesep.join([
            prepend_text,
            '',
            '----',
            '',
            '{}',
        ]).format(message)

    def _send_email(self, source_text, is_test=False):
        if 'email' not in self.config or not self.config.email:
            raise Exception('No email configuration present')
        sender = self.config.email.get('from')
        if not sender:
            raise Exception('Email sender is not configured')
        if is_test:
            to = sender
            cc = None
            bcc = None
        else:
            to = self.config.email.get('to')
            cc = self.config.email.get('cc')
            bcc = self.config.email.get('bcc')
        if not to:
            raise Exception('Email recipient(s) are not configured')
        subject = self.config.email.get('subject', DEFAULT_EMAIL_SUBJECT)
        if is_test:
            subject = '[TEST MESSAGE] {}'.format(subject)
        attachments = self.config.email.get('attachments') or []
        if isinstance(attachments, str):
            attachments = []
        message = self.config.email.get('message', '').strip()
        if len(message.splitlines()) == 1 and os.path.isfile(message):
            message = open(message, 'r').read().strip()
        message = self._prepend_to_message(
            message,
            os.linesep.join(['This automatic message was triggered by:',
                             source_text]))
        if is_test:
            message = self._prepend_to_message(
                message,
                'This is a test message being sent only to yourself.')

        email = None
        email_kwargs = dict(
            sender=sender,
            to=to,
            cc=cc,
            bcc=bcc,
            subject=subject,
            message=message,
            attachments=attachments,
            flowed=True,
            sign=True,
            sign_fallback=True,
            attach_errors=True
        )
        try:
            email = EmailMessage(**email_kwargs)
            if self.args.debug:
                print(email)
            if not self.args.debug:
                email.send()
        except Exception:
            message = os.linesep.join(
                [
                    'There was an error sending the message:',
                    ''
                ] + traceback.format_exc().splitlines()
            )
            email_kwargs.update(dict(
                to=sender,
                cc=None,
                bcc=None,
                subject='[ERROR] {}'.format(subject),
                message=message
            ))
            error_email = EmailMessage(**email_kwargs)
            try:
                if email:
                    error_email.attach_text_as_file(str(email),
                                                    'original_message.txt')
            except Exception as e:
                print('Exception attaching original message to error email: {}'
                      .format(e),
                      file=sys.stderr)
            if self.args.debug:
                print(error_email)
            if not self.args.debug:
                error_email.send()
        finally:
            if not email:
                raise Exception('No email message was generated!')


def check():
    a = Alive()
    a.check()


def main():
    a = Alive()
    a.main()
