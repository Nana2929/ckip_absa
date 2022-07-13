import pandas as pd
import numpy as np
import networkx as nx
from collections import defaultdict
from copy import deepcopy
import sys, os
import logging
import argparse
import json
from flask import  Flask, jsonify, abort, request, make_response, render_template, url_for
from flask_cors import CORS

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

'''path of source codes'''
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
# argparser.add_argument('--input', '-i', default = f'{root_path}/test_sent.txt', type = str, required = False,
#                       help = 'The file to read the test sentence from')
argparser.add_argument('--output', '-o', default = f'./testdata/', type = str, required = False,
                    help = 'The file to output the results to')

argparser.add_argument("-url_pre",default='https://ckip.iis.sinica.edu.tw/service/restaurant-absa',type=str)


args = argparser.parse_args()
logging.basicConfig(level=logging.INFO)
# this line takes too long
logging.info('Inititalizing Dependency Parser...')
# logging.info('Bypassing parser.')
ch_parser = init_parser()
logging.info('Successfully initialized.')


def text_process (test_sent):

    test_sent = test_sent.replace(' ', '').replace('\n','').replace('\r','')

    '''ws & parsing & post-processing'''

    # check input
    print(test_sent)

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
    pred = ''
    for k, v in D.items():
        logging.info(f'{k}: {v}')
        pred = pred + f'{k}: {v}' + '\n'
    logging.info(f"Span-marking: {ws}")
    tree.to_image(verbose = False)
    logging.info(f"Output success. Check the results under {output_path}")

    return ws, pred


'''Flask'''
@app.route('/', methods=['POST','GET'])
def index():
    global url_pre
    sent=""
    return render_template("index.html",sent=sent,url_pre=url_pre)

@app.route("/forward/", methods=['POST','GET'])
def move_forward():
    # Moving forward code
    global url_pre
    text_message = request.values['text']

    if request.method=='POST':
        process_output, result_output = text_process(text_message)
        # process_output, result_output = 0,0
        result = [text_message, process_output, result_output]
        return render_template('index.html', sent = result[0], process = result[1], result = result[2], url_pre=url_pre)

    return render_template('index.html', url_pre=url_pre)


url_pre = ""
if __name__ == '__main__':
    app.debug = True
    app.run(port=7777, host='0.0.0.0')