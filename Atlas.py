import json
import time
import time,hmac,base64,hashlib,urllib,urllib2,json
from hashlib import sha256
from decimal import Decimal
import datetime
import sys
import os
import httplib
import requests
#Adapted from Gox Class

class AtlasClient:
	timeout = 15
	tryout = 0

	def __init__(self, key=''):
		self.key = key
		self.time = {'init': time.time(), 'req': time.time()}
		self.reqs = {'max': 10, 'window': 10, 'curr': 0}
		self.base = 'https://atlasats.hk/'
		
	def throttle(self):
		# check that in a given time window (10 seconds),
		# no more than a maximum number of requests (10)
		# have been sent, otherwise sleep for a bit
		diff = time.time() - self.time['req']
		if diff > self.reqs['window']:
			self.reqs['curr'] = 0
			self.time['req'] = time.time()
		self.reqs['curr'] += 1
		if self.reqs['curr'] > self.reqs['max']:
			print 'Request limit reached...'
			time.sleep(self.reqs['window'] - diff)

	def req(self, path, inp=None):
		t0 = time.time()
		tries = 0
		funds_error=False
		while True:
			# check if have been making too many requests
			self.throttle()

			try:
				# send request to mtgox
				opener = urllib2.build_opener()
				opener.addheaders = [("Authorization" , "Token token="+self.key )]
				if inp==None:
					response = opener.open(self.base+path)
				else:
				    inpstr = urllib.urlencode(inp.items())
				    response = opener.open(self.base+path+"?"+inpstr)


				# interpret json response
				output = json.load(response)

				if 'error' in output:
					if output['error']!=[]:
						print output
						raise ValueError(output['error'])


				return output
				
			except Exception as e:
			    print str(e)
			    exc_type, exc_obj, exc_tb = sys.exc_info()
			    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
			    print(exc_type, fname, exc_tb.tb_lineno)			    
			    print "Error: %s" % e


			# don't wait too long
			tries += 1
			if time.time() - t0 > self.timeout or tries > self.tryout:
				
				if funds_error:
					raise Exception('Funds')       
				else:
					raise Exception('Timeout')
	def req_post(self, path, inp=None):
		t0 = time.time()
		tries = 0
		funds_error=False
		while True:
			# check if have been making too many requests
			self.throttle()
			try:
				# send request to mtgox
				opener = urllib2.build_opener()
				opener.addheaders = [("Authorization" , "Token token="+self.key )]
				if inp==None:
					response = opener.open(self.base+path)
				else:
				    inpstr = urllib.urlencode(inp.items())
				    response = opener.open(self.base+path,inpstr)

				# interpret json response
				output = json.load(response)

				if 'error' in output:
					if output['error']!=[]:
						print output
						raise ValueError(output['error'])


				return output
				
			except Exception as e:
			    print str(e)
			    exc_type, exc_obj, exc_tb = sys.exc_info()
			    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
			    print(exc_type, fname, exc_tb.tb_lineno)			    
			    print "Error: %s" % e


			# don't wait too long
			tries += 1
			if time.time() - t0 > self.timeout or tries > self.tryout:
				
				if funds_error:
					raise Exception('Funds')       
				else:
					raise Exception('Timeout')
				    
	def req_delete(self, path):
		t0 = time.time()
		tries = 0
		funds_error=False
		while True:
			# check if have been making too many requests
			self.throttle()
			try:
				# send request to mtgox
				headers = {'Authorization':  "Token token="+self.key}
				req = requests.request('DELETE',self.base+path,headers=headers )
				
				output = req.json()

				if 'error' in output:
					if output['error']!=[]:
						print output
						raise ValueError(output['error'])


				return output
				
			except Exception as e:
			    print str(e)
			    exc_type, exc_obj, exc_tb = sys.exc_info()
			    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
			    print(exc_type, fname, exc_tb.tb_lineno)			    
			    print "Error: %s" % e


			# don't wait too long
			tries += 1
			if time.time() - t0 > self.timeout or tries > self.tryout:
				
				if funds_error:
					raise Exception('Funds')       
				else:
					raise Exception('Timeout')  				    

def get_best_bid(book):
	best_price=0.0
	for item in book['bids']:
		price = float(item[0])
		volume = float(item[1])
		if volume> .25:
			if price>best_price:
				best_price=price
			
	return best_price
		
def get_best_ask(book):
	best_price=100000000
	for item in book['asks']:
		price = float(item[0])
		volume = float(item[1])
		if volume>.25:
			if price<best_price:
				best_price=price

	return best_price

def cancel_all_orders():
    x=0
    results=client.req_post(api_version+'orders')
    for item in results:
	if item['status']=='OPEN':
	    cancel_order(item['oid'])
	    x+=1
    return x

def cancel_order(oid):
    #Placing An Order
    return client.req_delete(api_version+'orders/'+oid)

def place_limit_order(side,pair,price,volume):
	#Placing An Order
	item=pair.split('_')[0]
	currency=pair.split('_')[1]
	price=round(price,2)
	volume=round(volume,4)
	return client.req_post(api_version+'orders',{'item':item,'currency':currency,'side':side,'price':price,'quantity':volume,'type':"limit"})['oid']

def get_balances():
    account_info=client.req(api_version+'account')
    btc_size=0.0
    for item in account_info['positions']:
        if item['item']=='BTC':
            btc_size=item['size']
    return account_info['buyingpower'],btc_size

def is_order_live(oid):
    if oid==None:
	return False
    order_info=client.req(api_version+'orders/'+oid)
    if order_info['status']!='OPEN':
	return False
    else:
	return True

def get_nbbo_krak(pair,thresh=.1):
		item=pair.split('_')[0]
		currency=pair.split('_')[1]
		best_bid_krak=0
		best_ask_krak=1000000
		book=client.req(api_version+'market/book',{'item':item,'currency':currency})
		
		for item in book['quotes']:
			if float(item['price'])>best_bid_krak and float(item['size'])>thresh and item['side']=="BUY":
				best_bid_krak=float(item['price'])
			if float(item['price'])<best_ask_krak and float(item['size'])>thresh and item['side']=="SELL":
				best_ask_krak=float(item['price'])	
		#for item in account_info['positions']:
		#	if item['item']=='BTC':
		#		btc_size=item['size']
		#return account_info['buyingpower'],btc_size
		return best_bid_krak,best_ask_krak

#Put Your Api Key Here
key=""
client = AtlasClient(key)
api_version='api/v1/'

print str(cancel_all_orders())+" Orders Cancelled"

#Get Balances
usd_balance,btc_balance=get_balances()
print get_nbbo_krak("BTC_USD")

#Place Bid
#id_bid_1=place_limit_order("BUY","BTC_USD","100.0","0.1")
				
#Cancel an Order
#cancel_order(id_bid_1)

#Check If Order Is Live
#is_order_live(id_bid_1)

