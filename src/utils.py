# https://github.com/NUSTM/SLC-Conjunction/blob/master/trandict.txt
# https://zh.m.wikipedia.org/zh-tw/%E9%80%A3%E8%A9%9E

class DepRelation():
    # https://universaldependencies.org/u/dep/ 
    CONJ = 'conj' 
    CC = 'cc' # coordinating conjunction 
    CONJUNCTIONS = [CONJ, CC]
    NEG = 'neg'

class POS():
    # https://ckip.iis.sinica.edu.tw/CKIP/paper/Sinica%20Corpus%20user%20manual.pdf
    Na = 'Na'
    Nb = 'Nb'
    Nc = 'Nc'
    Nd = 'Nd'
    D = 'D'
    Da = 'Da'
    Dfa='Dfa'
    Dfb='Dfb'
    Di='Di'
    Dk='Dk'
    Nouns = [Na, Nb, Nc, Nd]
    Adverbs =[D, Da, Dfa, Dfb, Di, Dk]
       
BOUNDDIST = 5
CONJDIST = 2
transition_list = ['但','但是',
'只是','不過','美中不足',
'可惜','遺憾','雖然','其他','只怪', '然而', '卻','反而']

