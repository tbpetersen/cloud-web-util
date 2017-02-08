import re, sys, json
import paramiko


def queryHolonet(qString):
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect('holonet.sdsc.edu', username='c1mckay', key_filename='.ssh/id_rsa.openssh')

	script = "query.php \"" + qString + "\""

	stdin, stdout, stderr = ssh.exec_command('php ' + script)
	err = "".join(stderr.readlines())
	if len(err) != 0 and 'PHP Warning' not in err:
		print err
		ssh.close()
		#raise BillingQueryError(err)
		return
	ssh.close()
	return "".join(stdout.readlines())

def main():
	if len(sys.argv) != 2:
		return
	username = sys.argv[1]
	username = re.sub(r'[^a-zA-Z0-9]', '', username)
	qString = "SELECT MRID, MRASSIGNEES, MRDESCRIPTION, MRALLDESCRIPTIONS, MRSTATUS, MRTITLE, MRUPDATEDATE, MRSUBMITDATE FROM FOOTPRINTS.MASTER3 where UPPER(MRASSIGNEES) LIKE '%{0}%' and MRSTATUS != '_DELETED_'".format(username.upper())
	print queryHolonet(qString)

	


if __name__ == "__main__":
	main()

"""
var url = "https://cloud-web-util.ucsd.edu/trelloCompliment"
	 var method = "POST";
	 var a_sync = true;
	 var request = new XMLHttpRequest();
	 var token = localStorage.getItem("loginToken");
	 request.onload = function () {
	 	 var status = request.status;
	 	 if (status === 401) {
	 	 	window.location.href = "https://cloud-web-util.ucsd.edu/projectCreation/login.html";
	 	 	return;
	 	 }
	 	 if(status !== 200){
	 	 	console.log(request.responseText);
	 	 }
	 	 	
		 console.log(request.responseText);
	 }
	 request.open(method, url, a_sync);
	 request.setRequestHeader('Authorization', token);
	 request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
	 request.send('c1mckay');
	 """