#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
product class initialized from object returned by either search_product() or get_product_info()
@author: Tu Bui @surrey.ac.uk
"""

class Product(object):
    def __init__(self, prod):
        if 'products' in prod:  # search_product object
            prod = prod['products'][0]
        elif 'data' in prod:  # get_product_info object
            key = list(prod['data'].keys())[0]
            prod = prod['data'][key]
        else:
            raise ValueError('Error! Object not recognized. ' 
                'Only object returned from search_product() or get_product_info() supported.')
        self._name = prod['name']
        self._id = prod['id']
        self._symbol = prod['symbol']
        self._currency = prod['currency']
        self._closeprice = prod['closePrice']
        try:
            int(prod['vwdId'])
            self._vwdId = prod['vwdId']
        except:
            self._vwdId = prod['vwdIdSecondary']
        self._closedate = prod['closePriceDate']

    def __repr__(self):
        msg = f'Product: {self._name}\n'
        msg += f'\tid: {self._id}\n'
        msg += f'\tsymbol: {self._symbol}\n'
        msg += f'\tclose price: {self._closeprice} {self._currency}\n'
        msg += f'\tclose date: {self._closedate}\n'
        msg += f'\tvwdId: {self._vwdId}\n'
        return msg