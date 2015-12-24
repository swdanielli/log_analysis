#! /usr/bin/env python

analytics_util_dir = '/usr/users/swli/program/analytics_util'
#import copy
#import json
import os.path
import re
#import string
#import subprocess
import sys
sys.path.append(analytics_util_dir)

import analytics_util

def parse_cond_sql(header, user):
  user_id = user[header.index('user_id')]
  group_id = re.match("xblock.partition_service.partition_(\d+)$", user[header.index('key')]).group(1)
  method_id = user[header.index('value')]
  return (user_id, group_id, method_id)

def parse_common_sql(header, user, concerned_slots):
  result = []
  for slot in concerned_slots:
    result.append(user[header.index(slot)])
  return result

def _main( ):
  database_condition = sys.argv[1]
  database_grades = sys.argv[2]
  user_list = sys.argv[3]
  inactive_user_list = sys.argv[4]
  rec_split_test = ['no_rec', 'rec']
  dis_split_test = ['no_dis', 'dis']
  split_test_id = ['604188856', '545632689']
  conditions = {
    split_test_id[0]: {'1777607612': dis_split_test[1], '1219160103': dis_split_test[0]},
    split_test_id[1]: {'1306630916': rec_split_test[1], '638756241': rec_split_test[0]}
  }
  split_users = {}
  grades = {}

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

  for (header, user) in analytics_util.load_csv_like(database_grades, '\t'):
    result = parse_common_sql(header, user, ['user_id', 'grade'])
    grades[result[0]] = result[1]

  for (split_test, user_ids) in split_users.iteritems():
    if not os.path.exists(split_test):
      os.makedirs(split_test)
    f_o = open('%s/%s' % (split_test, user_list), 'w')
    f_o_inactive = open('%s/%s' % (split_test, inactive_user_list), 'w')
    accumulate_grades = []

    for user_id in user_ids:
      if user_id in grades:
        if float(grades[user_id]) > 0.0:
          accumulate_grades.append(float(grades[user_id]))
          f_o.write('%s\t%s\n' % (user_id, grades[user_id]))
        else:
          f_o_inactive.write('%s\t%s\n' % (user_id, grades[user_id]))
    print 'Groups: %s\tSize: %d\tAverage grades: %f\n' % (split_test, len(accumulate_grades), sum(accumulate_grades)/len(accumulate_grades))

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
