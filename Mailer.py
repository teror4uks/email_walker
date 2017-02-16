import smtplib
import imaplib
import email
import datetime
from time import sleep
from email.mime.text import MIMEText


class Mailer():
    def __init__(self, account, passwd, toaddr):
        print('inicialise')
        self.account = account
        self.passwd = passwd
        self.toaddr = toaddr
        self.smtp = smtplib.SMTP('smtp.gmail.com:587')
        self.imap = imaplib.IMAP4_SSL('imap.gmail.com')
        self.uids = self.check_mail_box()

    def __new__(cls, account, passwd, toaddr):

        if account == '' or passwd == '' or toaddr == '':
            raise ValueError("One or more parametrs empty")

        if not '@' in account:
            raise ValueError("in account not symbol @!")

        print('create object')
        return super(Mailer, cls).__new__(cls)

    def connect_smtp(self):
        self.smtp = smtplib.SMTP('smtp.gmail.com:587')
        self.smtp.starttls()
        self.smtp.ehlo('ehlo')
        try:
            self.smtp.login(self.account, self.passwd)
        except smtplib.SMTPAuthenticationError as e:
            print("Auth error: ", e)
            return False
        except smtplib.SMTPServerDisconnected as e:
            print("Disconect serv: ", e)
            return False
        except Exception as e:
            print("Unexpected error: ", e)
            return False
        self.smtp.helo('helo')
        return True

    def check_mail_box(self):
        connected = self.connect_smtp()
        if connected:
            try:
                self.imap.login(self.account, self.passwd)
            except Exception as e:
                print(e)
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
            print("Unexpected error: ", e)
            raise

        self.smtp.send_message(msg=msg, from_addr=self.account, to_addrs=self.toaddr)

    def run(self):
        if len(self.uids) == 0:
            return "Not unseen emails"
        for f in self.uids:
            data = self.get_email_data(f)
            header = self.get_email_header_details(data)
            self.get_body_and_send(data,header)


    def close_smtp(self):
        self.smtp.close()

if __name__ == '__main__':
    m = Mailer("", "", "")
    #m.connect_smtp()