#! /usr/bin/env python

analytics_util_dir = '/usr/users/swli/program/analytics_util'
#import copy
#import json
#import os.path
import re
#import string
#import subprocess
import sys
sys.path.append(analytics_util_dir)

import analytics_util

def load_courseware(courseware_raw_fname, courseware_corpus_dir, courseware_pos_dir, id_mapping, stopwords, is_stemming, courseware_type, is_math, courseware_math_word_dir=None):
  data_generator = my_util.load_raw_data(courseware_raw_fname)
  l_id = ''

  if courseware_type == 'slides':
    key = 'id'
  elif courseware_type == 'tx':
    key = 'id'
  elif courseware_type == 'trans':
    key = 'link_1'
    tx_key = 'link_2'

  courseware_corpus_dir += '/%s' % courseware_type
  courseware_pos_dir += '/%s' % courseware_type
  if courseware_math_word_dir:
    courseware_math_word_dir += '/%s' % courseware_type

  if not os.path.exists(courseware_corpus_dir):
    os.makedirs(courseware_corpus_dir)
  if not os.path.exists(courseware_pos_dir):
    os.makedirs(courseware_pos_dir)
  if courseware_math_word_dir and not os.path.exists(courseware_math_word_dir):
    os.makedirs(courseware_math_word_dir)

  content = ''
  pos_buffer = ''
  vocabs = []
  f_o = None
  fpos_o = None
  if courseware_math_word_dir:
    math_buffer = ''
    fmath_o = None

  for data in data_generator:
    if data[key] not in id_mapping:
      print data
      continue

    if l_id != id_mapping[data[key]]['l_id']:
      l_id = id_mapping[data[key]]['l_id']
      if courseware_type in ['trans']:
        count = 1
      if f_o:
        f_o.write(content.strip() + '\n')
        f_o.close()
        content = ''
        fpos_o.write(pos_buffer.strip() + '\n')
        fpos_o.close()
        pos_buffer = ''
        if courseware_math_word_dir:
          fmath_o.write(math_buffer.strip() + '\n')
          fmath_o.close()
          math_buffer = ''
      f_o = open(courseware_corpus_dir + '/' + l_id, 'w')
      fpos_o = open(courseware_pos_dir + '/' + l_id, 'w')
      if courseware_math_word_dir:
        fmath_o = open(courseware_math_word_dir + '/' + l_id, 'w')

    preprocess_result = my_util.preprocess_content(
      data['content'].strip(),
      stopwords,
      is_math=is_math,
      is_stemming=is_stemming,
      is_return_pos=True,
      is_return_math_words=(not is_math)
    )
    words = preprocess_result[0]
    pos_tags = preprocess_result[1]

    processed_line = ' '.join(words)
    processed_line = re.sub('\s+', ' ', processed_line.strip())
    processed_tags = ' '.join(pos_tags)
    processed_tags = re.sub('\s+', ' ', processed_tags.strip())

    if courseware_type in ['trans']:
      doc_count = 'TRANS_%s_%d' % (l_id, count)
      count += 1
    elif courseware_type in ['slides']:
      doc_count = 'SLIDES_%s_%d' % (l_id, id_mapping[data[key]]['page_idx'])
    elif courseware_type in ['tx']:
      doc_count = 'TX_%s'% id_mapping[data[key]]['page_idx'] 
      
    if processed_line:
      content += '%s\t%s\n' % (processed_line, doc_count)
      pos_buffer += '%s\t%s\n' % (processed_tags, doc_count)
    else:
      content += 'this_is_an_empty_line\t%s\n' % doc_count
      pos_buffer += 'None\t%s\n' % doc_count

    if courseware_math_word_dir:
      math_words = preprocess_result[2]
      vocabs += math_words
      processed_math = re.sub('\s+', ' ', (' '.join(math_words)).strip())
      math_buffer += '%s\t%s\n' % (processed_math, doc_count)

  if f_o:
    f_o.write(content.strip() + '\n')
    f_o.close()
    fpos_o.write(pos_buffer.strip() + '\n')
    fpos_o.close()
    if courseware_math_word_dir:
      fmath_o.write(math_buffer.strip() + '\n')
      fmath_o.close()

  return vocabs

