import json, subprocess, random, sys

import credentials
from keystoneclient.v3 import client

from pyfootprints.footprintsEditor import createTicket, editTicket
from db_communicator import query

def main(project_name, shouldPrint = True):
	if len(sys.argv) < 2:
		return
	ticketNumber = createTicket(project_name = project_name, billing_index = 'CACNULL', first_name = 'Andrew', last_name = 'Ferbert', email = 'dferbert@sdsc.edu', title='Commvault Invoice - {0}', t_assignees=['dferbert'])
	query("insert into commvault_tickets (name, ticket_number) VALUES (%s, %s);", [project_name, ticketNumber], False)
	if shouldPrint:
		print ticketNumber
	return ticketNumber


if __name__ == "__main__":
	project_name = sys.argv[1]
	main(project_name = project_name)

