import json, paramiko, sys

def getColumnNames():
	qString = "SELECT COLUMN_NAME FROM ALL_TAB_COLUMNS WHERE TABLE_NAME = 'MASTER3'"
	results = json.loads(queryHolonet(qString))
	return [x['column_name'] for x in results]

def getTableNames():
	qString = "SELECT TABLE_NAME FROM ALL_TAB_COLUMNS"# and rownum between 1 and 2"
	#qString = "SELECT COLUMN_NAME FROM ALL_TAB_COLUMNS where TABLE_NAME ='INVALID_CHARGES'"# and rownum between 1 and 2"
	
	results = queryHolonet(qString)
	results = json.loads(results)
	results = [x['table_name'] for x in results]
	print results
	return results


def queryHolonet(qString, longWay = True, onErr = None):
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect('holonet.sdsc.edu', username='c1mckay', key_filename='.ssh/id_rsa.openssh')
	script = "query.php " + str(longWay).lower() + " \"" + qString + "\""
	stdin, stdout, stderr = ssh.exec_command('php ' + script)
	err = "".join(stderr.readlines())
	if len(err) != 0:
		ssh.close()
		if onErr:
			raise onErr(err)
		else:
			print err
	ssh.close()
	return "".join(stdout.readlines())

def optQ(qString, name):
	results = queryHolonet(qString, False, None)
	results = json.loads(results)
	results = [x[name] for x in results]
	results = list(set(results))
	return results

#table_names = optQ("SELECT TABLE_NAME FROM ALL_TAB_COLUMNS", "TABLE_NAME")

index = 0
def gCol(table_name):
	qString = "SELECT COLUMN_NAME FROM ALL_TAB_COLUMNS WHERE TABLE_NAME = '" + table_name + "'"
	results = optQ(qString, "COLUMN_NAME")
	for r in results:
		print r
	return results

def main():
	jObject = json.loads(sys.argv[1])
	qString = jObject['query']
	if 'longWay' in jObject:
		longWay = jObject['longWay']
	else:
		longWay = True
	print queryHolonet(qString, longWay = longWay)


if __name__ == "__main__" and len(sys.argv) > 1:
	main()


#qString = "SELECT DISTNCT TABLE_NAME FROM ALL_TAB_COLUMNS WHERE TABLE_NAME = 'MASTER3'"
#queryHolonet(qString, longWay = False)