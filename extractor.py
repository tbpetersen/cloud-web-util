import time
import sys
import string
import json
import datetime
from email.mime.text import MIMEText
from keystoneauth1.exceptions.http import Conflict as Name_Conflict
import os, errno
import requests
import paramiko

import db_communicator
import credentials
from email_util import sendMail
from keystoneclient.v3 import client
from openstack_utility import keyStoneUtility


ticketsGeneratedThisMonth = False
PRINT_ERRORS = True

dateConverter = {}
dateConverter['Jan'] = 1
dateConverter['Feb'] = 2
dateConverter['Mar'] = 3
dateConverter['Apr'] = 4
dateConverter['May'] = 5
dateConverter['Jun'] = 6
dateConverter['Jul'] = 7
dateConverter['Aug'] = 8
dateConverter['Sep'] = 9
dateConverter['Oct'] = 10
dateConverter['Nov'] = 11
dateConverter['Dec'] = 12

# good example ticket: 72184

BAD_TICKET_LISTENERS = ['c1mckay@sdsc.edu', 'ranakashima@sdsc.edu']#, 's1yeu@sdsc.edu', 'ranakashima@sdsc.edu']

TRIAL_INDEX = None
REPLY_EMAIL = 'support@sdsc.edu'
projectName = 'projectName'
projectMonth = 'projectMonth'
projectID = 'projectID'


keyStone = client.Client(username = credentials.open_stack_username, 
	password=credentials.open_stack_pw, 
	auth_url = credentials.open_stack_url)
projects = keyStone.projects.list()

words = ['First', 'Second', 'Third', 'Last']
TICKET_TYPES = ["Cloud Compute Usage Charges", "Cloud Storage Usage Charges", "Cloud Compute Image Charges", "Cloud Compute Volume Snapshot Charges", "Cloud Compute Volume Charges"]

local = True

def myprint(x):
	if local:
		print x

class Ticket:
	def __init__(self, month, ticketNumber, ticketType, project):
		self.month = month
		self.ticketNumber = ticketNumber
		self.ticketType = ticketType
		self.project = project

	def __str__(self):
		return str(self.ticketType) + " - [" + str(self.month) + "]"


	def __repr__(self):
		return str(self)

class BadProject:
	def __init__(self, projectName):
		self.projectName = projectName
		self.systems = []
		self.tickets = {}
		self.status = {}
		self.emails = None

		for ticketType in TICKET_TYPES:
			self.tickets[ticketType] = []
			self.status[ticketType] = -1

	def __str__(self):
		return self.projectName

	def __repr__(self):
		return str(self)

	def hasGoodTickets(self):
		for ticketType in TICKET_TYPES:
			if self.status[ticketType] != 0:
				return True
		return False

	def getFailingTypes(self):
		return [ticketType for ticketType in TICKET_TYPES if self.status[ticketType] != 0]

	def add(self, month, ticketNumber, ticketType):
		currentMonth = datetime.date.today().month 
		month = (currentMonth - month) % 12

		self.tickets[ticketType].append(Ticket(month, ticketNumber, ticketType, self))

	def resolveStatus(self):
		for ticketType in TICKET_TYPES:
			curMonths = [t.month for t in self.tickets[ticketType]]
			
			# i can see 0s this month
			# 0s indicate first warning
			if ticketsGeneratedThisMonth: 
				start = 0
				end = 4

			# 1s indicate first warning
			else:
				start = 1
				end = 5

			status = 0
			for m in range(start, end):
				if m in curMonths:
					status += 1
				else:
					break
			self.status[ticketType] = status

	def associateKeystoneProject(self):
		self.project = None
		for p in projects:
			if p.name == self.projectName:
				self.project = p
				break
		if self.project == None and PRINT_ERRORS:
			print '\tUnable to find a project for ' + self.projectName

	def setEmails(self):
		if self.project == None:
			self.associateKeystoneProject()
			if self.project == None:
				return

		self.emails = getEmails(self.project)
		

	def getEmails(self):
		if self.project == None:
			self.associateKeystoneProject()
			if self.project == None:
				return
		if self.emails == None:
			self.setEmails()
		return self.emails

	def report(self):
		myprint ('Reporting for project ' + self.projectName)
		myprint('--------------------------------------------')
		
		if self.project == None:
			self.associateKeystoneProject()
		if self.project == None:
			return
		
		fName = self.project.contact_name
		warningNumber = max([self.status[tType] for tType in TICKET_TYPES])
		
		myprint (warningNumber)
		warningText = words[warningNumber - 1].lower()
		self.setEmails()
		for email in self.emails:
			fName = getFirstName(email)
			if fName == None or len(fName) == 0:
				fName = self.project.contact_name
			sendTicketNotification(fName, self.projectName, warningText, email, self.systems)

		myprint('\n')

	def getEmailDates(self):
		emailData = []
		if self.projectName.lower() not in emailData:
			return []
		return emailData[self.projectName.lower()]

