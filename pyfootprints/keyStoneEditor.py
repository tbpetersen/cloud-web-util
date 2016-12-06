import credentials, json
from keystoneclient.v3 import client

ticket_data = {'itunix-backup': 76552, 's1yeu': 76503, 'nds-structural-biology-data-grid': 76545, 'ctan': 76530, 'djmoore': 76543, 'gdc': 76547, 'dclde': 76538, 'c1mckay': 76491, 'sdsc-big-data-analytics': 76535, 'sdsc-docs': 76580, 'suave': 76497, 'colby': 76496, 'leung_research_group': 76564, 'cfmri': 76493, 'cipres': 76519, 'commvault-ucd-its': 76526, 'librarydataworkshops': 76490, 'pmulrooney': 76573, 'jpltest': 76492, 'lca': 76561, 'zonca-test': 76498, 'colby_test': 76506, 'itsystems': 76551, 'reyalab': 76575, 'ux453261': 76601, 'ucm_faculty': 76585, 'philippines': 76572, 'ucsd_biochemical_genetics': 76600, 'commvault-cvma1': 76520, 'shuchien': 76582, 'commvault-ehs': 76521, 'commvault-isafe': 76522, 'jpl-pz-4': 76557, 'cyoun': 76533, 'jpl-pz-2': 76555, 'jpl-pz-3': 76556, 'commvault-mpl': 76523, 'acid': 76512, 'commvault-opthalmology': 76524, 'keltner-ucsd-cloud': 76560, 'delphi': 76541, 'Wuerthwein': 76505, 'ucrback10': 76589, 'rpwagner': 76576, 'openstack-logs': 76540, 'uci-astrixdb': 76516, 'imaging': 76550, 'jmarquie': 76553, 'klcadm': 76500, 'trial': 76508, 'sharma_lab': 76581, 'gordon': 76548, 'olefskylab': 76515, 'ucrback': 76587, 'ucr-academic-senate': 76586, 'selectornet': 76539, 'commvault-ucsdfdc': 76527, 'posakony_lab': 76574, 'jeff': 76509, 'zonca': 76489, 'ucsd_admissions': 76599, 'opentopography': 76569, 'fenglab': 76499, 'kcoakley': 76559, 'cinergi': 76518, 'dferbert': 76542, 'cloud-customer-archive': 76510, 'sciviscontest': 76579, 'hutton': 76549, 'cycorecalit2': 76531, 'cbrown': 76507, 'wasdev': 76602, 'ucrback2': 76590, 'nickel': 76567, 'commvault-rady': 76525, 'ucrback4': 76592, 'cdltemp': 76517, 'csh-it': 76528, 'bejarlab': 76513, 'pace': 76570, 'BioKepler': 76495, 'scidrive': 76577, 'ucrback9': 76597, 'ucrback8': 76596, 'ucrback1': 76588, 'sysadmin-l': 76584, 'ucrback3': 76591, 'jpl-pz-1': 76554, 'ucrback5': 76593, 'liai_irt': 76565, 'ucrback7': 76595, 'ucrback6': 76594, 'spg': 76583, 'dofranklin': 76544, 'less_than_50': 76563, 'bella': 76514, 'salk-storage-gateway': 76534, 'gnocchi': 76537, 'ucsb-bren': 76598, 'c1mckayadm': 76511, 'lcrews': 76562, 'normanlab': 76568, 'merritt': 76566, 'palms': 76571, 'ndslabs': 76494, 'cycoresdsc': 76532, 'dacor': 76536, 'polar-coding': 76502, 'kagnofflab': 76558, 'hng': 76504, 'csunbackup': 76529, 'scidrivedemo': 76578, 'coursera-backup': 76501, 'gdc_sdsc_ccle': 76546}
ticket_data = json.loads(ticket_data)

def getTicket(project_name):
	return ticket_data[project_name]


keyStone = client.Client(username = credentials.open_stack_username, 
	password=credentials.open_stack_pw, 
	auth_url = credentials.open_stack_url)



originalIndexes = {}
for project in keyStone.projects.list():
	originalIndexes[project.name] = project.billing_index
	if getTicket(project.name) != None:
		keyStone.projects.update(project.id, billing_index = getTicket(project.name))

print originalIndexes