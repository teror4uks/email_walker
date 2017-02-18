import smtplib
import imaplib
import email
import datetime
import logging
import os
from time import sleep
from email.mime.text import MIMEText
import xml.etree.ElementTree as ET

path_to_mail_log = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(filename=path_to_mail_log+os.sep+'mailer.log', format='%(asctime)s - %(levelname)s:%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


class MailerSettings():
    def __init__(self, config):
        self.tree = ET.parse(config)
        self.root = self.tree.getroot()
        self.acc = self.root.find('account').text
        self.passwd = self.root.find('password').text
        self.to = self.root.find('to').text


class Mailer(MailerSettings):
    def __init__(self, config):
        MailerSettings.__init__(self, config)
        logger.info('initialise object')
        self.account = self.acc
        self.passwd = self.passwd
        self.toaddr = self.to
        if self.account == None or self.passwd == None or self.to == None:
            logger.error("One or more parametrs empty")
        if not '@' in self.account:
            logger.error("in account not symbol @")
        if self.account == self.to:
            logger.error("Account and to address equals")
        self.smtp = smtplib.SMTP('smtp.gmail.com:587')
        self.imap = imaplib.IMAP4_SSL('imap.gmail.com')
        self.uids = self.check_mail_box()

    def connect_smtp(self):
        self.smtp = smtplib.SMTP('smtp.gmail.com:587')
        self.smtp.starttls()
        self.smtp.ehlo('ehlo')
        try:
            self.smtp.login(self.account, self.passwd)
        except smtplib.SMTPAuthenticationError as e:
            logger.error("Auth error: " + str(e.args[1]))
            return False
        except smtplib.SMTPServerDisconnected as e:
            logger.error("Disconect serv: " + str(e.args[1]))
            return False
        except Exception as e:
            logger.error("Unexpected error: ", str(e.args[1]))
            return False
        self.smtp.helo('helo')
        return True

    def check_mail_box(self):
        connected = self.connect_smtp()
        if connected:
            try:
                self.imap.login(self.account, self.passwd)
            except Exception as e:
                logger.error(e)
                return False
            self.imap.list()
            self.imap.select('inbox')
            result, uids = self.imap.uid('search', None, "UNSEEN")  # (ALL/UNSEEN)

            return uids[0].split()
        else:
            return False


    def get_email_data(self, uid):
        result, email_data = self.imap.uid('fetch', bytes(uid), '(RFC822)')
        raw_email = email_data[0][1]
        raw_email_string = raw_email.decode('utf-8')
        email_message = email.message_from_string(raw_email_string)

        return email_message

    def get_email_header_details(self, email_message):
        date_tuple = email.utils.parsedate_tz(email_message['Date'])
        local_message_date = ''
        if date_tuple:
            local_date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
            local_message_date = "{0}".format(local_date.strftime("%a, %d %b %Y %H:%M:%S"))
        email_from = str(email.header.make_header(email.header.decode_header(email_message['From'])))
        email_to = str(email.header.make_header(email.header.decode_header(email_message['To'])))
        subject = str(email.header.make_header(email.header.decode_header(email_message['Subject'])))

        try:
            sender = str(email.header.make_header(email.header.decode_header(email_message['Sender'])))
        except:
            sender = email_from

        header = "From: {0}\nSender: {1}\nTo: {2}\nDate: {3}\nSubject: {4}\nBody:  ".format(email_from,
                                                                                                   sender,
                                                                                                   email_to,
                                                                                                   local_message_date,
                                                                                                   subject)
        return header

    def get_body_and_send(self,email_message, header):
        for part in email_message.walk():

            if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True)
                    message = "{0}\n{1}\n".format(header, body.decode('utf-8', errors='ignore'))
                    logger.info("MESSAGE: {0}".format(message))
                    self.post_email(message)

    def post_email(self, message):
        msg = MIMEText(message)

        msg['Subject'] = "New redirect email!"
        msg['From'] = self.account
        msg['To'] = self.toaddr

        try:
            self.smtp.helo('helo')
        except smtplib.SMTPServerDisconnected:
            sleep(30)
            self.connect_smtp()

        except Exception as e:
            logger.error("Unexpected error: " + str(e))
            raise

        self.smtp.send_message(msg=msg, from_addr=self.account, to_addrs=self.toaddr)

    def run(self):
        if len(self.uids) == 0:
            logger.warning("Not unseen emails")
            return "Not unseen emails"
        for f in self.uids:
            data = self.get_email_data(f)
            header = self.get_email_header_details(data)
            self.get_body_and_send(data,header)

    def close_smtp(self):
        self.smtp.close()

if __name__ == '__main__':
    #m = Mailer("", "", "")
    #m.connect_smtp()

    c = Mailer("config.xml")
    c.run()