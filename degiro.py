#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

@author: Tu Bui @surrey.ac.uk
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import os
import sys
from api import DegiroAPI
import pandas as pd


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('There must be at least 2 input arguments')
        print('Input argument format:\n (i) credential_file command ...\n (ii) username password command...')
        sys.exit(0)

    arg1 = sys.argv[1]
    if os.path.exists(arg1):  # credential as a file
        print(f'Reading credentials at {arg1}')
        un, pw = open(arg1, 'r').read().strip().split('\n')
        args = sys.argv[2:]
    else:  # credential as input arguments
        print('Coundnt detect file credential, assuming username and password are entered as input arguments')
        un, pw = sys.argv[1:3]
        args = sys.argv[3:]

    os.makedirs('logs', exist_ok=True)
    print(un, pw)
    de = DegiroAPI(un, pw)
    cmd = args[0]
    if cmd == 'portfolio':
        df, cf = de.get_portfolio_summary()
        df.to_csv('logs/portfolio.csv', index=False)
