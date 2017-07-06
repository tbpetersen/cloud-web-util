import requests, psycopg2
import json as JSON
from requests_ntlm import HttpNtlmAuth

apiURL = 'https://dynamics.sdsc.edu/sdsc/api/data/v8.0'

NUM_OF_INDICIES = 15
MAX_DESC_INVOICE_CHAR_LIMIT = 60

class DynamicsQueryError(Exception):
	def __init__(self,*args,**kwargs):
		Exception.__init__(self,*args,**kwargs)

class Dino:

	def __init__(self, username, pw):
		self.sesh = authSess(username, pw)

	def query(self, url):
		response = self.sesh.get(apiURL + '/' + url)
		if response.status_code == 204 or response.status_code == 200:
			return JSON.loads(response.text)['value']
		raise DynamicsQueryError(response.text)

	def getProductID(self, name):
		response = self.query('products?$select=name&$filter=name eq \'{0}\''.format(name))
		return response[0]['productid']

	def getProduct(self, name):
		response = self.query('products?$select=name, _defaultuomid_value&$filter=name eq \'{0}\''.format(name))
		return response[0]

	def getAccountID(self, name):
		response = self.query('accounts?$select=name&$filter=name eq \'{0}\''.format(name))
		if len(response) == 0:
			raise DynamicsQueryError(name + " not found")
		return response[0]['accountid']

	def getAccountName(self, accountID):
		response = self.query('accounts?$select=name&$filter=accountid eq \'{0}\''.format(accountID))
		if len(response) == 0:
			raise DynamicsQueryError(name + " not found")
		return response[0]['name']

	def getMasterTicketID(self, accountID):
		response = self.query('salesorders?$select=salesorderid&$filter=_customerid_value eq {0}'.format(accountID))
		if len(response) == 0:
			raise DynamicsQueryError(accountID + " didn't have a master ticket")
		return response[0]['salesorderid']

	def getMasterTicketIDByName(self, name):
		response = self.query('salesorders?$select=salesorderid&$filter=name eq \'{0}\''.format(name))
		if len(response) == 0:
			raise DynamicsQueryError(name + " wasn't found")
		return response[0]['salesorderid']

	def getDetails(self, orderID):
		return self.query('salesorderdetails?$filter=_salesorderid_value eq {0}'.format(orderID))

	def getDetailIDs(self, orderID):
		response = self.query('salesorderdetails?$filter=_salesorderid_value eq {0}'.format(orderID))
		return [r['salesorderdetailid'] for r in response]

	def deleteDetailID(self, orderID):
		response = self.sesh.delete(apiURL + '/salesorderdetails({0})'.format(orderID))
		if response.status_code != 204:
			raise DynamicsQueryError(response.text)

	def deleteDetails(self, masterTicketID):
		idsOfAllDetails = self.getDetailIDs(masterTicketID)
		for detailID in idsOfAllDetails:
			self.deleteDetailID(detailID)

	#order detail
	def createDetail(self, orderID, productName, quantity):
		product = self.getProduct(productName)
		productID = product['productid']
		productUnit = product['_defaultuomid_value']
		head = {
			'Content-type': 'application/json'
		}
		#accountID = accountID.replace("-", '')
		payload = {
			'salesorderid@odata.bind': '/salesorders(' + orderID + ')',
			'productid@odata.bind':'/products(' +  productID + ')' ,
			'uomid@odata.bind':'/uoms('+ productUnit +')',
			'quantity' : float(quantity)
		}
		head = {'Content-type': 'application/json'}
		response = self.sesh.post(apiURL + '/salesorderdetails', json = payload, headers = head)
		if response.status_code != 204:
			print response
			raise DynamicsQueryError(response.text)

	def getContact(self, contact_id):
		return self.query('contacts?$filter=contactid eq {0}&$select=contactid'.format(contact_id))

	def isContact(self, customer_id):
		try:
			self.getContact(customer_id)
			isContact = True
		except IndexError:
			isContact = False

		try:
			self.getAccountName(customer_id)
			isAccount = True
		except IndexError:
			isAccount = False

		if isAccount and isContact:
			return None

		if (not isAccount) and (not isContact):
			return None

		return isContact

	def createInvoice(self, order):
		accountName = self.getAccountName(order.accountID)

		invoiceName = '' #TODO line 425
		dateDelivered : getEndOfMonth()

		payload = order.getPayload(accountName)
		



	def getInvoicesBetween(self, dMin, dMax):
		query = 'invoices?$filter=datedelivered gt ' + dMin
		if dMax:
			query += ' and datedelivered lt ' + dMax
		response = self.query(query)
		return response
		
	#example ind : [ [cacnull, 50], [cacsmtn, 50] ]
	def updateInvoice(self, invoiceid, ind):
		payload = {}
		for i in range(len(ind)):
			payload['new_index_' + str(i + 1)] = ind[i][0]
			payload['new_percentage_' + str(i + 1)] = ind[i][1]
		
		head = {'Accept': 'application/json',
			'OData-MaxVersion': '4.0',
			'OData-Version': '4.0'
		}

		url = '/invoices(' + invoiceid + ')'
		response = self.sesh.patch(apiURL + url, json = payload, headers = head)

		if response.status_code != 204 and response.status_code != 200:
			raise DynamicsQueryError(response.text)

	def getCustomerID(self, invoiceid):
		response = self.query('invoices?$select=_customerid_value&$filter=invoiceid eq {0}'.format(invoiceid))
		if len(response) < 1:
			raise DynamicsQueryError('No invoice with that id found')
		return response[0]['_customerid_value']

	def getPID(self, customerID):
		response = self.query('contacts?$select=new_pid&$filter=contactid eq {0}'.format(customerID))
		#response = self.query('contacts?$top=2')
		if len(response) < 1:
			raise DynamicsQueryError('No customer with that id found')
		#return response[0]['_customerid_value']
		return response[0]['new_pid']
	#def getPID(self, acc)