def queryHolonet(qString):
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect('holonet.sdsc.edu', username='c1mckay', key_filename='.ssh/id_rsa.openssh')

	script = "query.php \"" + qString + "\""

	stdin, stdout, stderr = ssh.exec_command('php ' + script)
	if len("".join(stderr.readlines())) != 0:
		ssh.close()
		raise BillingQueryError()
	ssh.close()
	return "".join(stdout.readlines())

def getOutstandingTickets():
	qString = "SELECT MRID, MRTITLE, ITEM__B1__BSELLER, ITEM__B1__BCATEGORY FROM FOOTPRINTS.MASTER3 where BILLABLE = 'Yes' and BILLED__BSTATUS = 'Rejected' and APPROVED__BBY__BMANAGER = 'on' and MRSTATUS != '_DELETED_'"
	data = queryHolonet(qString)
	data = json.loads(data)

	currentMonth = datetime.date.today().month;

	acceptableCategories = ['On__bDemand__bTriple__bCopy', 'Condo__bDual__bCopy', 'Cloud__bCompute']

	tickets = [x for x in data if x['ITEM__B1__BSELLER'] == 'SRF__bCloud']
	tickets = [x for x in data if x['ITEM__B1__BCATEGORY'] in acceptableCategories]

	for ticket in tickets:
		for key in ticket.keys():
			ticket[key] = str(ticket[key])
		ticket['ticket_id'] = int(ticket['MRID']) #ticket id

	badProjects = {}

	for x in tickets:
		descrip = x['MRTITLE'] # DESCRIPTION

		if "[Cloud Compute] Usage Charges (" in descrip:
			title = "Cloud Compute Usage Charges"
			descrip = descrip.replace("[Cloud Compute] Usage Charges (", "")
		elif "[Cloud Storage] Usage Charges (" in descrip:
			title = "Cloud Storage Usage Charges"
			descrip = descrip.replace("[Cloud Storage] Usage Charges (", "")
		elif "[Cloud Compute] Image Charges (" in descrip:
			title = "Cloud Compute Image Charges"
			descrip = descrip.replace("[Cloud Compute] Image Charges (", "")
		elif "[Cloud Compute] Volume Snapshot Charges (" in descrip:
			title = "Cloud Compute Volume Snapshot Charges"
			descrip = descrip.replace("[Cloud Compute] Volume Snapshot Charges (", "")
		elif "[Cloud Compute] Volume Charges (" in descrip:
			title = "Cloud Compute Volume Charges"
			descrip = descrip.replace("[Cloud Compute] Volume Charges (", "")
		else:
			myprint("~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
			myprint(descrip)
			myprint("~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

		descrip = descrip.replace(")", "")

		descrip = descrip.replace(")", "")
		parts =   descrip.split("&#58;")
		projectName =  parts[0]
		month = parts[1]
		month = dateConverter[month]
		
		if projectName.lower() in badProjects:
			project = badProjects[projectName.lower()]
		else:
			project = BadProject(projectName)
			badProjects[projectName.lower()] = project

		project.add(month, x['ticket_id'], title)
		if title not in project.systems:
			project.systems.append(title)

	for project in badProjects.values():
		project.associateKeystoneProject()
		project.resolveStatus()

	return badProjects

def formatTicketWarning(clientName, warningNumber, systems):
	clientName = clientName.replace("\"", "")

	fp = open('template.txt', 'rb')
	msg = fp.read()
	fp.close()
	msg = msg.replace('[Insert Customer Name Here]', clientName)
	msg = msg.replace('[Warning]', warningNumber)

	systems = ['\t - ' + s + '\n' for s in systems]
	systemText = string.join(systems, '')
	msg = msg.replace('[Systems]', systemText)
	
	return msg

def sendTicketNotification(clientName, projectName, warningNumber, receiverEmail, systems):
	myprint('Sending mail to ' + clientName + " with email: " + receiverEmail)
	msg = formatTicketWarning(clientName, warningNumber, systems)
	subject = ('SDSC Cloud Account [' + projectName + '] - [' + warningNumber.title() +']')
	receiverEmail = []
	receiverEmail += BAD_TICKET_LISTENERS
	# receiverEmail.append(receiverEmail)
	sendMail(REPLY_EMAIL, receiverEmail, subject, msg)

def getAndSendPassword(email):
	key      = credentials.onetimesecret_api_key
	username = credentials.onetimesecret_username

	url = 'https://onetimesecret.com/api/v1/generate'
	response = requests.post(url, auth=(username, key), data="recipient=" + email)
	response = json.loads(str(response.text))

	return str(response['value'])

def getEmails(project):
	role_assignments = keyStone.role_assignments.list(project=project.id)
	emails = []
	for role_assignment in role_assignments:
		try:
			user_id = role_assignment.user["id"]
			email = str(keyStone.users.get(user_id).name)
			if email not in emails and '@' in email:
				emails.append(email)
		except AttributeError:
			continue

	if emails == None or len(emails) == 0:
		emails = [project.contact_email]
	return emails

def silentRemove(filename):
    try:
        os.remove(filename)
    except OSError as e: # this would be "except OSError, e:" before Python 2.6
        if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
            raise # re-raise exception if a different error occured

# helper function to query footprints to get a possible 'first name' for email use
def getFirstName(email):
	qString = "SELECT FIRST__BNAME FROM FOOTPRINTS.MASTER18_ABDATA where UPPER(EMAIL__BADDRESS) = UPPER('" + email  + "')"
	result = queryHolonet(qString)
	result = json.loads(result)

	if len(result) == 0:
		return None

	return str(result[0]['FIRST__BNAME'])

def main():
	global local
	local = False
	argCount = len(sys.argv)
	if argCount < 2 or argCount > 3:
		printUsage()
		return

	gPdata = sys.argv[1]
	if argCount == 2:
		if gPdata != 'GET':
			printUsage()
			return
		getData()
		return

	if gPdata == "ACCOUNT":
		unpackProjectData(sys.argv[2])
		return

	if gPdata != "POST":
		printUsage()
		return

	postMail(sys.argv[2])

def monthAfter(seconds):
	date = datetime.datetime.fromtimestamp(seconds).date()
	nextAllowableDate = date + datetime.timedelta(days = 30)
	return nextAllowableDate < datetime.datetime.now().date()

class BillingQueryError(Exception):
	def __init__(self,*args,**kwargs):
		Exception.__init__(self,*args,**kwargs)

class EmailSpamError(Exception):
	def __init__(self,*args,**kwargs):
		Exception.__init__(self,*args,**kwargs)

class ProjectNameTaken(Exception):
	def __init__(self,*args,**kwargs):
		Exception.__init__(self,*args,**kwargs)

class NoProjectError(Exception):
	def __init__(self,*args,**kwargs):
		Exception.__init__(self,*args,**kwargs)


def postMail(project_name):

	project_name = project_name.lower()

	global PRINT_ERRORS
	PRINT_ERRORS = False
	badProjects = getOutstandingTickets() 

	# load previous emails
	with open('past_emails.json') as data_file:    
	    emailData = json.load(data_file)

	if project_name in emailData and len(emailData[project_name]) != 0:
		earliestEmail = max(emailData[project_name])
		if not monthAfter(earliestEmail):
			raise EmailSpamError()

	if project_name not in emailData:
		emailData[project_name] = []

	badProjects = getOutstandingTickets()
	if project_name not in badProjects:
		raise NoProjectError()

	badProjects[project_name].report()

	emailData[project_name].append(time.time())

	f = open('past_emails.json', 'w')
	f.write(json.dumps(emailData, separators=(',',':')))
	f.close()



def printUsage():
	print 'Usage:'
	print sys.argv[0] + " GET"
	print sys.argv[0] + " POST <project_name>"

def getData():
	global PRINT_ERRORS
	PRINT_ERRORS = False
	badProjects = getOutstandingTickets() 

	requestedData = {}
	behavingProjects = []
	requestedData['validProjects'] = behavingProjects
	weirdTickets = []
	requestedData['weirdTickets'] = weirdTickets
	seenTickets = []
	for project in badProjects.values():
		if not project.hasGoodTickets():
			continue
		behavingProject = {}
		behavingProject['projectName'] = project.projectName
		behavingProject['contactEmail'] = project.getEmails()
		behavingProject['emailDates'] = project.getEmailDates()
		tTypes = project.getFailingTypes()
		behavingProject['failingType'] = tTypes
		warningNumber = max([project.status[tType] for tType in tTypes])
		behavingProject['warningLevel'] = words[warningNumber - 1] + " Warning"
		tickets = []
		for tType in tTypes:
			for ticket in project.tickets[tType]:
				if ticket.month <= 4:
					tickets.append(ticket.ticketNumber)
					seenTickets.append(ticket)
		behavingProject['ticketNumbers'] = tickets
		behavingProjects.append(behavingProject)

	for project in badProjects.values():
		tTypes = project.getFailingTypes()
		for tType in tTypes:
			for ticket in project.tickets[tType]:
				if ticket not in seenTickets:
					weirdTicket = {}
					weirdTicket['ticketNumber'] = ticket.ticketNumber
					weirdTicket['projectName'] = ticket.project.projectName
					weirdTicket['month'] = ticket.month
					weirdTicket['failingType'] = ticket.ticketType
					weirdTickets.append(weirdTicket)
	

	# sends the data out so the nodescript can pick it up and send it out
	print json.dumps(requestedData, separators=(',',':'))

def saveTrialProject(project_name, warning, expiration):
	db_communicator.query('insert into trial_projects (name, created, notified, warning_length, delete_length) values (%s, CURRENT_TIMESTAMP, %s, %s, %s);', [project_name, False, warning, expiration], False)

ATTACH_NETWORK = True

def unpackProjectData(data):
	data = json.loads(data)
	project_name = data['projectName']
	contact_name = data['contactName']
	contact_email = data['contactEmail']
	users = data['users']
	if data['isTrial']:
		index = TRIAL_INDEX
		warningTime = data['warningTime']
		expirationTime = data['expirationTime']
	else:
		index = data['index']
		warningTime = None
		expirationTime = None

	pBuilder = keyStoneUtility.KeyStoneUtility(username = credentials.open_stack_username, password=credentials.open_stack_pw, auth_url = credentials.open_stack_url, 
		auth_url_dep = credentials.open_stack_url_dep, tenant_name=credentials.open_stack_username)

	try:
		pBuilder.createProject(project_name = project_name, contact_name = contact_name, contact_email = contact_email, billing_field = index, attachNetwork = ATTACH_NETWORK)
	except Name_Conflict:
		raise ProjectNameTaken()

	if index == TRIAL_INDEX:
		saveTrialProject(project_name, warningTime, expirationTime)

	usersAndPasswords = [{'username': u, 'password': '' if pBuilder.userExists(u) else getAndSendPassword(u)} for u in users]

	pBuilder.attachUsers(project_name, usersAndPasswords)

	sendMail("cloud-no-reply@sdsc.edu", ["c1mckay@sdsc.edu", "ranakashima@sdsc.edu"], 
		"New Project Created ["+project_name+"]", project_name + " created for:\n" + "\n".join(users))

if __name__ == "__main__":
	main()

	