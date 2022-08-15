'''
TESTER for NESTED LOGGING 
Author: Nana (Ching Wen Yang)
Date: 2022.8.15 
Purpose: 
    - test the nested module logging mechanism 
    - mimic the calling structure of demo.py without involving Flask 
Result: logging into file can work as expected in the below code
'''

import random, sys, os
import pandas as pd
root_path = '/share/home/nana2929/'
DepTree_path = '/share/home/nana2929/repo/src/'
for x in [root_path, DepTree_path]:
    if x not in sys.path:
        sys.path.append(x)
import chyiin_ch_parser
from chyiin_ch_parser import dependency_parser
from DepTree import DepTree
import logging


def display():
    outfile='/share/home/nana2929/repo/data/0810-general-data/0810_review_cleaned_parsed.pkl'
    df = pd.read_pickle(outfile)
    rindex = random.randint(0, len(df)-1)
    logging.info(f'random index: {rindex}')

    
    print(f'Review index: {rindex}')
    row = df.iloc[rindex]
    print(row['reviewText'])
    print(row['storeName'])
    # print(row['pos'])
    tree = DepTree(row, outdir = './25.5-test-dep')
    pairs, spans = tree.predict()
    for k, v in pairs.items():
        print(k, v)
    print(spans)
    print(tree.aspects) 
    print(tree.opinions)
    

if __name__ == '__main__':
    fp = './my-absa-log.log'
    logging.basicConfig(filename=fp,
                    filemode='w',
                    level=logging.INFO,
                    format='%(asctime)s.[%(levelname)s] %(message)s',
                    datefmt='%H:%M:%S')
    display() # logging can direct to file!
    print('=====================')
    with open(fp, 'r') as fh:
        logstring = fh.readlines() 
        logstring = ''.join(logstring)
    print(logstring)
    
    

