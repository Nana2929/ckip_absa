import networkx as nx
from collections import defaultdict
from copy import deepcopy
import json 
import requests
import os
from IPython.display import Image, display
import logging
import pandas as pd

class DepTree:
    
    
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
        # lexdir = '../repo/src/lexicon'
        os.makedirs(self.outdir, exist_ok =True)
        
        logging.info('attrs:    \t .pos, .ws, .depparse, .dG, .undG')
        logging.info('functions:\t detect(), get_all_sp(), to_image()')
    
    @classmethod
    def get_lexicon(cls, lextype, directory = None):
        directory ='../repo/src/lexicon' if directory is None else directory
        availables = ['aspect', 'opinion']
        if lextype not in availables:
            print(f'Action abort. Only options in {availables} are supported.')
            return 
        filepath = os.path.join(directory, lextype+'_lexicon.csv')
        df = pd.read_csv(filepath)
        logging.info(f'finished loading {lextype} lexicon.')
        return df 
        
    def detect(self, method = 'lexicon'):
        if method == 'lexicon':
            return self.lexicon_detect()
        return self.dep_detect()
    
    
    def dep_detect(self):
        # get tree 
        
        pass

    
    def lexicon_detect(self, food_lexicon = None, senti_lexicon = None):
        if not food_lexicon:
            aspect_lexicon = DepTree.get_lexicon('aspect')
            
        if not senti_lexicon:
            opn_lexicon = DepTree.get_lexicon('opinion')
        
        foodidx, foodtok = [], []
        sentiidx, sentitok, sentpol = [], [], []
        sentpos = self.pos
        aspectlist = aspect_lexicon['Word'].to_list() 
        
        rating = lambda x: 'positive' if x >= 6 else ('neutral' if 6 > x >= 4  else 'negative')
        for x in sentpos: 
            id, tokenpos = x
            token, pos = tokenpos.split()

            if token in aspectlist:
                foodidx.append(id)
                foodtok.append(token)
            
            for rid, r in opn_lexicon.iterrows():
                if token == r['Word']:
                    score = r['Valence_Mean']
                    sentiidx.append(id)
                    sentitok.append(token)
                    sentpol.append(rating(score))
        
        food = {'idx': foodidx, 'token': foodtok}
        senti = {'idx': sentiidx, 'token': sentitok, 'polarity': sentpol}
        
        # res = True if (foodidx and sentiidx) else False
        logging.info(f'aspects:\t{food}')
        logging.info(f'opinions:\t{senti}')
        return food, senti  
    
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
        for i in range(1, len(sp)):
            edge = u, v = sp[i-1], sp[i]
            # G.nodes(data="time")
            ustring = f'{u} - {dG.nodes[u]["label"]} {dG.nodes[u]["pos"]}'
            vstring = f'{v} - {dG.nodes[v]["label"]} {dG.nodes[v]["pos"]}'
            viewpath.append(f'{ustring} --> {vstring}')
        return dirpath, viewpath
    
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
                directed_path, viewpath = self.process_raw_sp(sp)
                currpathdict = {'diPath': directed_path,
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
    
    def to_image(self):
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
        display(Image(filename=filename))
        
    
            
    