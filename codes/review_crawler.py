import requests
import json
import re
import string
import pandas as pd

'''
Path to get url of comments in google:
Network/XHR/listentitlereviews.../header/Request URL
'''

# lists of comments' information
sentence_list = []
index_list = []
time_list = []
rating_list = []
len_list = []

# url of comments
url1 = 'https://www.google.com/maps/preview/review/listentitiesreviews?authuser=0&hl=zh-TW&gl=tw&pb=!1m2!1y3765760552082614337!2y2473994719707822216!2m2!1i0!2i10!3e1!4m5!3b1!4b1!5b1!6b1!7b1!5m2!1s1yO5Yqn_Bo6ohwPetJHwAg!7e81'
url2 = 'https://www.google.com/maps/preview/review/listentitiesreviews?authuser=0&hl=zh-TW&gl=tw&pb=!1m2!1y3765760552082614337!2y2473994719707822216!2m2!1i10!2i10!3e1!4m5!3b1!4b1!5b1!6b1!7b1!5m2!1s1yO5Yqn_Bo6ohwPetJHwAg!7e81'

# number of comment
comm_num = 1

for k in range(2):
    if k+1 == 1:
        url = url1
    else:
        url = url2

    # request of get
    text = requests.get(url).text

    # replace some characters
    pretext = ')]}\''
    text = text.replace(pretext,'')

    # convert string to json
    soup = json.loads(text)

    # list of comments
    conlist = soup[2]

    # all comments
    for i in conlist:
        # comm_user = str(i[0][1])
        comm_time = str(i[1]).replace(' ', '')
        comm_text = str(i[3])
        comm_rating = str(i[4])
        print('index: ' + str(comm_num))
        print('time: ' + comm_time)
        print('review: ' + '\n'+ comm_text)
        print('rating: ' + comm_rating)
        sentences = re.split('，|\,|。|！|\!|？|\?|\s|;', comm_text) # split text by delimiter

        # print(str(i[3]))
        # print(sentences)
        for sent in sentences:
            if len(sent) > 0:
                if sent[0] not in string.punctuation:
                    sentence_list.append(sent)
                    index_list.append(comm_num)
                    len_list.append(len(sent))
                    time_list.append(comm_time)
                    rating_list.append(comm_rating)

        comm_num += 1
        print('\n')

print(sentence_list)
print(index_list)
print(len_list)
print(time_list)
print(rating_list)

df = pd.DataFrame({'sentence': sentence_list, 'index': index_list, 'length': len_list, 'time': time_list, 'rating': rating_list})
# print(df)
# df.to_csv('review_clean.csv', index = False)