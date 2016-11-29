import subprocess, datetime, json, paramiko, credentials

NO = 0
YES = 1

NOT_BILLABLE = 'No'
BILLABLE = 'Yes'

APPROVED_BY_MANAGER = 'on'
NOT_APPROVED_BY_MANAGER = 'off'

MEDIUM = 3
HIGH = 2

CREATOR_FILE = 'create.pl'
EDITOR_FILE = 'edit.pl'

ACCOUNT_NAME = 2
FIRST_NAME = 3
LAST_NAME = 4
EMAIL = 5
TITLE = 7
SELLER = 8
CATEGORY = 9
RATE = 10
QUANTITY = 11

def queryHolonet(qString):
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect('holonet.sdsc.edu', username=credentials.holonet_username, key_filename='../.ssh/id_rsa.openssh')

	script = "query.php \"" + qString + "\""

	stdin, stdout, stderr = ssh.exec_command('php ' + script)
	stderr = "".join(stderr.readlines())
	if len(stderr) != 0:
		print stderr
		ssh.close()

		raise BillingQueryError()
	ssh.close()
	return json.loads("".join(stdout.readlines()))

def callPerl(file, args):
	subprocess.call(['perl', file, 'x', json.dumps(args)])

def createTicket(project_name, billing_index, first_name, last_name, email):

	ticketTitle = 'Cloud - ['  + project_name + ']'

	args = {}
	args['projectID'] = 3
	args['title'] = ticketTitle
	args['assignees'] = ['c1mckay', 'ranakashima', 'kcoakley', 'cwalsworth']
	args['description'] = 'Initial creation of Master Ticket'# This is where I would add billing comments
	args['status'] = 'Open'
	args['priorityNumber'] = MEDIUM # 3 for medium, 2 for high


	projfields['Index__b1'] = billing_index
	projfields['Percent__b1'] = 100
	projfields['Billable'] = NOT_BILLABLE
	projfields['Approved__bby__bManager'] = APPROVED_BY_MANAGER
	projfields['Start__bDate'] = '2016-11-10'

	abfields = {}
	abfields['First__bName']    = first_name
	abfields['Last__bName']     = last_name
	abfields['Email__bAddress'] = email

	args['abfields']   = abfields
	args['projfields'] = projfields

	callPerl(CREATOR_FILE, args)

	qString = "SELECT MRID FROM FOOTPRINTS.MASTER3 where MRTITLE = '" + ticketTitle + "' and BILLABLE = 'No' and APPROVED__BBY__BMANAGER = 'on' and MRSTATUS != 'DELETED_'"
	ticketNumbers = queryHolonet(qString)
	ticketNumbers = [int(t['MRID']) for t in ticketNumbers]
	return max(ticketNumbers)


def editTicket(ticketNumber, line_items):
	args = {}
	args['projectID'] = 3
	args['mrID'] = ticketNumber

	converter = {
		"[Cloud Storage] Usage Charges": 1,
		"[Cloud Compute] Usage Charges": 2,
		"[Cloud Compute] Image Charges": 3,
		"[Cloud Compute] Volume Charges": 4,
		"[Cloud Compute] Volume Snapshot Charges": 5
	}

	titleToSeller = {
		"[Cloud Storage] Usage Charges": ("SRF__bCloud", "On__bDemand__bTriple__bCopy", 32.16),
		"[Cloud Compute] Usage Charges": ("SRF__bCloud", "Cloud__bCompute", 0.08),
		"[Cloud Compute] Image Charges": ("SRF__bCloud", "Cloud__bCompute", 0.08),
		"[Cloud Compute] Volume Charges": ("SRF__bCloud", "Cloud__bCompute", 0.08),
		"[Cloud Compute] Volume Snapshot Charges": ("SRF__bCloud", "Cloud__bCompute", 0.08)
	}

	productInfoFormat = {
		"[Cloud Storage] Usage Charges": "Cloud Storage: {0} TB",
		"[Cloud Compute] Usage Charges": "Cloud Compute Usage Charges: {0} Units",
		"[Cloud Compute] Image Charges": "Cloud Compute Image Charges: {0} Units",
		"[Cloud Compute] Volume Charges": "Cloud Compute Volume Charges: {0} Units",
		"[Cloud Compute] Volume Snapshot Charges": "Cloud Compute Volume Snapshot Charges: {0} Units"
	}

	projfields = {}

	product_text = ["", "", "", "", ""]

	charges = range(1,6)
	for line_item in line_items:
		title = line_item[TITLE]
		title = title[:title.index('(') - 1]

		n = converter[title]
		if n not in range(1,6):
			print 'failed on' + title
			return
		else:
			converter.pop(title)

		product_text[n - 1] = productInfoFormat[title].format(str(line_item[QUANTITY]))

		projfields['Item__b{0}__bSeller'.format(n)] = line_item[SELLER]
		projfields['Item__b{0}__bCategory'.format(n)] = line_item[CATEGORY]

		projfields['Item__b{0}__bQuantity'.format(n)] = line_item[QUANTITY]
		projfields['Item__b{0}__bRate'.format(n)] = line_item[RATE]

	#print converter.keys()
	
	for title in converter:
		n        = converter[title]
		seller   = titleToSeller[title][0]
		category = titleToSeller[title][1]
		rate     = titleToSeller[title][2]
		
		projfields['Item__b{0}__bSeller'.format(n)] = seller
		projfields['Item__b{0}__bCategory'.format(n)] = category

		projfields['Item__b{0}__bRate'.format(n)] = rate
		projfields['Item__b{0}__bQuantity'.format(n)] = 0

	projfields['Other__bProduct__bInfo'] = '\n'.join(product_text)

	args['projfields'] = projfields

	#sellers
	#possibleTitles = ['[Cloud Compute] Image Charges', '[Cloud Compute] Volume Snapshot Charges', '[Cloud Compute] Usage Charges', '[Cloud Storage] Usage Charges']

	#categories
	#['SRF__bCompute', 'SRF__bCloud']

	#print args

	callPerl(EDITOR_FILE, args)



