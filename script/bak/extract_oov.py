#! /usr/bin/env python

nlp_util_dir = '/usr/users/swli/program/nlp_util'

# import modules & set up logging
import gensim, logging
import numpy as np
import re
import sys
sys.path.append(nlp_util_dir)

import my_util

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

trans_doc_prefix = 'TRANS'
slides_doc_prefix = 'SLIDES'
tx_doc_prefix = 'TX'

def load_corpus(corpus_name):
  corpus = {}
  for line in open(corpus_name):
    items = line.strip().split('\t')
    corpus[items[1]] = items[0].split(' ')
  return corpus

def _main( ):
  model_name = sys.argv[1]
  oov_dict_name = sys.argv[2]
  corpus_name = sys.argv[3]

  corpus = load_corpus(corpus_name)
  model = gensim.models.Word2Vec.load_word2vec_format(model_name, binary=True)
  oov_vocabs = []

  for doc_tag, doc in corpus.iteritems():
    items = re.split('_', doc_tag)
    if items[0] in [trans_doc_prefix, slides_doc_prefix, tx_doc_prefix]:
      for word in doc:
        if word not in model:
          oov_vocabs.append(word)

  my_util.print_vocab_list(oov_dict_name, oov_vocabs)

if __name__ == '__main__':
  _main( )
