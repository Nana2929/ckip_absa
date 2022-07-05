# -*- coding: UTF-8 -*-

from flask import  Flask, jsonify, abort, request, make_response,render_template
from ckiptagger import WS, POS, NER
from flask import jsonify
from flask_cors import CORS
import pandas as pd
import json
import argparse
def isnumber(aString):
    try:
        float(aString)
        return True
    except:
        return False

adv=["很","極","挺","太","怪","好","最","頂","更加","非常","格外","極其","越加","相當","稍","稍稍","稍微","略","略微","較","比較"]

app = Flask(__name__)
CORS(app)

ws = WS("ckip_data/data")



def text_senti(class_list,sentence_list):

    print(sentence_list)
    osentence_list=sentence_list
    sentence_list=sentence_list+"，"
    read2 =pd.read_csv("cvaw4_new.csv",index_col=("Valence_Mean"))
    senti = read2["Word"].tolist()
    if "，"in sentence_list:
        sentence_list = sentence_list.split("，")
    if ","in sentence_list:
        sentence_list = sentence_list.split(",")
    word_s = ws(sentence_list,
            sentence_segmentation=True,
            segment_delimiter_set={'?', '？', '!', '！', '。', ',',
                                    '，', ';', ':', '、'})

    GetResult=[]
    temp=[]
    sentice=[]
    obj=[]
    check_list=[]
    sent=[]
    f_sent=[]
    for word in word_s:
        check_adj=False
        if word in check_list:
            pass
        else:
            check_list.append(word)
           # print(word)
            for s in range(len(word)):
                if word[s] in adv:
                    temp.append(word[s])
                    sent.append(word[s])
                elif word[s] in class_list:
                  #  print(word[s],"(object)")
                    temp.append(word[s]+"(object)")
                    sent.append(word[s]+"(object)")
                elif  word[s-1]=="不" and  word[s] in senti:
                    a=read2[read2.Word==word[s]].index.tolist()
                    score=['%.2f'%(float(i)-5) for i in a]
                    score=float("".join(score))
                   # print(word[s],score)
                    temp.append(score)
                    sent.append(word[s]+"(Adj.)")
                    check_adj=True
                elif word[s] in senti :
                    a=read2[read2.Word==word[s]].index.tolist()
                    score=['%.2f'%(float(i)) for i in a]
                    score="".join(score)
                    temp.append(score)
                    sent.append(word[s]+"(Adj.)")
                    check_adj=True
                elif "難" in word[s] and word[s] not in senti:
                    score=3.0
                    temp.append(score)
                    sent.append(word[s]+"(Adj.)")
                    check_adj=True
                elif "好喝" in word[s] or "好用" in word[s]:
                    score=7.0
                    temp.append(score)
                    sent.append(word[s]+"(Adj.)")
                    check_adj=True
                else:
                    temp.append(word[s])
                    sent.append(word[s])
                    #print(word[s])
        print([t for t in temp])

        if check_adj:
            sent.append("\n")
            for t in range(len(temp)):
                if "(object)" in str(temp[t]):
                    obj.append(t)
                elif isnumber(temp[t]):
                    sentice.append(t)
                else:
                    pass

            for o in obj:
                min=100000
                for s in sentice:

                    if abs(o-s)<=min:
                        min=abs(o-s)
                        temp_s=s
                GetResult.append(str(o)+"/"+str(temp_s))
            for r in GetResult:
                print("R:",r)
                o=r.split("/")[0]
                s=r.split("/")[1]
                print(o,s)
                o1=temp[int(o)]
                o1=o1.split("(")
                s1=temp[int(s)]

                if float(s1)<5:
                    f_sent.append(o1[0]+":"+"負面"+" ")
                    print(o1[0],"負面")
                else:
                    print(o1[0],"正面")
                    f_sent.append(o1[0]+":"+"正面"+" ")

            GetResult=[]
            temp=[]
            sentice=[]
            obj=[]

    new_sent="".join(sent)
    sentence2list="".join(osentence_list)
    fin_sent=" ".join(f_sent)
    final=[]
    final.append(sentence2list)
    final.append(new_sent)
    final.append(fin_sent)
    print(final)
    return final


@app.route('/', methods=['POST','GET'])
def index():
    global url_pre
    sent=""
    return render_template("index.html",sent=sent,url_pre=url_pre)
@app.route("/forward/", methods=['POST','GET'])
def move_forward():
    #Moving forward code
    global url_pre
    text_message=request.values['text']
    classify=request.values['classify']

    if classify == 'food':
        read1 = pd.read_csv("food_list3.csv")
        class_list = read1['food_list'].tolist()
        result=text_senti(class_list,text_message)
    elif classify == 'clothes':
        read1 = pd.read_csv("clothes.csv")
        class_list = read1['clothes'].tolist()
        result=text_senti(class_list,text_message)
    elif classify == 'cosmetics':
        read1 = pd.read_csv("cosmetics.csv")
        class_list = read1['cosmetics'].tolist()
        result=text_senti(class_list,text_message)
    elif classify == '3c':
        read1 = pd.read_csv("3c.csv")
        class_list = read1['3c'].tolist()
        result=text_senti(class_list,text_message)
    elif classify == "default":
        read1 = pd.read_csv("default.csv")
        class_list = read1['default'].tolist()
        result=text_senti(class_list,text_message)



    if request.method=='POST':
        return render_template('index.html',sent=result[0],process=result[1],result=result[2],url_pre=url_pre);

    return render_template('index.html',url_pre=url_pre)


url_pre=""
if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument("-port",default=9210,type=int)
    parser.add_argument("-url_pre",default='https://ckip.iis.sinica.edu.tw/service/comment-analysis',type=str)
   # parser.add_argument("-url_pre",default='',type=str)
    args=parser.parse_args()
    url_pre=args.url_pre
    app.run(host='0.0.0.0',port=args.port,debug=False)
    #app.run(port=args.port,debug=False)
