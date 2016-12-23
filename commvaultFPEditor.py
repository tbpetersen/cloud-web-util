import csv, paramiko, json, subprocess, random

import db_communicator
import credentials
from keystoneclient.v3 import client

from pyfootprints.footprintsEditor import createTicket, editTicket

file_name = 'commvault.csv'
#file_name = 'example.csv'


def queryHolonet(qString):
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect('holonet.sdsc.edu', username='c1mckay', key_filename='../.ssh/id_rsa.openssh')

	script = "query.php \"" + qString + "\""

	stdin, stdout, stderr = ssh.exec_command('php ' + script)
	stderr = "".join(stderr.readlines())
	if len(stderr) != 0:
		print stderr
		ssh.close()

		raise BillingQueryError()
	ssh.close()
	return json.loads("".join(stdout.readlines()))

def getLineItems():

	with open(file_name, 'rb') as f:
		reader = csv.reader(f)
		line_items = list(reader)

	return [line_item for line_item in line_items if line_item[0] != "start_date"]

#https://docs.oracle.com/cd/B19306_01/server.102/b14237/statviews_2094.htm
def getColumnNames():
	qString = "select TABLE_NAME, COLUMN_NAME from ALL_TAB_COLUMNS"
	results = queryHolonet(qString)
	column_names = [r['COLUMN_NAME'] for r in results if r['TABLE_NAME'] == 'MASTER3']
	return column_names

def createTicket(project):
	#projects = [p for p in projects if hasattr(p, 'billing_index') and p.name not in ['c1mckayneutrontest5', 'ranakashima', 'wasprod']]
	if ' ' in project.contact_name:
		indexOfSpace = project.contact_name.index(' ')
		first_name = project.contact_name[:indexOfSpace]
		last_name = project.contact_name[indexOfSpace + 1:]
	else:
		first_name = project.contact_name
		last_name = project.contact_name

	billing_index = project.billing_index
	if ',' in billing_index:
		billing_index = billing_index.split(',')[0].split(':')[0]
		print 'fix ' + str(project.name)

	return createTicket(project_name = project.name, billing_index = billing_index, first_name = first_name, last_name = last_name, email = project.contact_email)

#https://itsm.northwestern.edu/help/FootPrintsHelp/content/perl_sample.htm
#http://docs.oracle.com/javadb/10.6.2.1/ref/rrefsqlj26498.html

def callPerl(file, args):
	subprocess.call(['perl', file, 'x', json.dumps(args)])

def getTicketNumber(name):

	res = db_communicator.query('select ticket_number from commvault_tickets where name = %s', [name], True)
	return res[0][0]

def main():

	
	projectToCharges = {}
	for line_item in getLineItems():
		p_name = line_item[2]
		if p_name not in projectToCharges:
			projectToCharges[p_name] = []
		projectToCharges[p_name].append(line_item)


	
	for project_name, items in projectToCharges.items():
		if project_name in ['fowlerlab', 'iSafeData', 'colby_test']:
			continue

		print project_name #+ str([item[11] for item in items])
		ticket_number = getTicketNumber(project_name)
		editTicket(ticket_number, items)


	
if __name__ == "__main__":
	main()



#qString = "SELECT * FROM FOOTPRINTS.MASTER3 where MRID = 76444"
#qString = "DESCRIBE \'FOOTPRINTS.MASTER3\'"

#qString = "select TABLE_NAME, COLUMN_NAME from ALL_TAB_COLUMNS"

