#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Isomer - The distributed application framework
# ==============================================
# Copyright (C) 2011-2019 Heiko 'riot' Weinen <riot@c-base.org> and others.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


__author__ = "Heiko 'riot' Weinen"
__license__ = "AGPLv3"

"""


Module MailTransmitter
======================


"""

from email.mime.text import MIMEText
from smtplib import SMTP, SMTP_SSL
from socket import timeout

from circuits import Event, Worker, task
from isomer.component import ConfigurableComponent, handler
from isomer.database import objectmodels
from isomer.debugger import cli_register_event
from isomer.logger import verbose, error
from isomer.mail import send_mail
from isomer.schemata.defaultform import fieldset
from isomer.tool import run_process
from pystache import render


def send_mail_worker(config, mail, event):
    """Worker task to send out an email, which is a blocking process unless
     it is threaded"""
    log = ""

    try:
        if config.get('ssl', True):
            server = SMTP_SSL(config['server'], port=config['port'], timeout=30)
        else:
            server = SMTP(config['server'], port=config['port'], timeout=30)

        if config['tls']:
            log += 'Starting TLS\n'
            server.starttls()

        if config['username'] != '':
            log += 'Logging in with ' + str(config['username']) + "\n"
            server.login(config['username'], config['password'])
        else:
            log += 'No username, trying anonymous access\n'

        log += 'Sending Mail\n'
        response_send = server.send_message(mail)
        server.quit()

    except timeout as e:
        log += 'Could not send email: ' + str(e) + "\n"
        return False, log, event

    log += 'Server response:' + str(response_send)
    return True, log, event


class cli_test_mail(Event):
    pass


class MailTransmitter(ConfigurableComponent):
    """Transmits mail to multiple accounts"""

    configprops = {
        'mail_send': {
            'type': 'boolean',
            'title': 'Send emails',
            'description': 'Generally toggle email sending (for Debugging)',
            'default': True
        },
        'default_account': {
            'type': 'string',
            'title': 'Default profile',
            'description': 'Name of default mail server configuration',
            'default': 'localhost'
        },
        'accounts': {
            'type': 'array',
            'default': [
                {
                    'name': 'localhost',
                    'server': 'localhost',
                    'port': 25,
                    'ssl': False,
                    'mail_from': 'bot@{{server}}'
                }
            ],
            'items': {
                'type': 'object',
                'properties': {
                    'name': {
                        'type': 'string',
                        'title': 'Mail server name',
                        'description': 'Name of mail server configuration',
                        'default': 'localhost'
                    },
                    'server': {
                        'type': 'string',
                        'title': 'Mail server',
                        'description': 'Mail server to send emails from',
                        'default': 'localhost',
                    },
                    'port': {
                        'type': 'integer',
                        'title': 'Mail server port',
                        'description': 'Mail server port to connect to',
                        'default': 465,
                    },
                    'ssl': {
                        'type': 'boolean',
                        'title': 'Use SSL',
                        'description': 'Use SSL to secure the mail server connection',
                        'default': True,
                    },
                    'tls': {
                        'type': 'boolean',
                        'title': 'Use TLS',
                        'description': 'Use TLS to secure the mail server connection',
                        'default': False,
                    },
                    'protocol': {
                        'type': 'string',
                        'title': 'Server protocol',
                        'description': 'Protocol to use with this mail server',
                        'default': 'smtp',
                        'enum': ['smtp'],
                    },
                    'mail_from': {
                        'type': 'string',
                        'title': 'Mail from address',
                        'description': 'From mail address to use for unspecified outgoing mail',
                        # TODO: Get a better default here:
                        'default': 'bot@{{server}}'
                    },
                    'username': {
                        'type': 'string',
                        'title': 'SMTP Username',
                        'default': '',
                    },
                    'password': {
                        'type': 'string',
                        'title': 'SMTP Password',
                        'x-schema-form': {
                            'type': 'password',
                        }
                    },
                    'use_sendmail': {
                        'type': 'boolean',
                        'title': 'Use sendmail',
                        'default': False,
                        'description': 'Use local sendmail (e.g. msmtp) instead of smtp'
                    },
                    'sendmail_extra_arguments': {
                        'type': 'string',
                        'title': 'Sendmail arguments',
                        'description':
                            'Use these extra arguments to control e.g. msmtp',
                        'default': '-t -oi'
                    },
                    'sendmail_binary': {
                        'type': 'string',
                        'title': 'Sendmail binary to use',
                        'description': 'Specify the executable to send mail with',
                        'default': '/usr/bin/sendmail'
                    }
                }
            }
        }
    }

    configform = [
        'mail_send',
        'default_account',
        {
            'key': 'accounts',
            'add': "Add account",
            'style': {
                'add': "btn-success"
            },
            'items': [
                'accounts[].name',
                'accounts[].mail_from',
                'accounts[].use_sendmail',
                fieldset('Sendmail details', [
                    'accounts[].sendmail_extra_arguments',
                    'accounts[].sendmail_binary',
                ], options={
                    'condition': '$ctrl.model.accounts[arrayIndex].use_sendmail == true'
                }),
                fieldset('SMTP account details', [
                    'accounts[].server',
                    'accounts[].port',
                    'accounts[].ssl',
                    'accounts[].tls',
                    'accounts[].protocol',
                    'accounts[].username',
                    'accounts[].password'
                ], options={
                    'condition':
                        '$ctrl.model.accounts[arrayIndex].use_sendmail == false'
                })
            ]
        },
    ]

    def __init__(self, *args, **kwargs):
        super(MailTransmitter, self).__init__('MAILTX', *args, **kwargs)

        self.worker = Worker(process=False, workers=2,
                             channel="mail-transmit-workers").register(self)

        self.hostname = objectmodels['systemconfig'].find_one({'active': True}).hostname

        self.log("Started")

        self.fireEvent(cli_register_event('test_mail', cli_test_mail))

    @handler('cli_test_mail')
    def cli_mail_test(self, event):
        self.log('Sending testmail')
        self.fireEvent(
            send_mail('root@localhost', 'Testmail', 'Hello dear test mail receiver!'))

    def send_mail(self, event):
        """Connect to mail server and send actual email"""

        mime_mail = MIMEText(event.text)
        mime_mail['Subject'] = event.subject

        if event.account == 'default':
            account_name = self.config.default_account
        else:
            account_name = event.account

        account = list(filter(lambda account: account['name'] == account_name,
                              self.config.accounts))[0]

        mime_mail['From'] = render(account['mail_from'], {
            'server': account['server'],
            'hostname': self.hostname
        })
        mime_mail['To'] = event.to_address

        self.log('MimeMail:', mime_mail, lvl=verbose)
        if self.config.mail_send is True:
            self.log('Sending mail to', event.to_address)

            if account['use_sendmail']:
                # TODO: TEST THIS!!!
                self.log('Would now task sendmail to send the mail')
                result, log = run_process(
                    '', [
                            account['sendmail_binary']
                        ] + account['sendmail_extra_arguments'].split(' '),
                    stdin=mime_mail.as_string()
                )
            else:
                self.fireEvent(task(send_mail_worker, account, mime_mail, event),
                               "mail-transmit-workers")
        else:
            self.log('Not sending mail, here it is for debugging info:', mime_mail,
                     pretty=True)

    @handler('task_success', channel="mail-transmit-workers")
    def task_success(self, event, call, result):
        success, log, originating_event = result

        if success is True:
            self.log('Sent mail successfully.')
        else:
            self.log('Sending mail failed:', event, call, log, lvl=error)
