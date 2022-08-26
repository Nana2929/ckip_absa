
import requests
import networkx as nx
import streamlit as st

output = [(2, 1, 'nsubj'), (0, 2, 'root'), (2, 3, 'dep'), (2, 4, 'punct')]
indexx = [(0, 'root'), (1, '你'), (2, '好'), (3, '嗎'), (4, ',')] 

g=nx.DiGraph()
for ind in indexx:
    g.add_node(ind[0], label=f'<{ind[1]}>')
for tok_ind in output:
    g.add_edge(tok_ind[0], tok_ind[1], label=f' {tok_ind[2]} ')
p=nx.drawing.nx_pydot.to_pydot(g)
print('its Graph nodes:', g.nodes)
print('its Graph edges:', g.edges)
print('what is its p:', p)

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
with open("chyiin_test.png", 'wb') as f:
    f.write(r.content)


def myDepTree():
    pos = [(0, 'root root'), (1, '清蒸鱸魚 Na'), (2, ', COMMACATEGORY'), (3, '不 D'), (4, '太 Dfa'), (5, '新鮮 VH'), (6, '， COMMACATEGORY'), (7, '有點 Dfa'), (8, '糟 VH'), (9, '。 PERIODCATEGORY'), (10, '老闆娘人 Na'), (11, '很 Dfa'), (12, '好 VH'), (13, '。 PERIODCATEGORY')]
    depparse = [('5 - 新鮮 VH', '1 - 清蒸鱸魚 Na', 'amod'), ('5 - 新鮮 VH', '2 - , COMMACATEGORY', 'punct'), ('5 - 新鮮 VH', '3 - 不 D', 'neg'), ('5 - 新鮮 VH', '4 - 太 Dfa', 'advmod'), ('0 - root root', '5 - 新鮮 VH', 'root'), ('5 - 新鮮 VH', '6 - ， COMMACATEGORY', 'punct'), ('8 - 糟 VH', '7 - 有點 Dfa', 'advmod'), ('5 - 新鮮 VH', '8 - 糟 VH', 'dep'), ('5 - 新鮮 VH', '9 - 。 PERIODCATEGORY', 'punct'), ('12 - 好 VH', '10 - 老闆娘人 Na', 'nn'), ('12 - 好 VH', '11 - 很 Dfa', 'advmod'), ('5 - 新鮮 VH', '12 - 好 VH', 'conj'), ('5 - 新鮮 VH', '13 - 。 PERIODCATEGORY', 'punct')]
    
    G =nx.DiGraph()
    for x in pos:
        node_id, p = x
        token, thispos = p.rsplit(' ', 1) # split by 1 WHITESPACE only
        G.add_node(node_id, label = f'<{token}>', pos = thispos)
    for (u, v, deprel) in depparse:
        u, v = u.split(' - '), v.split(' - ')
        uid = u[0] = int(u[0])
        vid = v[0] = int(v[0])
        G.add_edge(uid, vid, label = deprel)
    print('my Graph nodes:', G.nodes)
    print('my Graph edges:', G.edges)
    p = nx.drawing.nx_pydot.to_pydot(G)
    print('what is my p:', p)
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
    with open("mine_test.png", 'wb') as f:
        f.write(r.content)
    
myDepTree()

# print(p)
# strict digraph  {
# 0 [label=<root>];
# 1 [label=<你>]; 
# 2 [label=<好>];
# 3 [label=<嗎>];
# 4 [label=<？>];
# 0 -> 2  [label=" root "];
# 2 -> 1  [label=" nsubj "];
# 2 -> 3  [label=" dep "];
# 2 -> 4  [label=" punct "];
# }


