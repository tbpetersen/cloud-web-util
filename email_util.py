from email.mime.text import MIMEText
import smtplib

import credentials

UCSD_SMTP_SERVER = 'smtp.ucsd.edu'

def sendMail(sender, receiver, subject, msg):
	if type(receiver) is list:
		for name in receiver:
			sendMail(sender, name, subject, msg)
		return

	msg = MIMEText(msg)
	msg['To'] = receiver
	msg['From']    = sender
	msg['Subject'] = subject

	if receiver is not list:
		receiver = [receiver]

	server = smtplib.SMTP(UCSD_SMTP_SERVER) 
	server.ehlo()
	server.starttls()
	server.ehlo()
	server.login(credentials.email_server_username, credentials.email_server_password)
	server.sendmail(sender, receiver, msg.as_string())
	server.close()