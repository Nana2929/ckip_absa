import numpy as np
import rpyc
import json
import torch
from torch.utils.data import TensorDataset, DataLoader, SequentialSampler
from transformers import BertTokenizer
import matplotlib.pyplot as plt
from opencc import OpenCC
from tqdm import tqdm
import pandas as pd
import sys
import re

depp_path = '/share/home/nana2929/chyiin_ch_parser'
if depp_path not in sys.path:
    sys.path.append(depp_path)
root = depp_path
from BERT_encoder import BERT_Encoder1
from BERT_punct import BERT_Punct
from mst import fast_parse

s2t = OpenCC('s2tw') # 簡體 --> 繁體
t2s = OpenCC('t2s') # 繁體 --> 簡體

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# n_gpu = torch.cuda.device_count()
torch.cuda.set_device(2) # gpu setting
# print(f'cuda now:{torch.cuda.current_device()}')


def batch_io(input_path, output_path):
    df = pd.read_csv(input_path)
    textcol = 'text' if 'text' in df else 'sentence' # 'text', 'texts', 'sentence'
    lines = df[textcol].tolist()
    wses, poses, parses = [], [], [] 
    for lineid, line in enumerate(tqdm(lines)):
        ws, pos, depparse = ch_parser.output(line)
        wses.append(ws)
        poses.append(pos)
        parses.append(depparse)

    df = df.assign(word_seg = wses, pos = poses, dependency_parse = parses)
    df.to_pickle(output_path)


    
class chinese_parser():

    def __init__(self, port):
        
        self.conn = rpyc.classic.connect('localhost', port=port)
        self.conn.execute('from ckiptagger import data_utils, construct_dictionary, WS, POS, NER')
        self.conn.execute('ws = WS("./data")')
        self.conn.execute('pos = POS("./data")')
        self.ids_to_labels = {0: 'root', 1: 'nn', 2: 'conj', 3: 'cc', 4: 'nsubj', 5: 'dep', 6: 'punct', 7: 'lobj', 8: 'loc', 9: 'comod', 10: 'asp', 11: 'rcmod', 12: 'etc', 13: 'dobj', 14: 'cpm', 15: 'nummod', 16: 'clf', 17: 'assmod', 18: 'assm', 19: 'amod', 20: 'top', 21: 'attr', 22: 'advmod', 23: 'tmod', 24: 'neg', 25: 'prep', 26: 'pobj', 27: 'cop', 28: 'dvpmod', 29: 'dvpm', 30: 'lccomp', 31: 'plmod', 32: 'det', 33: 'pass', 34: 'ordmod', 35: 'pccomp', 36: 'range', 37: 'ccomp', 38: 'xsubj', 39: 'mmod', 40: 'prnmod', 41: 'rcomp', 42: 'vmod', 43: 'prtmod', 44: 'ba', 45: 'nsubjpass'}
        self.tokenizer = BertTokenizer.from_pretrained("bert-base-chinese")
        # recommend_dictionary = dictionary1, # words in this dictionary are encouraged
        # coerce_dictionary = dictionary2,   # words in this dictionary are forced
        # word_to_weight = {
        #     "土地公": 1,
        #     "土地婆": 1,
        #     "公有": 2,
        #     "": 1,
        #     "來亂的": "啦",
        #     "緯來體育台": 1,
        # }
        # d = construct_dictionary(word_to_weight)
        # word_sentence_list = ws(input, recommend_dictionary = d)
        
        
        #####
        from transformers import logging
        logging.set_verbosity_error()
        #####
        
        self.model = BERT_Encoder1(hidden_size=1024, pretrained="hfl/chinese-roberta-wwm-ext-large").cuda()
        self.model.load_state_dict(torch.load(f'{root}/demo_model/bert_encoder.pt')) 

        self.punct_model = BERT_Punct(loaded_model=f'{root}/demo_model/bert_encoder.pt', hidden_size=1024, num_labels=len(self.ids_to_labels)).cuda()
        self.punct_model.load_state_dict(torch.load(f'{root}/demo_model/bert_punct_encoder.pt')) 
    
    def tokenize_and_preserve_labels(self, subsent):
        tokenizer = self.tokenizer
        tokenized_sentence, labels_idx, seq = [], [], [0]
        n, idx = 0, 0
        for word in subsent:

            tokenized_word = tokenizer.tokenize(word)
            n_subwords = len(tokenized_word)
            n = n + n_subwords
            tokenized_sentence.extend(tokenized_word)
            labels_idx.extend([idx] * n_subwords)
            seq.append(n)
            idx = idx + 1

        return tokenized_sentence, torch.tensor(labels_idx), seq[:-1]
    @staticmethod
    def get_recommended_seg():
        # import os
        # print(os.getcwd())
        aspect_path = '../src/lexicons/aspect_lexicon-4.0.csv'
        df = pd.read_csv(aspect_path)
        const = 10; d = {}
        for rowid, r in df.iterrows():
            w, src = r['Word'], r['source']
            d[w] = const
            # if src.endswith('WS'): # 楊桃美食網WS
            #     d[w] = 15
            if src.startswith('self'):  # self-defined
                d[w] = 20
            # else: # 楊桃美食網, 松園, ehownet and CookBook
            #     d[w] = 20
        return d
    
    
    def output(self, input_text):

        input_text = s2t.convert(input_text)
        d = chinese_parser.get_recommended_seg()
        input_sent = self.conn.eval(f'ws(["{input_text}"], coerce_dictionary = construct_dictionary({d}))')[0]
        pos_sent = ['root'] + list(self.conn.eval(f'pos([{input_sent}])')[0])
        # print(f'input_sent:{input_sent}')
        input_sentence = []
        for i in input_sent:
            input_sentence.append(t2s.convert(i))
        input = ['root'] + list(input_sentence)
        parse_input = ['root'] + list(input_sent)
        sentence_index = []
        for i in range(len(parse_input)):
            sentence_index.append((i, f'{parse_input[i]} {pos_sent[i]}'))

        input_token, input_idx, input_seqs = self.tokenize_and_preserve_labels(input)

        input_ids = torch.tensor([self.tokenizer.convert_tokens_to_ids(txt) for txt in input_token])
        attention_masks = torch.tensor([float(i != 0.0) for i in input_ids])

        input_data = TensorDataset(input_ids.unsqueeze(0), attention_masks.unsqueeze(0), input_idx.unsqueeze(0))
        input_sampler = SequentialSampler(input_data)
        input_dataloader = DataLoader(input_data, sampler=input_sampler, batch_size=1, shuffle=False)

        torch.cuda.set_device(2)
        self.model.eval()

        punct_predict, predict = [], []
        for step, batch in enumerate(input_dataloader):            
            batch = tuple(t.to(device) for t in batch)
            b_input_ids, b_input_mask, b_idx = batch
            with torch.no_grad():
                # print(f'cuda now:{torch.cuda.current_device()}')
                output = self.model(input_ids=b_input_ids, token_type_ids=None, attention_mask=b_input_mask)
                punct_output = self.punct_model(input_ids=b_input_ids, token_type_ids=None, attention_mask=b_input_mask)

            # label_indices = np.argmax(output[1].to('cpu').numpy(), axis=2)
            # label_indices = fast_parse(torch.transpose(output[1], 1, 2)[0].fill_diagonal_(-100000).to('cpu').numpy(), one_root=True)
            punct_label_indices = np.argmax(punct_output[1].to('cpu').numpy(), axis=2)
            seq_output = torch.index_select(output[1][0], 0, torch.tensor(input_seqs).cuda())
            seq_output = torch.index_select(seq_output, 1, torch.tensor(input_seqs).cuda())
            label_indices = fast_parse(torch.transpose(seq_output, 0, 1).fill_diagonal_(-100000).to('cpu').numpy(), one_root=True)
          
            final_predict = []
            for label_idx in label_indices:
                final_predict.append(int(b_idx[0][input_seqs[label_idx]].cpu()))
            final_predict[0] = -1

            punct_new_labels = []
            for label_idx in punct_label_indices[0]:
                punct_new_labels.append(self.ids_to_labels[label_idx])
            punct_predict.append(punct_new_labels)

        punct_final_predict = []
        for i in input_seqs:
            punct_final_predict.append(punct_predict[0][i])

        parse = []
        for i in range(len(input[1:])):
            parse.append((f'{final_predict[1:][i]} - {parse_input[final_predict[1:][i]]} {pos_sent[final_predict[1:][i]]}', f'{i+1} - {parse_input[i+1]} {pos_sent[i+1]}', punct_final_predict[1:][i]))
  
        return input_sent, sentence_index, parse
    
    

