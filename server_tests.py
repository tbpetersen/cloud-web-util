import subprocess, time, requests, sys, base64
import credentials

from db_communicator import query




def getCredentials():
	return base64.b64encode(credentials.ad_username + ":" + credentials.ad_password)

def runTests():
	r = requests.post("https://cloud-web-util.ucsd.edu/new-commvault-ticket", data='c1mckaytest', verify=False, headers={'Authorization': getCredentials()})
	print 'delete ticket ' + r.text + ' on footprints'
	query("delete from commvault_tickets where ticket_number = %s;", [ticketNumber], False)
	# r.status_code




if __name__ == "__main__":
	server_process = subprocess.Popen(["node","server.js"])

	time.sleep(2)
	try:
		runTests()
	except Exception as e:
		print e

	time.sleep(5)

	server_process.terminate()

