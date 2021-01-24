#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

@author: Tu Bui @surrey.ac.uk
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import sys
import requests
import json
from collections import defaultdict
import pandas as pd
from datetime import datetime
from .interval import Interval
from .utils import plot_historic_price, get_yahoo_fin, pretty_json
from .product import Product


class DegiroAPI(object):
    def __init__(self, username, password, verbose=True):
        self.verbose = verbose
        self.sess, self.sessid = self.login(username, password)
        self.account_id = self.get_account_id()
        self.client_id = self.get_client_id()
        self.data = None
    
    def __del__(self):
        try:
            url = 'https://trader.degiro.nl/trading/secure/logout'
            url += f';jsessionid={self.sessid}'
            payload = {'intAccount': self.account_id,
                       'sessionId': self.sessid}
            r = self.sess.get(url, params=payload)
        except:
            pass
        
    def _info(self, *args):
        if self.verbose:
            for arg in args:
                print(arg)
    
    def login(self, username, password):
        url = 'https://trader.degiro.nl/login/secure/login'
        sess = requests.Session()
        payload = {'username': username,
                   'password': password,
                   'isPassCodeReset': False,
                   'isRedirectToMobile': False}
        header={'content-type': 'application/json'}
        r = sess.post(url, headers=header, data=json.dumps(payload))
        self._check_status(r, 'Login')

        # Get session id
        sessid = r.headers['Set-Cookie'].split(';')[0].split('=')[1]
        self._info('\tSession id: {}'.format(sessid))
        return sess, sessid
    
    def get_account_id(self):
        url = 'https://trader.degiro.nl/pa/secure/client'
        payload = {'sessionId': self.sessid}

        r = self.sess.get(url, params=payload)
        self._check_status(r, 'Get account id')

        data = r.json()
        acc_id = data['data']['intAccount']
        self._info(f'\tAccount id: {acc_id}')
        return acc_id
    
    def get_client_id(self):
        url = 'https://trader.degiro.nl/login/secure/config'
        cookie = {
            'JSESSIONID': self.sessid
        }
        r = self.sess.get(url, cookies=cookie)
        self._check_status(r, 'Get client id')
        client_id = r.json()['data']['clientId']
        self._info(f'\tClient id: {client_id}')
        return client_id
    
    def get_data(self):
        """
        get loads of data including:
        'orders', 'historicalOrders', 'transactions', 'portfolio', 'totalPortfolio', 'alerts', 'cashFunds'
        """
        url = 'https://trader.degiro.nl/trading/secure/v5/update/'
        url += f'{self.account_id};jsessionid={self.sessid}'
        payload = {'portfolio': 0,
                   'totalPortfolio': 0,
                   'orders': 0,
                   'historicalOrders': 0,
                   'transactions': 0,
                   'alerts': 0,
                   'cashFunds': 0,
                   'intAccount': self.account_id,
                   'sessionId': self.sessid}

        r = self.sess.get(url, params=payload)
        self._check_status(r, 'Get data')
        data = r.json()
        return data
    
    def _check_status(self, r, msg=''):
        if r.status_code != 200:
            raise AssertionError(f'Error! Request fails with status code {r.status_code}')
            sys.exit(1)
        self._info('\t' + msg, f'\t\tStatus code: {r.status_code}')

    def get_product_info(self, product_id_list):
        """collect product information given list of product ids"""
        url = 'https://trader.degiro.nl/product_search/secure/v5/products/info'
        params = {'intAccount': self.account_id,
                  'sessionId': self.sessid}
        header={'content-type': 'application/json'}
        r = self.sess.post(url, headers=header, params=params, data=json.dumps(product_id_list))
        self._check_status(r, 'Getting product info')
        data = r.json()
        return data
    
    def get_cash_funds(self):
        """get available cashfunds"""
        if self.data is None:
            self.get_data()       
        cashFunds = dict()
        for cf in self.data['cashFunds']['value']:
            entry = dict()
            for y in cf['value']:
                # Useful if the currency code is the key to the dict
                if y['name'] == 'currencyCode':
                    key = y['value']
                    continue
                entry[y['name']] = y['value']
            if entry['value'] != 0:
                cashFunds[key] = entry
        return cashFunds
    
    def get_portfolio(self):
        if self.data is None:
            self.data = self.get_data()       
        portfolio = []
        for row in self.data['portfolio']['value']:
            entry = dict()
            for y in row['value']:
                k = y['name']
                v = None
                if 'value' in y:
                    v = y['value']
                entry[k] = v
            # Also historic equities are returned, let's omit them
            if entry['size'] != 0:
                portfolio.append(entry)

        ## Restructure portfolio and add extra data
        portf_n = defaultdict(dict)
        # Restructuring
        for r in portfolio:
            pos_type = r['positionType']  # PRODUCT
            pid = r['id'] # Product ID
            del(r['positionType'])
            del(r['id'])
            portf_n[pos_type][pid]= r

        # Adding product info
        prod_id = list(portf_n['PRODUCT'].keys())
        prod_info = self.get_product_info(prod_id)
        
        for k,v in prod_info['data'].items():
            del(v['id'])
            # Some bonds tend to have a non-unit size
            portf_n['PRODUCT'][k]['size'] *= v['contractSize']
            portf_n['PRODUCT'][k].update(v)

        return portf_n
    
    def get_portfolio_summary(self):
        pf = self.get_portfolio()
        cf = self.get_cash_funds()
        tot = 0
        df = pd.DataFrame(index=range(len(pf['PRODUCT'])), columns=['Product', 'Symbol', 'Qty', 'Price',
                                                                    'Curr.', 'Value', 'BEP', 'alloc(%)'])
        for eq in pf['PRODUCT'].values():
            tot += eq['value']
        for i, eq in enumerate(pf['PRODUCT'].values()):
            df.iloc[i] = [eq['name'], eq['symbol'], eq['size'], eq['price'], eq['currency'], eq['value'],
                         eq['breakEvenPrice'],eq['value']/tot*100]

        self._info('Equity summary:', df)
        self._info('CashFund summary:')
        for key in cf.keys():
            self._info(f'{key:<5}: {cf[key]["value"]}')
        total = df['Value'].sum() + cf[list(cf.keys())[0]]['value']
        self._info(f'Total: {total}')
        return df, cf
    
    def search_product(self, search_text):
        url = 'https://trader.degiro.nl/product_search/secure/v5/products/lookup'
        payload = {
                    'searchText': search_text,
                    'limit': 1,
                    'offset': 0,
                    'intAccount': self.account_id,
                    'sessionId': self.sessid
                  }
        r = self.sess.get(url, params=payload)
        self._check_status(r, f'Searching {search_text}')
        return r.json()
    
    def query_price(self, search_text, interval='month', outdir='./'):
        assert hasattr(Interval, interval), f'Error! Interval {interval} not recognized. Supported values are {Interval()}'
        interval = getattr(Interval, interval)[0]
        
        # search product for vwdId
        prod = self.search_product(search_text)
        prod = Product(prod)  # convert to our own Product format

        # query price
        price = self._get_historic_price(prod._vwdId, interval)
        x = [data[0] for data in price['series'][1]['data']]
        y = [data[1] for data in price['series'][1]['data']]
        
        first = datetime.strptime(price['start'], '%Y-%m-%dT%H:%M:%S')
        last = datetime.strptime(price['end'], '%Y-%m-%dT%H:%M:%S')
        print(prod)
        plot_historic_price(x, y, (first, last), prod, outdir)
        get_yahoo_fin(prod, outdir)
        
    
    def _get_historic_price(self, vwdid, interval):
        url = 'https://charting.vwdservices.com/hchart/v1/deGiro/data.js'
        payload = {
                    'requestid': 1,
                    'period': interval,
                    'series': ['issueid:' + vwdid, 'price:issueid:' + vwdid],
                    'userToken': self.client_id
                  }
        r = self.sess.get(url, params=payload)
        self._check_status(r, 'Querying historic price')
        return r.json()