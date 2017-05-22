from email_util import sendMail
import db_communicator
import datetime
from keystoneclient.v3 import client
from keystoneauth1.exceptions.http import Conflict as Name_Conflict

from db_communicator import query
import credentials

ID = 0
NAME = 1
DATE = 2
NOTIFICATION_STATUS = 3
WARNING_TIME = 4
DELETE_TIME = 5

FIRST = True
SECOND = False

WATCHERS = ['c1mckay@sdsc.edu', 'ranakashima@sdsc.edu']

def timeToWarn(result, current_date):
	date_submitted = result[DATE]
	notified_already = result[NOTIFICATION_STATUS]
	warning_length = result[WARNING_TIME]
	if notified_already:
		return False
	sixty_days_after = date_submitted + datetime.timedelta(days = warning_length)
	return current_date >= sixty_days_after
	

def timeToDelete(result, current_date):
	date_submitted = result[DATE]
	delete_length = result[DELETE_TIME]
	ninety_days_after = date_submitted + datetime.timedelta(days = delete_length)
	return current_date > ninety_days_after
	

def markNotified(uid):
	db_communicator.query('update trial_projects set notified = true where project_id = %s', tuple([int(uid)]), False)

def deleteTrialDbEntry(uid):
	query('delete from trial_projects where project_id = %s;', tuple([int(uid)]), False)

def notifyUser(project_name, email, warningNumber, remainingTime):
	if warningNumber == FIRST:
		subj = 'The trial project for "{0}" is expiring soon'
		msg = 'Dear {0} project user,\n\n This message is a warning that your trial project "{0}" will expire within {1} days.  After {1} days, it will be deleted.\n\n'
		msg += 'SDSC Cloud Support'
	else:
		subj = 'The trial project for "{0}" has expired'
		msg = 'Dear {0} project user,\n\n This message is a notification that your trial project "{0}" has expired and the project was deleted.  Please contact SDSC Support with any concerns.\n\n'
		msg += 'SDSC Cloud Support'
	subj = subj.format(project_name)
	msg = msg.format(project_name, remainingTime)
	sendMail('support@sdsc.edu', email, subj, msg)

def notifyProject(project, warning_number, remainingTime):
	keyStone = client.Client(username = credentials.open_stack_username, 
	password=credentials.open_stack_pw, 
	auth_url = credentials.open_stack_url)

	project_instance = getProject(project)
	role_assignments = keyStone.role_assignments.list(project_instance.id)
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
		emails = [project_instance.contact_email]
	
	emails += WATCHERS
	for email in emails:
		notifyUser(project, email, warning_number, remainingTime)

def getProject(project_name):
	keyStone = client.Client(username = credentials.open_stack_username, 
	password=credentials.open_stack_pw, 
	auth_url = credentials.open_stack_url)
	for project in keyStone.projects.list():
		if project.name == project_name:
			return project

	return None

def disableTrialProject(project_name):
	keyStone = client.Client(username = credentials.open_stack_username, 
	password=credentials.open_stack_pw, 
	auth_url = credentials.open_stack_url)
	project_instance = getProject(project_name)
	keyStone.projects.update(project_instance.id, enabled=False)


if __name__ == "__main__":
	results = db_communicator.query('select project_id, name, created, notified, warning_length, delete_length from trial_projects', (), True)

	current_date = datetime.datetime.now().date()
	for result in results:
		remainingTime = result[DELETE_TIME] - result[WARNING_TIME]
		if timeToWarn(result, current_date):
			markNotified(result[ID])
			notifyProject(result[NAME], FIRST, remainingTime)

		elif timeToDelete(result, current_date):
			notifyProject(result[NAME], SECOND, remainingTime)
			deleteTrialDbEntry(result[ID])
			disableTrialProject(project)

		
