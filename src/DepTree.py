import networkx as nx
from collections import defaultdict
from copy import deepcopy
import json 
import requests



class DepTree:
    
    def __init__(self, row, outdir):
        '''a dictionary or a pandas row'''
        self.row = row
        self.pos = row['pos']
        self.ws = row['word_seg']
        self.depparse = row['dependency_parse']
        self.dG, self.undG = self.build_graph()
        self.outdir = outdir
        
    @classmethod
    def detect(cls, sentpos, food_lexicon, senti_lexicon):
        foods = food_lexicon
        sentis = senti_lexicon
        foodidx, foodtok = [], []
        sentiidx, sentitok = [], []
        for x in sentpos:
            id, tokenpos = x
            token, pos = tokenpos.split()
            if token in foods:
                foodidx.append(id)
                foodtok.append(token)
            if token in sentis:
                sentiidx.append(id)
                sentitok.append(token)
            food = {'idx': foodidx, 'token':foodtok}
            senti = {'idx': sentiidx, 'token':sentitok}
        # res = True if (foodidx and sentiidx) else False
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
    
    def get_all_sp(self, aspd, opd):
        filename = f'{self.outdir}/dep_tree_sp.json'
        undG = self.undG
        spD = defaultdict(list)
        for asp, asptok in zip(aspd['idx'], aspd['token']):
            for opn, opntok in zip(opd['idx'], opd['token']):
                sp = nx.shortest_path(undG, asp, opn)
                # Supported options: ‘dijkstra’ (default), ‘bellman-ford’.
                directed_path, viewpath = self.process_raw_sp(sp)
                #  (consider no tree direction)
                spD[f'{asptok}_{asp},{opntok}_{opn}'] = {'directed_path': directed_path,
                                                              'tree path': viewpath}
        with open(filename, 'w') as f:
            json.dump(spD, f, indent= 4, ensure_ascii = False)
        return spD
    
    
    def to_image(self):
        filename = f'{self.outdir}/dep_tree.png'
        p = nx.drawing.nx_pydot.to_pydot(self.dG)
        r = requests.post(
            "https://quickchart.io/graphviz",
            headers={"Content-Type": "application/json"},
            json={
                "graph": 
                f'{p}',                 # --> change here
                "layout": "dot",
                "format": "png"
            }
        )
        with open(filename, 'wb') as f:
            f.write(r.content)
        
    
            
    