class IndexGroup:
	def __init__(self, index, percentage, position):
		if index is '':
			index = None
		self.index = index
		self.percent = percentage
		self.position = position

	def addToPayload(self, payload):
		payload['new_index_' + self.position] = self.index
		payload['new_percentage_' + self.position] = self.percent



class Order:
	def __init__(self, order, isContact):
		self.name        = order['name']
		self.id          = order['salesorderid']
		self.customerID  = order['_customerid_value']
		self.description = order['description']
		self.priceListID = order['_pricelevelid_value']

		self.indices = []
		for i in range(1, NUM_OF_INDICIES + 1):
			index_name = order['new_index_' + i]
			index_percent = order['new_percentage_' + i]
			index = IndexGroup(index_name, index_percent, i)
			self.indices.append(index)

		self.isContact = isContact

	def getPayload(self):
		payload = {
			'name'          : invoiceName,
			'dateDelivered' : dateDelivered,
			'description'   : order.description[:MAX_DESC_INVOICE_CHAR_LIMIT],
			'salesorderid@odata.bind' : '/salesorders({0})'.format(self.id),
			'pricelevelid@odata.bind' : '/pricelevels({0})'.format(self.priceListID)
		}

		for ind in order.indices:
			ind.addToPayload(payload)

		if self.isContact:
			payload['customerid_contact@odata.bind'] = '/contacts({0})'.format(self.customer_id)
		else:
			payload['customerid_account@odata.bind'] = '/accounts({0})'.format(self.customer_id)

		#

		return payload

class Detail:
	def __init__(self, detail):
		self.productID = detail['productid']
		self.unitID    = detail['unitid']
		self.quantity  = detail['quantity']

def authSess(username, password):
	session = requests.Session()
	session.auth = HttpNtlmAuth('ad\\' + username, password, session)
	return session

def isValidCustomerID(sesh, customer_id):
	return sesh.isContact(customer_id) is not None


def payrollLookup(pid):
	conn = psycopg2.connect("dbname='{0}' user='{1}' host='{2}' password='{3}' port={4}".format())#todo config
	cur = conn.cursor()

	queryString = 'select indx, pct, pct_time from recharge_pub.payroll_snapshot where pid=%s'
	values = [pid]	
	
	cur.execute(queryString, values)
	result = cur.fetchall()
	
	conn.commit()
	cur.close()
	conn.close()

	res = []
	seen = [] #necessary because the database gives back double values.  Only interested in unique values
	for r in result:
		if r[0] not in seen:
			res.append([r[0], r[1] * r[2]])
			seen.append(r[0])

	return res
