from collections import defaultdict
from copy import deepcopy
import json 
import requests
import os
from IPython.display import Image, display
import logging
import pandas as pd
from utils import DepRelation, POS
from utils import BOUNDDIST, CONJDIST
import networkx as nx
from networkx.algorithms.traversal.depth_first_search import dfs_tree
import re

class DepTree:
    
    def build_graph(self):
        G = nx.DiGraph()
        self.nodes = []
        for x in self.pos:
            id, tokenpos = x
            token, pos = tokenpos.rsplit(' ', 1) # split by 1 WHITESPACE only
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
    
    def __init__(self, row, outdir = './DepTree_out'):
        '''a dictionary or a pandas row'''
        logging.basicConfig(level = logging.INFO)
        logging.info('== DepTree ==')
        self.row = row
        self.pos = row['pos']
        self.ws = row['word_seg']
        self.depparse = row['dependency_parse']
        self.dG, self.undG = self.build_graph()
        self.outdir = outdir
        os.makedirs(self.outdir, exist_ok =True)
        
        logging.debug('attrs:    \t .pos, .ws, .depparse, .dG, .undG, .aspects, .opinions')
        logging.debug('functions:\t predict(), to_image()')
    
    @classmethod
    def get_lexicon(cls, lextype, directory = None):
        filedir = os.path.join(os.path.dirname(__file__), './lexicons')
        directory = filedir if directory is None else directory
        availables = ['aspect', 'opinion']
        if lextype not in availables:
            logging.warning(f'Action abort. Only options in {availables} are supported.')
            return 
        filepath = os.path.join(directory, lextype+'_lexicon.csv')
        df = pd.read_csv(filepath)
        logging.debug(f'finished loading {lextype} lexicon.')
        return df 
    
    
    def node2tok(self, node):
        '''
        Params:
            node: the node id recorded in {NetworkX Object}.nodes
        =======
        Return: 
            the label (token tag) of the node
        '''
        return self.dG.nodes[node]['label']
    
    def node2pos(self, node):
        return self.dG.nodes[node]["pos"]
    
    
    def predict(self):
        spD = self.get_pairing()
        procD = self.neg_detect(spD) 
        D = self.conj_detect(procD)
        tokenD, span_marking = self.markspan(D)
        
        return tokenD, span_marking
    
    def markspan(self, D):
        '''
        
        Params:
        
        
        =========
        Return:
        
        
        
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
        logging.debug('marking: [] for aspect; <> for opinion')
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
                outs = dG.out_edges(opn)
                for opn, v in outs:
                    if dG[opn][v]['label'] == DepRelation.NEG:
                        logging.info(
                        f'[Rule 3] Detect negation on {self.node2tok(opn)}; polarity is reversed.')
                        neg_token = v 
                        spD[opnkey][j]['pair'] = asp, [neg_token, opn]
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
        self.conjunctions = conj_edges
        return self.conjunctions

    def conj_detect(self, spD):
        D = defaultdict(list)
        conjunctions = self.get_conjunctions()
        for opnkey, sps in spD.items(): 
            for sp in sps:
                asp, opn = sp['pair']
                oppol = sp['polarity']
                # dG.nodes[sp[-1]]['label']
                # opn = self.node2tok(opn) if not isinstance(opn, list) else ''.join(self.node2tok(x) for x in opn)
                if asp in conjunctions:
                    partner = conjunctions[asp]
                    partnertok = self.node2tok(partner)
                    logging.info(
                        f'[Rule 2] Detect conjunction beween existing aspect {self.node2tok(asp)} and node {partnertok}; new aspect {partnertok} is added.')
                    D[partner].append((opn, oppol))
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
            aspect_lexicon = DepTree.get_lexicon('aspect')
            
        if not senti_lexicon:
            opn_lexicon = DepTree.get_lexicon('opinion')
        
        sentpos = self.pos
        aspectlist = aspect_lexicon['Word'].to_list() 
        aspectlist = set(aspectlist)
        opnlexicon = {r['Word']:r['Valence_Mean'] for rid, r in opn_lexicon.iterrows()}
        rating = lambda x: 'positive' if x >= 6 else ('neutral' if 6 > x >= 4  else 'negative')
        
        if hasattr(DepTree, 'aspects') and hasattr(DepTree, 'opinions'):
            logging.info('Aspect and opinion inventories are already detected.')
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
                elif token in aspectlist:
                    foodinfo = {'id':id, 'token': token}
                    self.aspects.append(foodinfo)
        logging.info(f'[lexicon-based] detected aspects: {self.aspects}')
        logging.info(f'[lexicon-based] detected opinions: {self.opinions}')
    
    
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
        return dirpath, viewpath, (aspect, [opinion])
            
    
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
            
            
            # if within the opinion's neighbors (1-step away nodes)
            # a `neighbor` POS is N && its node id is PRIOR to opnid
            # then add this `neighbor` as aspect into self.aspect 
            for neighborid in neighbors:
                # if self.node2pos(neighborid) in POS.Nouns and neighborid <= opnid:
                if self.node2tok(neighborid).strip() != '':
                    if self.dG[opnid][neighborid]['label'] == DepRelation.NSUBJ and neighborid <= opnid:
                        self.aspects.append({'id':neighborid, 'token':self.node2tok(neighborid)})
                        logging.info(
                            f'[Rule 1] Detect NOUN neighbor in subtree; new aspect {self.node2tok(neighborid)} is added.')
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
                # Supported options: ‘dijkstra’ (default), ‘bellman-ford’.
                directed_path, viewpath, pair = self.process_raw_sp(sp)
                currpathdict = {'pair': pair, 'diPath': directed_path,
                            'treePath': viewpath, 'polarity': oppol}
                currdist = len(directed_path)
                if currdist < mindist:
                    spD[opnkey] = [currpathdict]
                elif currdist == mindist: 
                    spD[opnkey].append(currpathdict)
                mindist = min(mindist, currdist)
        
        filename = f'{self.outdir}/dep_tree_sp.json'
        with open(filename, 'w') as f:
            json.dump(spD, f, indent= 4, 
                      ensure_ascii = False)
        return spD
    
    
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
        
    
            
    