def wget_wiki_page(term, corpus_dir, stopwords, loaded_entities, disambiguation_suffixes, is_stemming, wiki_doc_count, is_math):
  f_pre_tokenized_name = 'file_pre_tokenized.temp'
  if term not in loaded_entities:
    loaded_entities.append(term.lower())
  else:
    return (wiki_doc_count, None)

  try:
    wiki_page = wikipedia.page(term)
  except wikipedia.exceptions.DisambiguationError as e:
    options = []
    for disambiguation_suffix in disambiguation_suffixes:
      for option in e.options:
        if disambiguation_suffix in option:
          options.append(option)

    for option in options:
      (wiki_doc_count, _) = wget_wiki_page(option, corpus_dir, stopwords, loaded_entities, disambiguation_suffixes, is_stemming, wiki_doc_count, is_math)

    return (wiki_doc_count, None)
  except wikipedia.exceptions.PageError:
    return (wiki_doc_count, None)

  f_temp = open(f_pre_tokenized_name, 'w')
  f_temp.write(wiki_page.title.encode('utf-8') + '\n')

  content = re.sub(r'\n===(.+)Edit ===\n', r'\n\1.\n', wiki_page.content + '\n')
  content = re.sub(r'\n==(.+)Edit ==\n', r'\n\1.\n', content)
  content = re.sub(r'\n===(.+)===\n', r'\n\1.\n', content)
  content = re.sub(r'\n==(.+)==\n', r'\n\1.\n', content)
  f_temp.write(content.encode('utf-8'))
  f_temp.close()

  f_o = open(corpus_dir + '/' + term, 'w')
  content = ''
  for line in my_util.tokenization(f_pre_tokenized_name).stdout.readlines():
    if re.match('Read in \d+ sentences', line):
      break
    processed_line = ' '.join(
      my_util.preprocess_content(
        line.strip(),
        stopwords,
        is_math=is_math,
        is_stemming=is_stemming
      )
    )
    processed_line = re.sub('\s+', ' ', processed_line.strip())
    if processed_line:
      content += processed_line + '\n'

  sentences = re.sub('\n+', '\n', content.strip()).split('\n')

  for sentence in sentences:
    f_o.write(sentence.strip() + '\tWIKI_DOC_COUNT_%d\n' % wiki_doc_count)
    wiki_doc_count += 1
  f_o.close()

  return (wiki_doc_count, wiki_page)

def parse_cond_sql(header, user):
  user_id = user[header.index('user_id')]
  group_id = re.match("xblock.partition_service.partition_(\d+)$", user[header.index('key')]).group(1)
  method_id = user[header.index('value')]
  return (user_id, group_id, method_id)

def _main( ):
  database_condition = sys.argv[1]
  rec_split_test = ['no_rec', 'rec']
  dis_split_test = ['no_dis', 'dis']
  split_test_id = ['604188856', '545632689']
  conditions = {
    split_test_id[0]: {'1777607612': dis_split_test[1], '1219160103': dis_split_test[0]},
    split_test_id[1]: {'1306630916': rec_split_test[1], '638756241': rec_split_test[0]}
  }
  split_users = {}

  group = [None, None]
  for (header, user) in analytics_util.load_csv_like(database_condition, '\t'):
    (user_id, group_id, method_id) = parse_cond_sql(header, user)
    group[split_test_id.index(group_id)] = conditions[group_id][method_id]

    if group[0] and group[1]:
      method = '_'.join(group)
      if method not in split_users:
        split_users[method] = []
      split_users[method].append(user_id)
      group = [None, None]

  '''
  # Choose preprocessing method
  preprocess_method = sys.argv[3]
  stopwords = []
  is_stemming = False
  is_math = True

  if re.match('.*remove_stop', preprocess_method):
    stopwords = my_util.load_stopwords(nlp_util_dir + '/stopList')
  if re.match('.*stem', preprocess_method):
    is_stemming = True
  if re.match('.*no_math', preprocess_method):
    is_math = False

  # wget wiki pages
  entities = []
  base_concepts = ['Statistics']
  wiki_corpus_dir = sys.argv[1]
  disambiguation_suffixes = ['mathematics', 'statistics']
  wiki_doc_count = 0

  # base concepts: load every term in the page
  for term in base_concepts:
    (wiki_doc_count, wiki_page) = wget_wiki_page(term, wiki_corpus_dir, stopwords, entities, disambiguation_suffixes, is_stemming, wiki_doc_count, is_math)
    for link in wiki_page.links:
      (wiki_doc_count, _) = wget_wiki_page(link, wiki_corpus_dir, stopwords, entities, disambiguation_suffixes, is_stemming, wiki_doc_count, is_math)

  # concepts in textbook glossary
  qid_value_map = json.load(open(sys.argv[2]))
  for term in qid_value_map.values():
    (wiki_doc_count, _) = wget_wiki_page(term, wiki_corpus_dir, stopwords, entities, disambiguation_suffixes, is_stemming, wiki_doc_count, is_math)


  dictionary = []
  mapping_s_fname = sys.argv[4]
  mapping_tx_fname = sys.argv[5]
  slides_raw_fname = sys.argv[6]
  trans_raw_fname = sys.argv[7]
  tx_raw_fname = sys.argv[8]
  courseware_corpus_dir = sys.argv[9]
  courseware_pos_dir = sys.argv[10]
  courseware_math_word_dir = None
  if re.match('.*no_math', preprocess_method):
    courseware_math_word_dir = sys.argv[11]
    math_word_dict = sys.argv[12]

  sid_mapping = my_util.load_id_mapping(mapping_s_fname)
  txid_mapping = my_util.load_id_mapping(mapping_tx_fname, resource_type='tx', tx_start_type='Ch')
  math_words = load_courseware(slides_raw_fname, courseware_corpus_dir, courseware_pos_dir, sid_mapping, stopwords, is_stemming, 'slides', is_math, courseware_math_word_dir)
  dictionary += math_words

  math_words = load_courseware(trans_raw_fname, courseware_corpus_dir, courseware_pos_dir, sid_mapping, stopwords, is_stemming, 'trans', is_math, courseware_math_word_dir)
  dictionary += math_words

  math_words = load_courseware(tx_raw_fname, courseware_corpus_dir, courseware_pos_dir, txid_mapping, stopwords, is_stemming, 'tx', is_math, courseware_math_word_dir)
  dictionary += math_words

  if not is_math:
    my_util.print_vocab_list(math_word_dict, dictionary)
  '''
if __name__ == '__main__':
  _main( )
