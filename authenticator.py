import smtplib
import sys

UCSD_SMTP_SERVER = 'smtp.ucsd.edu'
ALLOWED_USERNAMES = ['ranakashima@sdsc.edu', 'kcoakley@sdsc.edu', 'colby@sdsc.edu', 'c1mckay@sdsc.edu']

def authenticate(username, password):
	server = smtplib.SMTP(UCSD_SMTP_SERVER) 
	server.ehlo()
	server.starttls()
	server.ehlo()
	server.login(username, password)
	server.close()

if __name__ == "__main__":
	authenticate(sys.argv[1], sys.argv[2])