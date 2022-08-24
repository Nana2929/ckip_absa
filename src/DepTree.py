from collections import defaultdict
from copy import deepcopy
import json 
import requests
import os
from IPython.display import Image, display
import logging
import pandas as pd
from utils import DepRelation, POS
import networkx as nx
from networkx.algorithms.traversal.depth_first_search import dfs_tree
import re, sys

class DepTree:
    
    def __init__(self, row, 
                 logfile='./DepTree_out/DepTree.log', 
                 outdir = './DepTree_out'):
        
        '''
        Params:
            row: a dictionary or a pandas row
            logfile: the file name that logging messages go into
            outdir: directory that output image/data go to 
        '''

        self.row = row
        self.pos = row['pos']
        self.ws = row['word_seg']
        self.depparse = row['dependency_parse']
        self.dG, self.undG = self.build_graph()
        self.outdir = outdir
        os.makedirs(self.outdir, exist_ok =True)
         
        self.init_logger(logfile)
        self.logger.info('======= Dep Tree =======')
    
    def build_graph(self):
        '''
        Params:
        (None) using self.pos, self.depparse
        ========
        Return:
            nxGraph: dependency graph(directed/undirected)
        '''
        G = nx.DiGraph()
        self.nodes = []
        self.periods = []
        
        for x in self.pos:
            id, tokenpos = x
            token, pos = tokenpos.rsplit(' ', 1) # split by 1 WHITESPACE only
            # RULE 5: DO NOT pair Crossing-boundary 
            if pos == POS.EXCLAMATIONCATEGORY or pos == POS.PERIODCATEGORY:
                self.periods.append(id)
            
            # print(f'token: {token}, pos: {pos}')
            G.add_node(id, label = token, pos = pos)
            self.nodes.append((id, token, pos))
            
        for dep in self.depparse:
            u, v, deprel = dep 
            u, v = u.split(' - '), v.split(' - ')
            uid = u[0] = int(u[0])
            vid = v[0] = int(v[0])
            G.add_edge(uid, vid, label = deprel)
        # nx.draw(G)
        copyG = deepcopy(G)
        copyG = copyG.to_undirected()
        dG, undG = G, copyG
        return dG, undG
    
    def init_logger(self, logfile):
        '''
        Params:
            str: path to the log file 
        =======
        Return: 
            (None)initializing module-specific logger  
        '''
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # initialize handlers 
        stream_handler = logging.StreamHandler()
        file_handler = logging.FileHandler(logfile, 'w') # 'w+' or 'w' to overwrite file 

        # formatters
        stream_formatter = logging.Formatter('%(name)s|%(message)s')
        file_formatter = logging.Formatter('%(message)s') # cleaner 
        stream_handler.setFormatter(stream_formatter)
        file_handler.setFormatter(file_formatter)
        
        # add handlers 
        self.logger.addHandler(file_handler)
        self.logger.addHandler(stream_handler)
        
    
    def clean_logging(self):
        '''
        Cleaning logger handlers, 
        s.t. it cleans the previous logging messages to avoid logging messages for different user inputs to be mixed 
        '''
        self.logger.handlers = []
        print(f'{len(self.logger.handlers)} remaining handlers.')
    
    

    def _get_lexicon(self, lextype, directory = None):
        filedir = os.path.join(os.path.dirname(__file__), './lexicons')
        directory = filedir if directory is None else directory
        availables = ['aspect', 'opinion']
        if lextype not in availables:
            self.logger.warning(f'Action abort. Only options in {availables} are supported.')
            return 
        filepath = os.path.join(directory, lextype+'_lexicon.csv')
        df = pd.read_csv(filepath)
        self.logger.info(f'finished loading {lextype} lexicon.')
        return df 
    
    
    def node2tok(self, node):
        '''
        Params:
            int: node: the node id recorded in {NetworkX Object}.nodes
        =======
        Return: 
            str: the label (token tag) of the node
        '''
        return self.dG.nodes[node]['label']
    
    def node2pos(self, node):
        '''
        Params:
            int: node: the node id recorded in {NetworkX Object}.nodes
        =======
        Return: 
            str: the pos tag of the node
        '''
        return self.dG.nodes[node]["pos"]
    
    
    def predict(self):
        '''
        MAIN FUNCTION 
        '''
        spD = self.get_pairing()
        procD = self.neg_detect(spD) 
        D = self.conj_detect(procD) # removing duplicates
        tokenD, span_marking = self.markspan(D)
        return tokenD, span_marking
    
    
    def markspan(self, D):
        '''
        Return: 
            defaultdict: tokenD: 
                key: str: aspect_label, 
                value: list of tuples: (str: opinion, str: polarity)
            str: spanned_ws: tagged user-input sequence 
        '''
        tokenD = defaultdict(list)
        pos = self.pos
        # list of token id
        aspspan = set(D.keys())
        opnspan = set()
        for asp, inventory in D.items():
            asplabel = self.node2tok(asp)
            for entry in inventory:
                opn, oppol = entry 
                opnspan.update(opn)   #['不', '好吃']
                opnlabel = ''.join(self.node2tok(x) for x in opn)
                tokenD[asplabel].append((opnlabel, oppol))
        self.logger.debug('marking: [] for aspect; <> for opinion')
        spanned_ws = ''
        for id in range(self.dG.number_of_nodes()):
            token = pos[id][-1].rsplit(' ', 1)[0]
            if id in aspspan:
                token = f'[{token}]'
            if id in opnspan:
                token = f'<{token}>'
            if token != 'root':
                spanned_ws += token 
        
        return tokenD, spanned_ws
            

    def neg_detect(self, spD):
        '''
        if a detected opinion is negated,
            reverse its polarity
        '''
        dG = self.dG
        for opnkey in spD.keys(): 
            for j in range(len(spD[opnkey])):
                pol = spD[opnkey][j]['polarity']
                asp, opn = spD[opnkey][j]['pair']
                print(f'!neg_detect opn: {opn}')
                outs = dG.out_edges(opn)
                for opn, v in outs:
                    if dG[opn][v]['label'] == DepRelation.NEG:
                        self.logger.info(
                        f'[Rule 3] Detect negation on {self.node2tok(opn)}; polarity is reversed.')
                        neg_token = v 
                        spD[opnkey][j]['pair'] = asp, (neg_token, opn)
                        spD[opnkey][j]['polarity'] = 'positive' if pol == 'negative' else 'negative'
        return spD

    def get_conjunctions(self):
        '''
        get CLOSE conjunction
        
        '''
        
        if getattr(self, 'conjunctions', None) is not None:
            return self.conjunctions
        conj_edges = {}
        G = self.dG
        edges = G.edges
        for u, v in edges:
            depr = G[u][v]['label']
            # A和B
            # if abs(u - v) <= CONJDIST:
            # if an conjunction edge (u,v) is present 
            # and u, v's linguistic distance <= 1 
            # if depr == DepRelation.CONJ:
            #     conj_edges[u] = v; conj_edges[v] = u
            if depr == DepRelation.CC: #（和）
                conj_edges[u] = v-1; conj_edges[v-1] = u
            elif depr == DepRelation.CONJ: # 蛋糕、麵包
                conj_edges[u] = v; conj_edges[v] = u
        self.conjunctions = conj_edges
        return self.conjunctions

    def conj_detect(self, spD):
        D = defaultdict(list)
        conjunctions = self.get_conjunctions()
        for opnkey, sps in spD.items(): 
            for sp in sps:
                asp, opn = sp['pair'] # 
                
                oppol = sp['polarity']
                # dG.nodes[sp[-1]]['label']
                # opn = self.node2tok(opn) if not isinstance(opn, list) else ''.join(self.node2tok(x) for x in opn)
                if asp in conjunctions:
                    partner = conjunctions[asp]
                    partnertok = self.node2tok(partner)
                    self.logger.info(
                        f'[Rule 2] Detect conjunction between existing aspect {self.node2tok(asp)} and node {partnertok}; new aspect {partnertok} is added.')
                    if (opn, oppol) not in D[partner]:
                        D[partner].append((opn, oppol))
                if (opn, oppol) not in D[asp]:
                    D[asp].append((opn, oppol))
        return D
    
    
    def detect(self, food_lexicon = None, senti_lexicon = None):
        '''
        Params: 
            food_lexicon := str: filepath to aspect lexicon (.csv)
            senti_lexicon := str: filepath to opinion lexicon (.csv) 
        =======
        Return None
        =======
        Generate
            self.aspects  := list of dict: the detected inventory of foods (with node id)
            self.opinions := list of dict: the detected inventory of opinions (with node id and polarity)
        '''
        if not food_lexicon:
            aspect_lexicon = self._get_lexicon('aspect')
            
        if not senti_lexicon:
            opn_lexicon = self._get_lexicon('opinion')
        
        sentpos = self.pos
        asplexicon = aspect_lexicon['Word'].to_list() 
        asplexicon = set(asplexicon)
        opnlexicon = {r['Word']:r['Valence_Mean'] for rid, r in opn_lexicon.iterrows()}
        rating = lambda x: 'positive' if x >= 6 else ('neutral' if 6 > x >= 4  else 'negative')
        
        if hasattr(DepTree, 'aspects') and hasattr(DepTree, 'opinions'):
            self.logger.info('Aspect and opinion inventories are already detected.')
            return 
        
        self.aspects = []
        self.opinions = []
        for x in sentpos: 
            id, tokenpos = x
            token, pos = tokenpos.rsplit(' ', 1)
            if token in opnlexicon:
                if not self.node2pos(id) in POS.Adverbs:
                    score = opnlexicon[token]
                    sentinfo = {'id': id, 'token': token, 'polarity': rating(score)}
                    self.opinions.append(sentinfo)
            elif token in asplexicon:
                foodinfo = {'id':id, 'token': token}
                self.aspects.append(foodinfo)
        self.logger.info(f'[lexicon-based] detected aspects: {self.aspects}')
        self.logger.info(f'[lexicon-based] detected opinions: {self.opinions}')
    
    
    def process_raw_sp(self, sp):
        '''
        helper function of .get_all_sp()
        Params:
            sp:= a list of node id: nx.shortest_path(undG, asp, opn) 
                given undirected tree, asp, opn as the node index
                find the shortest path between the 2 nodes (usually the only path)     
        =======
        Return:
            the processed shortest path information (collecting the information of node)  
            including: 
                diPath, 
                treePath, 
                aspect:opinion(s) pairing
        '''
        dG, undG = self.dG, self.undG
        dirpath = []
        for i in range(1, len(sp)):
            u, v = sp[i-1], sp[i]
            # ustring = f'{u} - {G.nodes[u]["word"]} {G.nodes[u]["pos"]}'
            if dG.has_edge(u, v): 
                deprel = dG.get_edge_data(u, v)['label']
                dirpath.append((u, v, deprel))
            else: 
                deprel = dG.get_edge_data(v, u)['label']
                dirpath.append((v, u, deprel))

        viewpath = []
        aspect = sp[0]
        opinion = sp[-1]
        for i in range(1, len(sp)):
            edge = u, v = sp[i-1], sp[i]
            ustring = f'{u} - {self.node2tok(u)} {self.node2pos(u)}'
            vstring = f'{v} - {self.node2tok(v)} {self.node2pos(v)}'
            viewpath.append(f'{ustring} --> {vstring}')
        
        return dirpath, viewpath, [aspect, [opinion]]
    
    def get_pairing(self):
        '''
        Params:
            None
        =========
        Return:
            dictionary of k:v = opinion: currpathdict (to the nearest aspect)
            key examples: {'好':.. ,'好吃':... ,'酸甜':...}
            value: currpathdict: a dict of 
                pair (opinion: matched aspect)
                diPath: directed Path (path, but follows directed edge direction)
                treePath: tree Path (path, edges are transformed to be tail-head connected)
                polarity: the polarity recorded in the aspect lexicon 
        '''
        self.detect()
        spD = defaultdict(list)
        
        for opn_triplet in self.opinions:
            opnid, opntok, oppol = opn_triplet['id'], opn_triplet['token'], opn_triplet['polarity']
            opnkey = f'{opntok}_{opnid}'
            
            # if within the opinion's subtree, the opn directly (directionally) link to a Noun
            opn_subT = dfs_tree(self.dG, opnid)
            neighbors = opn_subT.neighbors(opnid)
            
            # if within the opinion's neighbors
            # a `neighbor` POS is N && its node id is PRIOR to opnid
            # then add this `neighbor` as aspect into self.aspect 
            for neighborid in neighbors:
                
                if self.node2tok(neighborid).strip() != '':
                    if (self.node2pos(neighborid) in POS.Nouns or self.dG[opnid][neighborid]['label'] == DepRelation.NSUBJ) and neighborid <= opnid:
                        self.aspects.append({'id':neighborid, 'token':self.node2tok(neighborid)})
                        self.logger.info(
                            f'[Rule 1] Detect NOUN neighbor in subtree; \
                            new aspect {self.node2tok(neighborid)} is added.')
                        directed_path, viewpath, pair = self.process_raw_sp([neighborid, opnid])
                        spD[opnkey].append({'pair': pair, 'diPath': directed_path,
                                'treePath': viewpath, 'polarity': oppol})
            
            # otherwise 
            mindist = float('inf') 
            for asp_tuple in self.aspects:
                aspid, asptok = asp_tuple['id'], asp_tuple['token']
                ## linguistic distance 4 以內才加入
                # if abs(aspid-opnid) > BOUNDDIST:
                #     continue
                sp = nx.shortest_path(self.undG, aspid, opnid)
                directed_path, viewpath, pair = self.process_raw_sp(sp)
                currpathdict = {'pair': pair, 'diPath': directed_path,
                            'treePath': viewpath, 'polarity': oppol}
                currdist = len(directed_path)
                
                if currdist < mindist:
                    if self.isCrossed(aspid = aspid, opnid = opnid):
                        continue 
                    spD[opnkey] = [currpathdict]
                mindist = min(mindist, currdist)
        return spD
    
    
    def isCrossed(self, aspid, opnid):
        for period_id in self.periods:
            if aspid < period_id < opnid:
                self.logger.info(f'[Rule 5] Detected crossing boundary pair {self.node2tok(aspid)} and {self.node2tok(opnid)}, ignore the pair.')
                return True
        return False
                       
    
    def to_image(self, verbose = True):
        p = nx.drawing.nx_pydot.to_pydot(self.dG)
        r = requests.post(
            "https://quickchart.io/graphviz",
            headers={"Content-Type": "application/json"},
            json={
                "graph": 
                f'{p}',                 
                "layout": "dot",
                "format": "png"
            }
        )
        filename = f'{self.outdir}/dep_tree.png'
        with open(filename, 'wb') as f:
            f.write(r.content)
        if verbose:
            display(Image(filename=filename))
        
    
            
    