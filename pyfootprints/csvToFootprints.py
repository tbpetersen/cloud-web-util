import csv, paramiko, json, subprocess, random

import credentials
from keystoneclient.v3 import client

from footprintsEditor import createTicket, editTicket

file_name = '../commvault.csv'
#file_name = 'example.csv'


def queryHolonet(qString):
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect('holonet.sdsc.edu', username='c1mckay', key_filename='.ssh/id_rsa.openssh')
	script = "query.php \"" + qString + "\""
	stdin, stdout, stderr = ssh.exec_command('php ' + script)
	stderr = "".join(stderr.readlines())
	if len(stderr) != 0:
		print stderr
		ssh.close()
		raise BillingQueryError()
	ssh.close()
	return json.loads("".join(stdout.readlines()))

def getLineItems():
	with open(file_name, 'rb') as f:
		reader = csv.reader(f)
		line_items = list(reader)

	return [line_item for line_item in line_items if line_item[0] != "start_date"]

#https://docs.oracle.com/cd/B19306_01/server.102/b14237/statviews_2094.htm
def getColumnNames():
	qString = "select TABLE_NAME, COLUMN_NAME from ALL_TAB_COLUMNS"
	results = queryHolonet(qString)
	column_names = [r['COLUMN_NAME'] for r in results if r['TABLE_NAME'] == 'MASTER3']
	return column_names

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

def main():

	ACCOUNT_NAME = 2
	ticket_data = {'itunix-backup': 76552, 's1yeu': 76503, 'nds-structural-biology-data-grid': 76545, 'ctan': 76530, 'djmoore': 76543, 'gdc': 76547, 'dclde': 76538, 'c1mckay': 76491, 'sdsc-big-data-analytics': 76535, 'sdsc-docs': 76580, 'suave': 76497, 'colby': 76496, 'leung_research_group': 76564, 'cfmri': 76493, 'cipres': 76519, 'commvault-ucd-its': 76526, 'librarydataworkshops': 76490, 'pmulrooney': 76573, 'jpltest': 76492, 'lca': 76561, 'zonca-test': 76498, 'colby_test': 76506, 'itsystems': 76551, 'reyalab': 76575, 'ux453261': 76601, 'ucm_faculty': 76585, 'philippines': 76572, 'ucsd_biochemical_genetics': 76600, 'commvault-cvma1': 76520, 'shuchien': 76582, 'commvault-ehs': 76521, 'commvault-isafe': 76522, 'jpl-pz-4': 76557, 'cyoun': 76533, 'jpl-pz-2': 76555, 'jpl-pz-3': 76556, 'commvault-mpl': 76523, 'acid': 76512, 'commvault-opthalmology': 76524, 'keltner-ucsd-cloud': 76560, 'delphi': 76541, 'Wuerthwein': 76505, 'ucrback10': 76589, 'rpwagner': 76576, 'openstack-logs': 76540, 'uci-astrixdb': 76516, 'imaging': 76550, 'jmarquie': 76553, 'klcadm': 76500, 'trial': 76508, 'sharma_lab': 76581, 'gordon': 76548, 'olefskylab': 76515, 'ucrback': 76587, 'ucr-academic-senate': 76586, 'selectornet': 76539, 'commvault-ucsdfdc': 76527, 'posakony_lab': 76574, 'jeff': 76509, 'zonca': 76489, 'ucsd_admissions': 76599, 'opentopography': 76569, 'fenglab': 76499, 'kcoakley': 76559, 'cinergi': 76518, 'dferbert': 76542, 'cloud-customer-archive': 76510, 'sciviscontest': 76579, 'hutton': 76549, 'cycorecalit2': 76531, 'cbrown': 76507, 'wasdev': 76602, 'ucrback2': 76590, 'nickel': 76567, 'commvault-rady': 76525, 'ucrback4': 76592, 'cdltemp': 76517, 'csh-it': 76528, 'bejarlab': 76513, 'pace': 76570, 'BioKepler': 76495, 'scidrive': 76577, 'ucrback9': 76597, 'ucrback8': 76596, 'ucrback1': 76588, 'sysadmin-l': 76584, 'ucrback3': 76591, 'jpl-pz-1': 76554, 'ucrback5': 76593, 'liai_irt': 76565, 'ucrback7': 76595, 'ucrback6': 76594, 'spg': 76583, 'dofranklin': 76544, 'less_than_50': 76563, 'bella': 76514, 'salk-storage-gateway': 76534, 'gnocchi': 76537, 'ucsb-bren': 76598, 'c1mckayadm': 76511, 'lcrews': 76562, 'normanlab': 76568, 'merritt': 76566, 'palms': 76571, 'ndslabs': 76494, 'cycoresdsc': 76532, 'dacor': 76536, 'polar-coding': 76502, 'kagnofflab': 76558, 'hng': 76504, 'csunbackup': 76529, 'scidrivedemo': 76578, 'coursera-backup': 76501, 'gdc_sdsc_ccle': 76546}

	projectToCharges = {}
	for line_item in getLineItems():
		p_name = line_item[ACCOUNT_NAME]
		if p_name not in projectToCharges:
			projectToCharges[p_name] = []
		projectToCharges[p_name].append(line_item)


	
	for project_name, items in projectToCharges.items():
		if project_name in ['fowlerlab']:
			continue

		print project_name #+ str([item[11] for item in items])
		ticket_number = ticket_data[project_name]
		editTicket(items[0][6], items)
		#editTicket(76488, items)


	
if __name__ == "__main__":
	main()



#qString = "SELECT * FROM FOOTPRINTS.MASTER3 where MRID = 76444"
#qString = "DESCRIBE \'FOOTPRINTS.MASTER3\'"

#qString = "select TABLE_NAME, COLUMN_NAME from ALL_TAB_COLUMNS"

