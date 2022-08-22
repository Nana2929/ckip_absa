import pandas as pd
import numpy as np
import networkx as nx
from collections import defaultdict
from copy import deepcopy
import sys, os
import logging
import argparse
import json 
from flask import Flask, jsonify, abort, request, make_response, render_template, url_for
from flask_cors import CORS

'''paths of modules'''
# root_path = '/share/home/qwe9887476/'
root_path = '/share/home/nana2929/'
# DepTree_path = '/share/home/qwe9887476/absa/ckip_absa/src/'
DepTree_path = '/share/home/nana2929/repo/src/'

for x in [root_path, DepTree_path]:
    if x not in sys.path:
        sys.path.append(x)
import chyiin_ch_parser
from chyiin_ch_parser import dependency_parser
from DepTree import DepTree


'''initializing'''
def init_parser(port, device_id):
    ch_parser = dependency_parser.chinese_parser(port, device_id)
    return ch_parser


'''main function'''
def text_process(test_sent):
    
    test_sent = test_sent.replace(' ', '').replace('\n','').replace('\r','')
    '''ws & parsing & post-processing'''
    # check input
    print(test_sent) 
    print("Parsing...")
    
    ws, pos, deptree = ch_parser.output(test_sent) 
    os.makedirs(outputdir, exist_ok=True)

    r = {'sentence': test_sent,
        'word_seg': ws,
        'pos': pos, 
        'dependency_parse': deptree}
    tree = DepTree(r, outdir = outputdir, logfile = outlog)

    print("Pairing aspects with opinions...")
    D, ws = tree.predict()

    print("Prediction:")
    pred = ''
    for k, v in D.items():
        # print(f'{k}: {v}')
        pair = ''
        for t in v:
            # print(t[0], t[1])
            if t[1] == 'positive':
                polar = '正面'
            elif t[1] == 'negative':
                polar = '負面'
            else:
                polar = '中性'
            pair = pair + f'{t[0]}({polar})' + '、'
        pair = pair[:-1] # remove last '、'
        print(f'{k}:{pair}')
        pred = pred + f'{k}' + '：' + f'{pair}' + '\n'

    print(f"Span-marking: {ws}") 
    tree.to_image(verbose = False)
    # open the written logfile 
    # read the current input's log
    with open(outlog, 'r') as fh:
        logstring = fh.readlines() 
        logstring = ''.join(logstring) #.lstrip('\00')

    print(f"Output success. Check the results under {outputdir}")
    tree.clean_file()
    return ws, pred, logstring

'''read image of dependnecy tree'''
def return_img_stream(img_local_path):
    import base64
    img_stream = ''

    with open(img_local_path, 'rb') as img_f:
        img_stream = img_f.read()
        img_stream = base64.b64encode(img_stream)
        # print(img_stream.decode('ascii'))

    return img_stream.decode('ascii')

'''Flask'''
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)
@app.route('/', methods=['POST','GET'])
def index():
    sent = ""
    # url_pre = args.url_pre
    # return render_template("index.html", sent = sent, url_pre = url_pre)
    return render_template("index.html", sent = sent)

@app.route("/forward/", methods=['POST','GET'])
def move_forward():
    # Moving forward code
    user_text = request.values['text']
    # url_pre = args.url_pre
    cnt = 0 
    if request.method=='POST':
        
        print('Did user request to show the process?', request.form.get("show_progress"))
        process_output, result_output, logmsg = text_process(user_text)
        if request.form.get("show_progress"):
            sepline = '='*30+'\n'
            process_output = logmsg + sepline + process_output
            img_path = './testdata/dep_tree.png'
            img_output = return_img_stream(img_path)

        results = [user_text, process_output, result_output]
        return render_template('index.html', 
                               sent = results[0], 
                               process = results[1], 
                               result = results[2],
                               img_stream = img_output)
                            #    url_pre = url_pre)
    # return render_template('index.html', url_pre = url_pre)
    return render_template('index.html')


if __name__ == '__main__':
    
    # do NOT modify this variable
    URLLINK = 'https://ckip.iis.sinica.edu.tw/service/restaurant-absa'
    
    
    argparser = argparse.ArgumentParser(prog='') 
    argparser.add_argument('--tagger_port', '-tgp', default = 2022, type = int, required = False, 
                        help = 'At which port you wish to run your dependency parser\'s associated module (ckip tagger)')
    # argparser.add_argument("--url_pre",'-u', default= URLLINK, type=str, help = 'The url you wish to run your Flask App on')
    argparser.add_argument("--device_id",'-d', default= 2, type=int, help = 'Gpu device id to run the dep parser on')
    global args
    global outputdir 
    global outlog 
    
    outputdir = './testdata'
    args = argparser.parse_args()
    outlog = f'{outputdir}/ch_absa_usr_log.log'    
    # disable Flask logging
    # flasklog = logging.getLogger('werkzeug')
    # flasklog.setLevel(logging.ERROR)
    print('Inititalizing Dependency Parser...') 
    ch_parser = init_parser(args.tagger_port, args.device_id)
    print('Successfully initialized.')
    # if already written, clean the file 
    app.run(host='0.0.0.0', port=7778, debug = False, threaded=True)  # running on port 7777