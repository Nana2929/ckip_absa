import networkx as nx
from collections import defaultdict
from copy import deepcopy
import json 
import requests
import os
from IPython.display import Image, display
import logging
import pandas as pd
from utils import DepRelation





class DepTree:
    
    def build_graph(self):
        G = nx.DiGraph()
        for x in self.pos:
            id, tokenpos = x
            token, pos = tokenpos.split()
            G.add_node(id, label = token, pos = pos)
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
        
        logging.info('attrs:    \t .pos, .ws, .depparse, .dG, .undG')
        logging.info('functions:\t detect(), get_all_sp(), to_image()')
    
    @classmethod
    def get_lexicon(cls, lextype, directory = None):
        filedir = os.path.join(os.path.dirname(__file__), './lexicons')
        directory = filedir if directory is None else directory
        availables = ['aspect', 'opinion']
        if lextype not in availables:
            print(f'Action abort. Only options in {availables} are supported.')
            return 
        filepath = os.path.join(directory, lextype+'_lexicon.csv')
        df = pd.read_csv(filepath)
        logging.info(f'finished loading {lextype} lexicon.')
        return df 
        
    def node2tok(self, node):
        res = self.dG.nodes[node]['label']
        return res
    
    
    def get_conjunctions(self):
        if getattr(self, 'conjunctions', None) is not None:
            return self.conjunctions
        conj_edges = {}
        G = self.dG
        edges = G.edges
        for u, v in edges:
            depr = G[u][v]['label']
            # if an conjunction edge is present 
            if depr == DepRelation.CONJ:
                conj_edges[u] = v; conj_edges[v] = u
        self.conjunctions = conj_edges
        return self.conjunctions

    def neg_detect(self, spD):
        '''
        if a detected opinion is negated,
            reverse its polarity
        '''
        dG = self.dG
        for opnkey in spD.keys(): 
            for j in range(len(spD[opnkey])):
                asp, opn = spD[opnkey][j]['pair']
                outs = dG.out_edges(opn)
                for opn, v in outs:
                    if dG[opn][v]['label'] == DepRelation.NEG:
                        neg_token = v 
                        spD[opnkey][j]['pair'] = asp, [neg_token, opn]
                        break
            
        return spD
                    
    def conj_detect(self, spD):
        D = defaultdict(list)
        conjunctions = self.get_conjunctions()
        for opnkey, sps in spD.items(): 
            for sp in sps:
                asp, opn = sp['pair']
                # dG.nodes[sp[-1]]['label']
                opn = self.node2tok(opn) if not isinstance(opn, list) else ''.join(self.node2tok(x) for x in opn)
                if asp in conjunctions:
                    partner = conjunctions[asp]
                    partner = self.node2tok(partner)
                    D[partner].append(opn)
                asp = self.node2tok(asp)
                D[asp].append(opn)
        return D
    
    def predict(self):
        spD = self.get_all_sp()
        procD = self.neg_detect(spD) 
        D = self.conj_detect(procD)
        return D
    
    
    def detect(self, food_lexicon = None, senti_lexicon = None):
        '''
        1. detecting aspect and opinion appearing in the lexicons
        2. lexicon-based 
        '''
        if not food_lexicon:
            aspect_lexicon = DepTree.get_lexicon('aspect')
            
        if not senti_lexicon:
            opn_lexicon = DepTree.get_lexicon('opinion')
        
        foodidx, foodtok = [], []
        sentiidx, sentitok, sentpol = [], [], []
        sentpos = self.pos
        aspectlist = aspect_lexicon['Word'].to_list() 
        aspectlist = set(aspectlist)
        opnlexicon = {r['Word']:r['Valence_Mean'] for rid, r in opn_lexicon.iterrows()}
        rating = lambda x: 'positive' if x >= 6 else ('neutral' if 6 > x >= 4  else 'negative')
        for x in sentpos: 
            id, tokenpos = x
            token, pos = tokenpos.split()

            if token in aspectlist:
                foodidx.append(id)
                foodtok.append(token)
            
            if token in opnlexicon:
                score = opnlexicon[token]
                sentiidx.append(id)
                sentitok.append(token)
                sentpol.append(rating(score))
        
        food = {'idx': foodidx, 'token': foodtok}
        senti = {'idx': sentiidx, 'token': sentitok, 'polarity': sentpol}
        
        # res = True if (foodidx and sentiidx) else False
        logging.info(f'aspects:\t{food}')
        logging.info(f'opinions:\t{senti}')
        
        return food, senti  
    
    
    def process_raw_sp(self, sp):
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
            ustring = f'{u} - {dG.nodes[u]["label"]} {dG.nodes[u]["pos"]}'
            vstring = f'{v} - {dG.nodes[v]["label"]} {dG.nodes[v]["pos"]}'
            viewpath.append(f'{ustring} --> {vstring}')
        return dirpath, viewpath, (aspect, opinion)
            
    
    def get_all_sp(self):
        '''string-match by lexicons'''
        aspd, opd = self.detect()
        
        undG = self.undG
        spD = defaultdict(list)
        
        for opn, opntok in zip(opd['idx'], opd['token']):
            opnkey = f'{opntok}_{opn}'
            mindist = float('inf')
            for asp, asptok in zip(aspd['idx'], aspd['token']):
                sp = nx.shortest_path(undG, asp, opn)
                # Supported options: ‘dijkstra’ (default), ‘bellman-ford’.
                directed_path, viewpath, pair = self.process_raw_sp(sp)
                currpathdict = {'pair': pair, 'diPath': directed_path,
                            'treePath': viewpath}
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
        
    
            
    