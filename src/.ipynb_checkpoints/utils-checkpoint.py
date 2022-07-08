class DepRelation():
    # https://universaldependencies.org/u/dep/ 
    CONJ = 'conj' 
    CC = 'cc' # coordinating conjunction 
    NEG = 'neg'


transition_list = ['但','但是',
'只是','不過','美中不足',
'可惜','遺憾','雖然','其他','只怪', '然而', '卻','反而']
# https://github.com/NUSTM/SLC-Conjunction/blob/master/trandict.txt
# https://zh.m.wikipedia.org/zh-tw/%E9%80%A3%E8%A9%9E

    
    
#     def expand_by_conj(self, foods, sentis):
        
#         '''
#         during lexicon_detect() 
#         1. if found a token in lexicon linking with 'conj' to a non-detected token, 
#             activate the token
#         2. the token is appended (expanding the detected returns)
#         ''' 
# #                 for out in outs:
# #                     if G.get_edge_data(*out)['label'] in ['cc' or 'advmod']:
# #                         conj_tok = out[-1]
#         self.get_conjunction()
#         conj_edges = self.conjunctions
#         for id in foods['idx']:
#             if id in conj_edges:
#                 partner_id = conj_edges[id]
#                 foods['idx'].append(partner_id)
#                 foods['token'].append(self.node2tok(partner_id))
        
#         return foods, sentis