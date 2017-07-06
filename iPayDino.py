from dynamicsAPI import Dino
import psycopg2





invoices = dino.getInvoicesBetween('2017-06-26', '2017-06-29')

#print invoices[0]


#print invoice['invoiceid'] 

for invoice in invoices:
	if invoice['new_index_1'] != 'PAYROLL':
		continue
	#print invoice['name']
	invoiceid = invoice['invoiceid']

	#should be contact
	customerid = dino.getCustomerID(invoiceid)

	pid = dino.getPID(customerid)

	if pid is None:
		print str(invoice['name']) + '\n\t no pid found'
		continue
	indexes = payrollLookup(pid)


	if len(indexes) == 0:
		print str(invoice['name']) + '\n\tno indexes found, ' + '\n\tPID : ' + str(pid)
		continue


	dino.updateInvoice(invoiceid, indexes)
	print '\n\n'
#	

#for item, value in invoices[0].items():
#	print item + '\t' + str(value)

#print len(invoices)

#print invoiceid

#print dino.updateInvoice(invoiceid, [['cachukk', 52]])


