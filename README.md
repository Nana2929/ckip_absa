# ckip_absa_ch
  - Academia Sinica CKIP Lab 
  - Summer Internship 2022
    - Collaborators: Ching Wen Yang, Chia Wen Lu
  - Aspect Based Sentiment Analysis System
    - Domain: Restaurant
    - Language: Traditional Chinese
  - Implementation:
    - Unsupervised, rule-based ABSA system 
    - [CKIP Chinese Dependency Parser](https://ckip.iis.sinica.edu.tw/service/dependency-parser/)
    - Lexicon-based Method: keeping a food(*aspect*) lexicon of 8K entries and a sentiment(*opinion*) lexicon cvaw4 of 5.6K entries
      - 2022.8 [Update] Expanding food(*aspect*) lexicon to 33K entries by crawling and segmenting
    - Shortest path algorithm from a found opinion to a found aspect
      - 2022.8 [Update] For each found opinion, search its aspect by NOUN relations, if a relation exists, set it as the aspect instead of running SP algorithm. 
    - Particularly dealing with "Neg" (不) and "Advmod" (都) dep relations
    
  - [Meeting Minutes](https://docs.google.com/document/d/17dW7Ez8wbULITSe6E5FWNudWOelQmqiWVbFqYe4M15Y/edit?usp=sharing)
  - [Drive](https://drive.google.com/drive/folders/10MmRyd7-w2vSHFracueSCn32Sps6BEwO?usp=sharing)
  - 🥨 餐廳評論分析系統 [Demo (CKIP Cluster/Internal)](https://ckip.iis.sinica.edu.tw/service/restaurant-absa/)

