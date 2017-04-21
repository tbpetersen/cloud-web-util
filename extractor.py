import re
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

import db_communicator, pyfootprints.footprintsEditor as tEditor
import credentials
import holonetComm
from email_util import sendMail
from keystoneclient.v3 import client
from openstack_utility import keyStoneUtility

now = datetime.date.today()
ticketsGeneratedThisMonth = now.day >= 21
PRINT_ERRORS = True

dateConverter = {}
dateConverter['jan'] = 1
dateConverter['feb'] = 2
dateConverter['mar'] = 3
dateConverter['apr'] = 4
dateConverter['may'] = 5
dateConverter['jun'] = 6
dateConverter['jul'] = 7
dateConverter['aug'] = 8
dateConverter['sep'] = 9
dateConverter['oct'] = 10
dateConverter['nov'] = 11
dateConverter['dec'] = 12

# good example ticket: 72184

BAD_TICKET_LISTENERS = ['c1mckay@sdsc.edu', 'ranakashima@sdsc.edu']#, 's1yeu@sdsc.edu', 'ranakashima@sdsc.edu']

TRIAL_INDEX = None
REPLY_EMAIL = 'support@sdsc.edu'
projectName = 'projectName'
projectMonth = 'projectMonth'
projectID = 'projectID'


sdscStone = keyStoneUtility.KeyStoneUtility(username = credentials.open_stack_username, password=credentials.open_stack_pw, auth_url = credentials.open_stack_url, 
	auth_url_dep = credentials.open_stack_url_dep, tenant_name=credentials.open_stack_username)

projects = sdscStone.keyStone.projects.list()

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
			global ticketsGeneratedThisMonth
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
		self.project = sdscStone.getProject(self.projectName)

		if self.project == None:# and PRINT_ERRORS:
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
		emailData = getDatesSent(self.projectName.lower())
		return [(t-datetime.date(1970,1,1)).total_seconds() for t in emailData]

def queryHolonet(qString):
	return holonetComm.queryHolonet(qString, longWay = True, onErr = BillingQueryError)

def getOutstandingTickets():
	qString = "SELECT MRID, MRTITLE, ITEM__B1__BSELLER, ITEM__B1__BCATEGORY, START__BDATE FROM FOOTPRINTS.MASTER3"
	qString += " where BILLABLE = 'Yes' and BILLED__BSTATUS = 'Rejected' and APPROVED__BBY__BMANAGER = 'on' and MRSTATUS != '_DELETED_'"
	qString += " and ITEM__B1__BSELLER = 'SRF__bCloud'"
	qString += " and (ITEM__B1__BCATEGORY = 'On__bDemand__bTriple__bCopy' OR ITEM__B1__BCATEGORY = 'Condo__bDual__bCopy' OR ITEM__B1__BCATEGORY = 'Cloud__bCompute')"

	data = queryHolonet(qString)
	tickets = json.loads(data)

	currentMonth = datetime.date.today().month;

	acceptableCategories = ['On__bDemand__bTriple__bCopy', 'Condo__bDual__bCopy', 'Cloud__bCompute']

	for ticket in tickets:
		for key in ticket.keys():
			ticket[key] = str(ticket[key])
		ticket['ticket_id'] = int(ticket['MRID'.lower()]) #ticket id

	badProjects = {}


	from datetime import datetime as d1

	for x in tickets:
		descrip = x['MRTITLE'.lower()] # DESCRIPTION

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
		if "&#58;" in descrip:
			parts =   descrip.split("&#58;")
			projectName =  parts[0]
			month = parts[1]
			month = dateConverter[month.lower()]
			oldTicket = False
		else:
			projecName = descrip.replace(" Cloud - [", "").replace("]", "")
			date = x['START__BDATE'.lower()]
			date = d1.strptime(date, '%Y-%m-%d %H:%M:%S')
			month = date.month
			oldTicket = True

		
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
	role_assignments = sdscStone.keyStone.role_assignments.list(project=project.id)
	emails = []
	for role_assignment in role_assignments:
		try:
			user_id = role_assignment.user["id"]
			email = str(sdscStone.keyStone.users.get(user_id).name)
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

def monthAfter(date):
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

def saveEmailTimeToDb(project_name):
	db_communicator.query('insert into email_records (project_name, date_sent) values (%s, CURRENT_TIMESTAMP);', [project_name], False)

def getDatesSent(project_name):
	results = db_communicator.query('select date_sent from email_records where project_name = %s', [project_name.lower()], True)
	return [r[0] for r in results]


def postMail(project_name):

	project_name = project_name.lower()

	global PRINT_ERRORS
	PRINT_ERRORS = False
	badProjects = getOutstandingTickets() 

	# load previous emails

	sent_emails = getDatesSent(project_name)
	if len(sent_emails) != 0:
		earliestEmail = max(sent_emails)
		if not monthAfter(earliestEmail):
			raise EmailSpamError

	badProjects = getOutstandingTickets()
	if project_name not in badProjects:
		raise NoProjectError()

	badProjects[project_name].report()

	saveEmailTimeToDb(project_name)



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


	try:
		global sdscStone
		sdscStone.createProject(project_name = project_name, contact_name = contact_name, contact_email = contact_email, billing_field = index, attachNetwork = ATTACH_NETWORK)
	except Name_Conflict:
		raise ProjectNameTaken()

	if index == TRIAL_INDEX:
		saveTrialProject(project_name, warningTime, expirationTime)
	else:
		if ' ' in contact_name:
			indexOfSpace = contact_name.index(' ')
			first_name = contact_name[:indexOfSpace]
			last_name = contact_name[indexOfSpace + 1:]
		else:
			first_name = contact_name
			last_name = contact_name
		title = None #auto set in create ticket
		assignees = None #auto set in create ticket
		ticketNumber = tEditor.createTicket(project_name, index, first_name, last_name, contact_email, title, assignees)
		#probably uneeded refresh now
		sdscStone = keyStoneUtility.KeyStoneUtility(username = credentials.open_stack_username, password=credentials.open_stack_pw, auth_url = credentials.open_stack_url, 
		auth_url_dep = credentials.open_stack_url_dep, tenant_name=credentials.open_stack_username)
		sdscStone.setBillingInfo(project_name, str(ticketNumber))

	usersAndPasswords = [{'username': u, 'password': '' if sdscStone.userExists(u) else getAndSendPassword(u)} for u in users]

	sdscStone.attachUsers(project_name, usersAndPasswords)

	sendMail("cloud-no-reply@sdsc.edu", ["c1mckay@sdsc.edu", "ranakashima@sdsc.edu"], 
		"New Project Created ["+project_name+"]", project_name + " created for:\n" + "\n".join(users))

if __name__ == "__main__":
	main()

	