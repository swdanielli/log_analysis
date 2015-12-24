#! /usr/bin/env python

# import modules & set up logging
import gensim, logging
from random import shuffle
import sys

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

def _main( ):
  alpha, min_alpha, passes = (0.025, 0.001, 60)
  alpha_delta = (alpha - min_alpha) / passes

  corpus_name = sys.argv[1]
  model_name = sys.argv[2]

  sentences = []
  labels = []
  for line in open(corpus_name):
    items = line.strip().split('\t')
    sentences.append(items[0].split(' '))
    labels.append(items[1])

  bigram_transformer = gensim.models.Phrases(sentences, min_count=3)
  trigram_transformer = gensim.models.Phrases(bigram_transformer[sentences], min_count=3)
  sentences = trigram_transformer[bigram_transformer[sentences]]

  docs = []
  for doc_idx in range(len(sentences)):
    docs.append(gensim.models.doc2vec.LabeledSentence(words=sentences[doc_idx], tags=[labels[doc_idx]]))

  # use fixed learning rate
  model = gensim.models.Doc2Vec(alpha=alpha, min_alpha=alpha, size=100, window=5, min_count=3, sample=1e-5, negative=10)
  model.build_vocab(docs)

  for epoch in range(passes):
#    shuffle(docs)
    model.train(docs)
    model.alpha -= alpha_delta # decrease the learning rate
    model.min_alpha = model.alpha  # fix the learning rate, no decay

  # model.accuracy('google_eval/questions-words.txt')
  model.save(model_name)
  # model = gensim.models.Doc2Vec.load(model_name)
  # model.train(more_sentences)

'''
def find_tags(index):
  return docs[index].tags[0]

def find_id(id):
  for index in range(len(docs)):
    if docs[index].tags[0] == id:
      return index

def most_sim(model, id, topn):
  for pair in model.docvecs.most_similar(id, topn=topn):
    if 'WIKI_DOC_COUNT' not in find_tags(pair[0]):
      print find_tags(pair[0])

# lo_types in ['TRANS', 'SLIDES', 'WIKI_DOC_COUNT']
def most_sim(id, topn, model, lo_types):
  for pair in model.docvecs.most_similar(id, topn=topn):
    if lo_types in find_tags(pair[0]):
      print find_tags(pair[0])

>>> model.docvecs.most_similar(30000)
[(33887, 0.9392176866531372), (44978, 0.9350051879882812), (73554, 0.9346908926963806), (102010, 0.9325971603393555), (40392, 0.931594967842102), (59577, 0.9314853549003601), (37001, 0.9313675165176392), (87141, 0.9310975074768066), (24783, 0.9310616850852966), (85367, 0.930946946144104)]
>>> model.docvecs.most_similar(33887)
[(35521, 0.9771468639373779), (76667, 0.9766572713851929), (50768, 0.9766234159469604), (43275, 0.9765418767929077), (42501, 0.9764294624328613), (88586, 0.9763633608818054), (65728, 0.9763003587722778), (51228, 0.9762075543403625), (40768, 0.9761608242988586), (15963, 0.9761068820953369)]
>>> model.docvecs.most_similar(35521)
[(53145, 0.996285617351532), (55970, 0.9962190389633179), (43275, 0.9961640238761902), (25158, 0.9959849715232849), (31596, 0.9958720207214355), (6330, 0.9958254098892212), (35155, 0.9957549571990967), (52861, 0.9957283735275269), (63068, 0.9957234263420105), (46005, 0.9957040548324585)]
>>> model.docvecs.most_similar(53145)
[(51630, 0.9971001744270325), (64165, 0.9970839023590088), (6330, 0.997072696685791), (63068, 0.9968304634094238), (53918, 0.9967813491821289), (53437, 0.9967505931854248), (78979, 0.9966580271720886), (53070, 0.9966079592704773), (55970, 0.9965354800224304), (43275, 0.9964852929115295)]
>>> model.docvecs.most_similar(51630)
[(6330, 0.9973094463348389), (58220, 0.9972167015075684), (53437, 0.9971422553062439), (53145, 0.9971001744270325), (31596, 0.997093915939331), (55478, 0.9970093965530396), (52861, 0.9969046115875244), (61466, 0.9968329071998596), (25158, 0.9968326687812805), (89375, 0.9967776536941528)]
>>> model.docvecs.similarity(51630, 6330)
0.99730961687520714
>>> model.docvecs.similarity(51630, 58220)
0.99721675756183958
>>> model.docvecs.similarity(51630, 89375)
0.99677752439887701
>>>



>>> model.doesnt_match("bernoulli poisson normal average".split())
'bernoulli'
>>> model.doesnt_match("bernoulli poisson normal sd".split())
'sd'
>>> model.doesnt_match("mean median average".split())
'average'
>>> model.doesnt_match("mean median mode average".split())
'average'
>>> model.doesnt_match("mean median mode".split())
'mode'
>>> model.doesnt_match("mean median mode sd".split())
'sd'
>>> model.doesnt_match("mean median mode standard_deviation".split())
'mode'
>>> model.doesnt_match("mean mode standard_deviation".split())
'mode'
>>> model.doesnt_match("mean median mode quartile".split())
'quartile'
>>> model.doesnt_match("mean median mode regression".split())
'regression'
>>> model.doesnt_match("mean median mode standard_deviation normal".split())
'normal'
>>> model.doesnt_match("mean median mode standard_deviation regression".split())
'regression'
>>>
'''

if __name__ == '__main__':
  _main( )
