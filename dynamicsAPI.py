import requests
import json as JSON
from requests_ntlm import HttpNtlmAuth

apiURL = 'https://dynamics.sdsc.edu/sdsc/api/data/v8.0'


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
		

def authSess(username, password):
	session = requests.Session()
	session.auth = HttpNtlmAuth('ad\\' + username, password, session)
	return session

