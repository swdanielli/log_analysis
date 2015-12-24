#! /usr/bin/env python

# import modules & set up logging
import gensim, logging
import sys

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

trans_doc_prefix = 'TRANS'
slides_doc_prefix = 'SLIDES'

def load_corpus(corpus_name):
  sentences = []
  labels = []
  for line in open(corpus_name):
    items = line.strip().split('\t')
    sentences.append(items[0].split(' '))
    labels.append(items[1])
  return (sentences, labels)

def get_doc_size(doc_type, l_id, labels):
  doc_size = 1
  while get_doc_tags(doc_type, l_id, doc_size) in labels:
    doc_size += 1
  return doc_size - 1

def get_doc_tags(doc_type, l_id, index):
  if doc_type in [trans_doc_prefix, slides_doc_prefix]:
    return '%s_%s_%d' % (doc_type, l_id, index)

def _main( ):
  corpus_name = sys.argv[1]
  model_name = sys.argv[2]
  lecture_list_name = sys.argv[3]
  fea_dir = sys.argv[4]

  (_, labels) = load_corpus(corpus_name)
  model = gensim.models.Doc2Vec.load(model_name)

  for l_id in open(lecture_list_name):
    l_id = l_id.strip()
    trans_size = get_doc_size(trans_doc_prefix, l_id, labels)
    slides_size = get_doc_size(slides_doc_prefix, l_id, labels)

    f_o = open('%s/%s' % (fea_dir, l_id), 'w')
    for trans_idx in range(1, trans_size + 1):
      fea = []
      for slides_idx in range(1, slides_size + 1):
        sim = model.docvecs.similarity(
          get_doc_tags(slides_doc_prefix, l_id, slides_idx),
          get_doc_tags(trans_doc_prefix, l_id, trans_idx)
        )
        fea.append(str(sim))

      f_o.write('\t'.join(fea) + '\n')
    f_o.close()

if __name__ == '__main__':
  _main( )