if __name__ == '__main__':

    import argparse
    argparser = argparse.ArgumentParser(prog='Chinese Dependency Parser') 
    argparser.add_argument('--port', '-p', default = 2022, type = int, required = False, 
                           help = 'At which port you wish to run your dependent ckip tagger')
    argparser.add_argument('--input_file', '-i', default = '../data/0705-dep-testdata.csv', type = str, 
                           required = False, help = 'input file (csv with a `text` column)')
    argparser.add_argument('--output_name', '-o', type = str, 
                           required = False, help = 'output file name (pickle)')
    args = argparser.parse_args()
    port = args.port
    infile = args.input_file
    outfile = args.output_name
    
    filesuffix = re.search('(.\w+)$', infile).group() # get file suffix 
    if not outfile: 
        outfile = infile.rstrip(filesuffix) + '_parsed.pkl'
    print(' === ckip dependency parser === ')
    print(f'input file : {infile}')
    print(f'output file: {outfile}')
    global ch_parser
    ch_parser = chinese_parser(port)
    print('parser initialized.')
    batch_io(input_path = infile, 
       output_path = outfile) 
    
#     class preprocess():

#         def __init__(self):
#             self.parser = chinese_parser(args.)

#         def forward(self, sentence): # filename
              
#             segment_output, token_index, dependency_tree = self.parser.output(sentence)
#             print(segment_output)
#             print(token_index)
#             print(dependency_tree) 
    
    
#     test_sent = '這個面很不好吃。'
#     segment_output, token_index, dependency_tree = ch_parser.output(test_sent)
#     print(segment_output)
#     print(token_index)
#     print(dependency_tree)
    