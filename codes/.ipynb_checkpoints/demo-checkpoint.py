import pandas as pd
import numpy as np
import networkx as nx
from collections import defaultdict
from copy import deepcopy
import sys, os
import logging
import argparse
import json 


root_path = '/share/home/nana2929/'
DepTree_path = '/share/home/nana2929/repo/src/'
for x in [root_path, DepTree_path]:
    if x not in sys.path:
        sys.path.append(x)


import chyiin_ch_parser
from chyiin_ch_parser import dependency_parser
from DepTree import DepTree


'''initializing'''
def init_parser():
    # avoid loading model every time with Flask
    # https://stackoverflow.com/questions/61049310/how-to-avoid-reloading-ml-model-every-time-when-i-call-python-script
    port = args.port 
    ch_parser = dependency_parser.chinese_parser(port)
    return ch_parser


argparser = argparse.ArgumentParser(prog='') 
argparser.add_argument('--port', '-p', default = 2022, type = int, required = False, 
                       help = 'At which port you wish to run your dependency parser\'s associated ckip tagger')
argparser.add_argument('--input', '-i', default = f'{root_path}/test_sent.txt', type = str, required = False, 
                      help = 'The file to read the test sentence from')
argparser.add_argument('--output', '-o', default = f'./testdata/', type = str, required = False, 
                      help = 'The file to output the results to')

args = argparser.parse_args()
logging.basicConfig(level=logging.INFO)
# this line takes too long 
logging.info('Inititalizing Dependency Parser...') 
ch_parser = init_parser()
logging.info('Successfully initialized.') 


'''ws & parsing & post-processing'''
test_sent_path = args.input
with open(test_sent_path) as f:
    lines = f.readlines()
test_sent = lines[0].strip('\n').strip()
logging.info("Parsing...")
ws, pos, deptree = ch_parser.output(test_sent)  
# make dir 
output_path = args.output
os.makedirs(output_path, exist_ok=True)

r = {'sentence': test_sent,
     'word_seg': ws,
     'pos': pos, 
     'dependency_parse': deptree}
tree = DepTree(r, outdir = output_path)
logging.info("Pairing aspects with opinions...")

'''output (to revise later)'''
# get outputs under f'{root_path}/testdata/'
logging.info(f"Sentence: {test_sent}")
D, ws = tree.predict()
logging.info("Prediction:")
for k, v in D.items():
    logging.info(f'{k}: {v}')
logging.info(f"Span-marking: {ws}")  
tree.to_image(verbose = False)
logging.info(f"Output success. Check the results under {output_path}")
