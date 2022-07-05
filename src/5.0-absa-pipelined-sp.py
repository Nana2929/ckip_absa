import pandas as pd
import numpy as np
import networkx as nx
from collections import defaultdict
from copy import deepcopy
import sys, os
import logging
import argparse
import json 

# path variables 
root_path = '/share/home/nana2929'
code_path = f'{root_path}/codes'
foodlexpath = f'{root_path}/data/food_lexicon.csv'
oplexpath = f'{root_path}/data/simplified_opinions.json'


external_paths = [root_path, code_path]
for p in external_paths:
    if p not in sys.path:
        sys.path.append(p)
        
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
argparser.add_argument('--output', '-o', default = f'{root_path}/testdata/', type = str, required = False, 
                      help = 'The file to output the results to')

args = argparser.parse_args()
logging.basicConfig(level=logging.INFO)
# this line takes too long 
logging.info('Inititalizing Dependency Parser...') 
ch_parser = init_parser()
logging.info('Successfully initialized.') 


'''ws & parsing'''
test_sent_path = args.input
with open(test_sent_path) as f:
    lines = f.readlines()
test_sent = lines[0].strip('\n').strip()
ws, pos, deptree = ch_parser.output(test_sent)


'''loading lexicons'''
logging.info('Loading aspect and opinion lexicons...')
food_lexicon = pd.read_csv(foodlexpath)
food_lexicon = food_lexicon['name'].to_list() # a list 
with open(oplexpath, 'r') as f:
    opinion_lexicon = json.load(f) # a dict 
logging.info('Sucessfully loaded.')   

'''processing shortest path'''
logging.info("Parsing and finding shortest path...")
# make dir 
output_path = args.output
os.makedirs(output_path, exist_ok=True)

r = {'sentence': test_sent,
     'word_seg': ws,
     'pos': pos, 
     'dependency_parse': deptree}
tree = DepTree(r, outdir = output_path)
aspectdict, opiniondict = DepTree.detect(pos, food_lexicon = food_lexicon, 
                                         senti_lexicon = opinion_lexicon)
'''output (to revise later)'''
# get outputs under f'{root_path}/testdata/'
# output sp dictionary 
spD = tree.get_all_sp(aspd = aspectdict, 
                       opd = opiniondict)
# output tree 
tree.to_image()
logging.info(f"Output success. Check the results under {output_path}")







