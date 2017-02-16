import smtplib
import imaplib


class Mailer():
    def __init__(self, account, passwd, toaddr):
        self.account = account
        self.passwd = passwd
        self.toaddr = toaddr
        self.smtp = smtplib.SMTP('smtp.gmail.com:587')
        self.imap = imaplib.IMAP4_SSL('imap.gmail.com')

    def connect_smtp(self):
        self.smtp.starttls()
        self.smtp.ehlo('ehlo')
        self.smtp.login(self.account, self.passwd)
        self.smtp.helo('helo')

    def connect_imap(self):
        self.imap.login(self.account, self.passwd)
        self.imap.list()
        self.imap.select('inbox')
        result, data = self.imap.uid('search', None, "UNSEEN")  # (ALL/UNSEEN)
        return data[0]


