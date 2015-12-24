#! /usr/bin/env python

# import modules & set up logging
import gensim, logging
import sys

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

class my_sentences(object):
  def __init__(self, corpus_name):
    self.corpus_name = corpus_name

  def __iter__(self):
    with open(self.corpus_name, 'r') as f:
      for line in f:
        yield line.strip().split('\t')[0].split(' ')

'''
def load_corpus(corpus_name):
  with open(corpus_name, 'r') as f:
    for line in f:
      yield line.strip().split('\s+')
      # yield line.strip().split('\s+')
'''

def _main( ):
  corpus_name = sys.argv[1]
  model_name = sys.argv[2]
  dim = int(sys.argv[3])
  sentences = my_sentences(corpus_name)
  # bigram_transformer = gensim.models.Phrases(sentences, min_count=2)
  # trigram_transformer = gensim.models.Phrases(bigram_transformer[sentences], min_count=2)

  model = gensim.models.Word2Vec(
    sentences,
    min_count=2,
    sample=1e-5,
    negative=10,
    size=dim,
    iter=20
  )
  '''
  model = gensim.models.Word2Vec(
    trigram_transformer[bigram_transformer[sentences]],
    min_count=2,
    sample=1e-5,
    negative=10,
    size=dim,
    iter=20
  )
  '''
  model.accuracy('google_eval/questions-words.txt')

  model.save(model_name)
  # model = gensim.models.Word2Vec.load(model_name)
  # model.train(more_sentences)

'''
>>> model.doesnt_match("bernoulli poisson normal average".split())
'average'
>>> model.doesnt_match("bernoulli poisson normal sd".split())
'sd'
>>> model.doesnt_match("mean median average".split())
'median'
>>> model.doesnt_match("mean median mode average".split())
'average'
>>> model.doesnt_match("mean median mode".split())
'mean'
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


>>> model.most_similar_cosmul(positive=['mean', 'regression'], negative=['standard_deviation'])
[(u'residuals', 0.9418241381645203), (u'regression_line', 0.9229797124862671), (u'good_summary', 0.9160003662109375), (u'scatterplots', 0.9058727622032166), (u'linear_regression', 0.903145432472229), (u'correlation_coefficient', 0.9021129012107849), (u'straight_line', 0.9014043807983398), (u'variables', 0.9011037945747375), (u'dependent_variable_y', 0.8984076976776123), (u'residual_plot_than', 0.8976736664772034)]
'''

if __name__ == '__main__':
  _main( )
