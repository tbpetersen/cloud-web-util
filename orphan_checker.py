from keystoneclient.v3 import client
from keystoneauth1.exceptions.http import Conflict as Name_Conflict
import credentials
import sys
import traceback

from email_util import sendMail
from db_communicator import query

ACCOUNT_EXCEPTIONS = ['heat_domain_admin']
keyStone = client.Client(username = credentials.open_stack_username, 
	password=credentials.open_stack_pw, 
	auth_url = credentials.open_stack_url)

WATCHERS = ['c1mckay@sdsc.edu', 'ranakashima@sdsc.edu']

def collectOrphans():
	user_ids = []
	orphan_names = []
	orphan_ids = []
	for project in keyStone.projects.list():
		role_assignments = keyStone.role_assignments.list(project=project.id)
		for role_assignment in role_assignments:
			try:
				user_id = role_assignment.user["id"]
				if user_id not in user_ids:
					user_ids.append(user_id)
			except AttributeError:
				continue
	for user in keyStone.users.list():
		if user.id not in user_ids and user.name not in ACCOUNT_EXCEPTIONS:
			orphan_names.append(user.name)
			orphan_ids.append(user.id)
	
	if len(orphan_names) == 0:
		return [], []

	return orphan_names, orphan_ids

def saveOrphans(orphan_names, orphan_ids):
	qString = ''
	qData = []
	for name, uid in zip(orphan_names, orphan_ids):
		qString += "insert into orphan_accounts (account_name, account_id) VALUES (%s, %s);"
		qData.append(str(name))
		qData.append(str(uid))
		sendMail('support@sdsc.edu', [name] + WATCHERS, 'SDSC Cloud User Account Inactivity', 'Dear SDSC Cloud User,\n\nYour user account, {0}, does not belong to any active projects.  The user account will automatically be deleted if it is not associated with an active project within 14 days.\n\nPlease contact us by replying to this email if you need your user account to remain active.\n\nRegards,\nSDSC Cloud Support Team'.format(name))
	query(qString, tuple(qData), False)
	
def notifyOrphans():
	orphan_names, orphan_ids = collectOrphans()


	previous_orphans = query('select account_name, account_id from orphan_accounts', (), True)

	still_orphan = []
	for prev_orphan in previous_orphans:
		name = prev_orphan[0]
		if name in orphan_names:
			still_orphan.append(prev_orphan)

	for name, uid in still_orphan: 
		keyStone.users.delete(user=uid)
		sendMail('support@sdsc.edu', [name] + WATCHERS, 'SDSC Cloud User Account Deleted', 'Dear SDSC Cloud User,\n\nYour user account, {0}, has been deleted because it does not belong to any active projects.\n\nPlease contact us by replying to this email if you need your account re-created.\n\nRegards,\nSDSC Cloud Support Team'.format(name))
		
	query('delete from orphan_accounts;', (), False)

if __name__ == "__main__":
	if sys.argv[1] == 'collect':
		try:
			orphan_names, orphan_ids = collectOrphans()
			if len(orphan_names) == 0:
				sendMail('cloud-no-reply@sdsc.edu', WATCHERS, 'SDSC Cloud Orphan Accounts', 'There were no orphaned cloud accounts found in keyStone.')
			else:
				saveOrphans(orphan_names, orphan_ids)
		except:
			sendMail('cloud-support-no-reply@sdsc.edu', 'c1mckay@sdsc.edu', 'Orphan collection failed', str(traceback.format_exc()))
	elif sys.argv[1] == 'delete':
		try:
			notifyOrphans()
		except:
			sendMail('cloud-support-no-reply@sdsc.edu', 'c1mckay@sdsc.edu', 'Orphan destruction failed', str(traceback.format_exc()))
	

	