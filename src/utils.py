
class DepRelation():
    # https://universaldependencies.org/u/dep/ 
    CONJ = 'conj' 
    CC = 'cc' # coordinating conjunction 
    CONJUNCTIONs = [CONJ, CC]
    NEG = 'neg'
    NSUBJ = 'nsubj'
    NN = 'nn'
    NSUBJPASS = 'nsubjpass'
    POBJ = 'pobj'
    DOBJ = 'dobj'
    LOBJ = 'lobj'
    OBJs = [POBJ, LOBJ, DOBJ]
    
class POS():
    # https://ckip.iis.sinica.edu.tw/CKIP/paper/Sinica%20Corpus%20user%20manual.pdf
    Na = 'Na'
    Nb = 'Nb'
    Nc = 'Nc'
    Nd = 'Nd'
    D = 'D'
    Da = 'Da'
    Dfa ='Dfa'
    Dfb ='Dfb'
    Di ='Di'
    Dk ='Dk'
    PERIODCATEGORY = 'PERIODCATEGORY'# ['.', '。']
    COMMACATEGORY = 'COMMACATEGORY' #[',', '，']
    EXCLAMATIONCATEGORY = 'EXCLAMATIONCATEGORY' #['!','！']
    Nouns = [Na, Nb, Nc, Nd]
    Adverbs =[D, Da, Dfa, Dfb, Di, Dk]
       
# BOUNDDIST = 5
# CONJDIST = 2
transition_list = ['但','但是',
                    '只是','不過','美中不足',
                    '可惜','遺憾','雖然','其他','只怪', '然而', '卻','反而']


'''
Chyiin Dependency Parser Relations
self.ids_to_labels = 
{0: 'root', 1: 'nn', 2: 'conj', 3: 'cc', 4: 'nsubj', 5: 'dep', 6: 'punct', 7: 'lobj', 8: 'loc', 9: 'comod', 10: 'asp', 11: 'rcmod', 12: 'etc', 13: 'dobj', 14: 'cpm', 15: 'nummod', 16: 'clf', 17: 'assmod', 18: 'assm', 19: 'amod', 20: 'top', 21: 'attr', 22: 'advmod', 23: 'tmod', 24: 'neg', 25: 'prep', 26: 'pobj', 27: 'cop', 28: 'dvpmod', 29: 'dvpm', 30: 'lccomp', 31: 'plmod', 32: 'det', 33: 'pass', 34: 'ordmod', 35: 'pccomp', 36: 'range', 37: 'ccomp', 38: 'xsubj', 39: 'mmod', 40: 'prnmod', 41: 'rcomp', 42: 'vmod', 43: 'prtmod', 44: 'ba', 45: 'nsubjpass'}
'''
