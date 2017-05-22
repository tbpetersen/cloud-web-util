import csv, paramiko, json, subprocess, random, sys

import credentials
from keystoneclient.v3 import client

from footprintsEditor import createTicket, editTicket
	
def getLineItems(file_name):
	with open(file_name, 'rb') as f:
		reader = csv.reader(f)
		line_items = list(reader)

	return [line_item for line_item in line_items if line_item[0] != "start_date"]

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


def main(file_name):

	ACCOUNT_NAME = 2
	
	projectToCharges = {}
	for line_item in getLineItems(file_name):
		p_name = line_item[ACCOUNT_NAME]
		if p_name not in projectToCharges:
			projectToCharges[p_name] = []
		projectToCharges[p_name].append(line_item)


	
	for project_name, items in projectToCharges.items():
		if project_name in ['fowlerlab']:
			continue

		#print project_name #+ str([item[11] for item in items])
		ticket_number = items[0][6]
		if ticket_number.isdigit():
			editTicket(items[0][6], items)
		else:
			print project_name + " didn't have a ticket number associated with it"

	
if __name__ == "__main__":
	if len(sys.argv) != 2:
		print 'Usage: ' + sys.argv[0] + ' file_name'
	else:
		main(sys.argv[1])



#qString = "SELECT * FROM FOOTPRINTS.MASTER3 where MRID = 76444"
#qString = "DESCRIBE \'FOOTPRINTS.MASTER3\'"

#qString = "select TABLE_NAME, COLUMN_NAME from ALL_TAB_COLUMNS"

