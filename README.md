### This should now be on the SDSC gitlab server.

Auto-Email System

NodeJS serves as the top level HTTP handler.  All the requests are password protected and sent over https.  The server lives on port 8134.  All valid requests will return '200 OK'.

Authentication
Password protection works by submitting a username and password to '/login'.  If successful, the server will spit a token back at you to be used with all other requests.  Currently, the server will only accept one token.  That token is generated and 'saved' server side each time a logon is done.  So logging in on one device, and then another, and then trying to use the same token from the previous one will not work.

Python
Almost all other work is done by calling the 'extractor.py' file with the appropriate arguments.

Sending Email
To report to the users of a project, make a POST request with the url being the project name.  For example, the url would be "https://holonet.sdsc.edu:8134/biokepler".  Once an email is sent, the time is logged in a file on holonet, and until '30 days' have passed, attempts to send email to this user will result in 'spam errors' with an error code of 405.

Getting all the data
To get all the information on the bouncing tickets, make a GET request to 'https://holonet.sdsc.edu:8134/requestData'.

The format will be as follows:
{
	'validProjects':[
		{
			'projectName': 'BioKepler',
			'contactEmail': 'bio@sdsc.edu',
			'emailDates': [epoch time in seconds],
			'failingType': ['Cloud Storage', 'Cloud Compute'],
			'warningLevel': '3rd warning',
			'ticketNumbers': [3342,2415,3241,9983]
		},
		{
			'projectName': 'sdsc-analytics',
			'contactEmail': 'analytics@sdsc.edu',
			'emailDates': [],
			'failingType': ['Cloud Storage', 'Cloud Compute'],
			'warningLevel': '3rd warning',
			'ticketNumbers': [3342,2415,3241,9983]
		}
	],
	'weirdTickets':[
		{
			'ticketNumber' : 4232,
			'projectName' : 'BioKepler'
			'month' : 8, //signifying months since this ticket bounced
			'failingType' : 'Cloud Storage'
		},
		{
			'ticketNumber' : 3938,
			'projectName' : 'SDSC-Analytics'
			'month' : 2, 
			'failingType' : 'Cloud Compute'
		},
	],
	'error': 'Reason why it failed'
}

Creating a project:
To create a project/account combo, make a POST request to "https://holonet.sdsc.edu:8134/account".  Any users for the account must be emails. The account data should be of this format:
{
	'projectName': 'BioKeplerTest',
	'contactEmail': 'bio@sdsc.edu',
	'contactName': 'Fred Fred',
	'users': ['userAccount1@sdsc.edu', 'userAccount2@sdsc.edu'],
	'index': 'CACTRIA', //unneeded if isTrial is true
	'isTrial': true,
	'warningTime': 60,
	'expirationTime' 90
}
This script automatically sends out passwords for the new users being created through onetimepassword.net, but it also handles old usernames(emails) correctly.  It doesn't reset the password.
