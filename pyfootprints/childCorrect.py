import csv, paramiko, json, subprocess, random

import credentials
from keystoneclient.v3 import client

from footprintsEditor import callPerl, EDITOR_FILE



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

def clearLine(ticketNumber, lineIndex):
	print '\tclearing ' + str(lineIndex)
	args = {}
	args['projectID'] = 3
	args['mrID'] = ticketNumber
	projfields = {}

	projfields['Item__b{0}__bSeller'.format(lineIndex)] = None
	projfields['Item__b{0}__bCategory'.format(lineIndex)] = None

	projfields['Item__b{0}__bRate'.format(lineIndex)] = None
	projfields['Item__b{0}__bQuantity'.format(lineIndex)] = None

	args['projfields'] = projfields

	callPerl(EDITOR_FILE, args)

tickets = range(78720, 78724) + range(78754, 78809)

for tick in tickets:
	print 'checking ticket ' + str(tick)
	for i in range(1, 11):
		quantity = 'ITEM__B{0}__BQUANTITY'.format(str(i))
		qString = 'SELECT ' + quantity + ' from FOOTPRINTS.MASTER3 where MRID = ' + str(tick)
		result = queryHolonet(qString)
		result = result[0][quantity]
		if(result == None or result == '0'):
			clearLine(tick, i)