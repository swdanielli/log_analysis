#! /usr/bin/env python

#import copy
import json
import os.path
import re
#import string
import subprocess
import sys
#import unicodedata

#from nltk import PorterStemmer

wget_tree_api = 'http://wdq.wmflabs.org/api?q=tree[%s][][31,279,361]'
wget_entity_api = '"action=wbgetentities&ids=%s&props=labels|claims&languages=en&format=json" https://www.wikidata.org/w/api.php?'
concept_cap = 250
#temp_filename = 'temp_tree'

def load_seeds(filename):
  seeds = []
  with open(filename) as f:
    for line in f:
      seed = {'terms': [], 'id': [], 'parents': [], 'parents_id': [], 'offsprings': [], 'offsprings_id': []}
      items = line.strip().split('\t')
      for item in items:
        if re.match('Q\d+$', item):
          seed['id'].append(item)
        else:
          seed['terms'].append(item)
      seeds.append(seed)
  return seeds

def wget_offsprings_id(term_id):
  matches = re.match('Q(\d+)$', term_id)
  filename = 'tree/%s' % term_id
  if not os.path.exists(filename):
    wget_tree_addr = wget_tree_api % matches.group(1)
    subprocess.call(
      'wget %s -O %s' % (
         wget_tree_addr,
         filename
      ), shell=True
    )
  try:
    items = json.load(open(filename))['items']
  except ValueError:
    return []
  if len(items) > concept_cap:
    return []
  else:
    return map(lambda x: str(x), items)

def wget_entity(entity_cache, term_id):
  if term_id not in entity_cache:
    filename = 'entity/%s' % term_id
    if not os.path.exists(filename):
      wget_entity_addr = wget_entity_api % term_id
      subprocess.call(
        'curl -s -o %s -d %s' % (
          filename,
          wget_entity_addr
        ), shell=True
      )
    entity_cache[term_id] = json.load(open(filename))['entities'][term_id]

def get_parents_id(entity_cache, term_id):
  parents_id = []
  for term_property in ['P31', 'P279', 'P361']:
    if term_property in entity_cache[term_id]['claims']:
      for claim in entity_cache[term_id]['claims'][term_property]:
        parents_id.append(str(claim['mainsnak']['datavalue']['value']['numeric-id']))
  return parents_id

def get_term_value(entity_cache, term_id):
  if 'en' not in entity_cache[term_id]['labels']:
    return []
  else:
    return [entity_cache[term_id]['labels']['en']['value']]

def unique_append(to_list, from_list, header=''):
  for from_item in from_list:
    if from_item not in to_list:
      to_list.append(header + from_item)

def filter_by_property(filtered_properties, filtered_property_values, entity_cache, term_id):
  wget_entity(entity_cache, term_id)
  if term_id not in entity_cache:
    return False
  for filtered_property in filtered_properties:
    for filtered_property_value in filtered_property_values:
      if filtered_property in entity_cache[term_id]['claims']:
        for claim in entity_cache[term_id]['claims'][filtered_property]:
          if claim['mainsnak']['datavalue']['value']['numeric-id'] == filtered_property_value:
            return False
  return True

def _main( ):
  #load_seeds(sys.argv[1])
  seeds = load_seeds('concepts')
  entity_cache = {}
  maps = {'id': 'terms', 'parents_id': 'parents', 'offsprings_id': 'offsprings'}
  f_concepts_o = open('concept_terms', 'w')

  filtered_properties = ['P31', 'P17']
  filtered_property_values = [1390618, 230]
#  print json.dumps(seeds, sort_keys=True, indent=2)
  qid_value_map = {}

  for seed in seeds:
    for term_id in seed['id']:
      wget_entity(entity_cache, term_id)
      parents_id = get_parents_id(entity_cache, term_id)
      unique_append(seed['parents_id'], parents_id, 'Q')

      noisy_offsprings_id = wget_offsprings_id(term_id)
      offsprings_id = filter(
        lambda x: filter_by_property(filtered_properties, filtered_property_values, entity_cache, 'Q' + x)
        , noisy_offsprings_id
      )
      unique_append(seed['offsprings_id'], offsprings_id, 'Q')

    for terms_id, terms in maps.iteritems():
      for term_id in seed[terms_id]:
        wget_entity(entity_cache, term_id)
        value = get_term_value(entity_cache, term_id)
        unique_append(seed[terms], value)
        if value:
          qid_value_map[term_id] = value[0]

    topic_terms = []
    for terms in maps.values():
      unique_append(topic_terms, seed[terms])
    f_concepts_o.write('\t'.join(topic_terms).encode('utf-8') + '\n')

  # http://wdq.wmflabs.org --- 504 Gateway Time-out
  # add what I have currently
  '''
  terms_id = [f for f in os.listdir('entity') if os.path.isfile('entity/' + f)]
  for term_id in terms_id:
    wget_entity(entity_cache, term_id)
    value = get_term_value(entity_cache, term_id)
    if value:
      qid_value_map[term_id] = value[0]
  '''

  f_o = open(sys.argv[1], 'w')
  f_o.write(json.dumps(qid_value_map, sort_keys=True, indent=2))
  '''
  global slides_id, trans_id, textbook_id

  f_trans_o = open(sys.argv[8], 'w')
  f_slides_o = open(sys.argv[9], 'w')
  f_textbook_o = open(sys.argv[10], 'w')

  with open(sys.argv[6], 'r') as sections:
    for line in sections:
      line = line.strip()
      items = line.split('\t')
      textbook_ids[items[0]] = 'tx' + str(len(textbook_ids.keys()))

  labels_slides_tb = {}
  for line in open(sys.argv[5], 'r').readlines():
    line = line.strip()
    items = line.split('.jpg\t')
    g = re.match('L(\d+\.\d+_\d+)', items[0])
    labels_slides_tb[g.group(1)] = items[1]
 
  with open(sys.argv[1], 'r') as lectures:
    for line in lectures:
      line = line.strip()
      items = line.split('.pdf\t')
#      print items[0]
      gen_slides_data(items[0], sys.argv[4], items[1])
      gen_trans_data(items[0], sys.argv[3], items[1], sys.argv[2], f_trans_o, labels_slides_tb)
      gen_slides_data(items[0], sys.argv[4], items[1], labels_slides_tb, f_slides_o)

  with open(sys.argv[6], 'r') as sections:
    for line in sections:
      line = line.strip()
      items = line.split('\t')
      print items[0]
      gen_tb_data(items[0], sys.argv[7], f_textbook_o)
      f_textbook_o.write('\n')

  f_trans_o.close()
  f_slides_o.close()
  f_textbook_o.close()
  '''
if __name__ == '__main__':
  _main( )
