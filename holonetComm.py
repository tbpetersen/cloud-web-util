import json, paramiko

def getColumnNames():
	qString = "SELECT COLUMN_NAME FROM ALL_TAB_COLUMNS WHERE TABLE_NAME = 'MASTER3'"
	results = json.loads(queryHolonet(qString))
	return [x['column_name'] for x in results]


def queryHolonet(qString):
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect('holonet.sdsc.edu', username='c1mckay', key_filename='.ssh/id_rsa.openssh')

	script = "query.php \"" + qString + "\""

	stdin, stdout, stderr = ssh.exec_command('php ' + script)
	err = "".join(stderr.readlines())
	if len(err) != 0:
		print err
		ssh.close()
		raise BillingQueryError()
	ssh.close()
	return "".join(stdout.readlines())