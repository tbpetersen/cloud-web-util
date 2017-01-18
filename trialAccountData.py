from db_communicator import query

from openstack_utility import keyStoneUtility
import json, credentials, datetime

pBuilder = keyStoneUtility.KeyStoneUtility(username = credentials.open_stack_username, password=credentials.open_stack_pw, auth_url = credentials.open_stack_url, 
		auth_url_dep = credentials.open_stack_url_dep, tenant_name=credentials.open_stack_username)

results = query('select project_id, name, created, notified, warning_length, delete_length from trial_projects', (), True)

trialData = []

for r in results:
	proj_o = pBuilder.getProject(r[1])
	if proj_o == None:
		continue
	dataPacket = {}
	dataPacket['projectName'] = r[1]
	dataPacket['projCreated'] = (r[2]-datetime.date(1970,1,1)).total_seconds()
	dataPacket['trialLength'] = (r[5])

	dataPacket['contactEmail'] = proj_o.contact_email
	dataPacket['contactName'] = proj_o.contact_name

	trialData.append(dataPacket)

print json.dumps(trialData)

"""var url = "https://cloud-web-util.ucsd.edu/requestTrials"
	 var method = "GET";
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
	 request.send();
	 """