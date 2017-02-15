import sys, json, re

from db_communicator import query

from openstack_utility import keyStoneUtility
import json, credentials, datetime

import pyfootprints.footprintsEditor as tEditor
from email_util import sendMail


pBuilder = keyStoneUtility.KeyStoneUtility(username = credentials.open_stack_username, password=credentials.open_stack_pw, auth_url = credentials.open_stack_url, 
		auth_url_dep = credentials.open_stack_url_dep, tenant_name=credentials.open_stack_username)

class InvalidCharacters(Exception):
	def __init__(self,*args,**kwargs):
		Exception.__init__(self,*args,**kwargs)

def validateProjectName(pName):
	return match is not None

def main():
	argCount = len(sys.argv)
	if argCount != 2:
		return
	#return
	data = json.loads(sys.argv[1])

	project_name = data[0]
	project_index = data[1].upper()

	if not validateProjectIndex(project_index):
		raise InvalidCharacters()

	project_o = pBuilder.getProject(project_name)
	if project_o == None:
		return

	contact_name = project_o.contact_name
	if ' ' in contact_name:
		indexOfSpace = contact_name.index(' ')
		first_name = contact_name[:indexOfSpace]
		last_name = contact_name[indexOfSpace + 1:]
	else:
		first_name = contact_name
		last_name = contact_name	
	title = None #auto set in create ticket
	assignees = None #auto set in create ticket

	ticketNumber = tEditor.createTicket(project_name, project_index, first_name, last_name, project_o.contact_email, title, assignees)
	pBuilder.setBillingInfo(project_name, str(ticketNumber))

	query('delete from trial_projects where name = %s;', tuple([project_name]), False)

	subj = "Cloud Project Upgraded [{0}]".format(project_name)
	msg = "The Cloud Project " + project_name + " has been upgraded to a paid project \n\n\n Cloud-Web-Util"
	sendMail("cloud-web-util@sdsc.edu", ["ranakashima@sdsc.edu", "c1mckay@sdsc.edu"], subj, msg)
	print ticketNumber

if __name__ == "__main__":
	main()

"""
var url = "https://cloud-web-util.ucsd.edu/convertTrialProject"
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
	 request.send(JSON.stringify(['c1mckaytrialdatatest', 'index']));
"""