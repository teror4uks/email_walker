import datetime
import email
import imaplib
import smtplib

from email.mime.text import MIMEText

EMAIL_ACCOUNT = ""
PASSWORD = ""
TOADDR = ''

mail_smtp = smtplib.SMTP('smtp.gmail.com:587')

mail_smtp.starttls()
mail_smtp.ehlo()

mail_smtp.login(EMAIL_ACCOUNT,PASSWORD)

mail_imap = imaplib.IMAP4_SSL('imap.gmail.com')
mail_imap.login(EMAIL_ACCOUNT, PASSWORD)
mail_imap.list()
mail_imap.select('inbox')
result, data = mail_imap.uid('search', None, "UNSEEN") # (ALL/UNSEEN)

for email_uid in data[0].split():

    result, email_data = mail_imap.uid('fetch', email_uid, '(RFC822)')

    raw_email = email_data[0][1]
    raw_email_string = raw_email.decode('utf-8')

    email_message = email.message_from_string(raw_email_string)

    # Header Details
    date_tuple = email.utils.parsedate_tz(email_message['Date'])
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

    # Body details
    for part in email_message.walk():

        if part.get_content_type() == "text/plain":
            body = part.get_payload(decode=True)

            message = "From: {0}\nSender: {1}\nTo: {2}\nDate: {3}\nSubject: {4}\nBody: \n{5}\n".format(email_from,
                                                                                                       sender,
                                                                                                       email_to,
                                                                                                       local_message_date,
                                                                                                       subject,
                                                                                                       body.decode('utf-8', errors='ignore'))
            msg = MIMEText(message)

            msg['Subject'] = "New redirect email  {0}".format(subject)
            msg['From'] = EMAIL_ACCOUNT
            msg['To'] = TOADDR
            helo = mail_smtp.helo()
            mail_smtp.send_message(msg=msg,from_addr=EMAIL_ACCOUNT,to_addrs=TOADDR)
            mail_smtp.quit()
            exit()
        else:
            continue
