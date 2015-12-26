#! /usr/bin/env python

analytics_util_dir = '/usr/users/swli/program/analytics_util'
#import copy
import datetime
#import gzip
import itertools
import json
#import math
import os.path
import re
#import string
#import subprocess
import sys
sys.path.append(analytics_util_dir)

import analytics_util

start_date = datetime.date(2015, 7, 14)
end_date = datetime.date(2015, 12, 22)

def update_counts(event_counts, module_counts, event_type, element):
  if event_type not in event_counts:
    event_counts[event_type] = 0
  event_counts[event_type] += 1
  if event_type not in module_counts:
    module_counts[event_type] = []
  module_counts[event_type].append(element)

def write_statistics(f_o, event_counts, module_counts, event_name, is_last=False):
  f_o.write('%d/%d%s' % (
    event_counts[event_name] if event_name in event_counts else 0,
    len(list(set(module_counts[event_name]))) if event_name in module_counts else 0,
    '\n' if is_last else '\t'
  ))

def _main( ):
  user_list = sys.argv[1]
  user_event_dir = sys.argv[2]
  recommender_event_analysis_dir = sys.argv[3]
  considered_events = [
    'mit.recommender.addResource',
    'mit.recommender.arrowDown',
    'mit.recommender.arrowUp',
    'mit.recommender.backToView',
    'mit.recommender.clickResource',
    'mit.recommender.editResource',
    'mit.recommender.endorseResource', # total (attempt) = success, undo
    'mit.recommender.exportResource',
    'mit.recommender.flagResource', # total (attempt), success, undo
    'mit.recommender.hideShow', # how many people access RXB
    'mit.recommender.hover',
    'mit.recommender.importResource',
    'mit.recommender.pagination',
    'mit.recommender.removeResource'
  ]
  closest_event_diff = 1.0  # meaningful events (especially for hovering) should be separated by at least 1 second
  users = analytics_util.load_users(user_list)

  for single_date in itertools.chain(analytics_util.date_range_gen(start_date, end_date), ['accumulation']):
    f_o = open('%s/%s' % (recommender_event_analysis_dir, single_date), 'w')
    f_o.write('\t'.join([
      'user_id',
      'add_resource_attempt', # n_events/n_unique_RXB
      'add_resource_success',
      'downvote',
      'upvote',
      'back_to_view',
      'click_resource',
      'edit_resource_attempt',
      'edit_resource_success',
      'endorse_resource',
      'unendorse_resource',
      'export_resource_attempt',
      'export_resource_success',
      'flag_resource_attempt',
      'flag_resource',
      'unflag_resource',
      'access_RXB',
      'hover_resource',
      'import_resource_attempt',
      'import_resource_success',
      'click_pagination',
      'remove_resource_attempt',
      'remove_resource_success'
    ]) + '\n')

    for user in users:
      event_filename = '%s/%d/%s' % (user_event_dir, user, single_date)
      if not os.path.isfile(event_filename):
        continue

      prev_action_time = {}
      event_counts = {}
      module_counts = {}

      events = analytics_util.load_time_sorted_event(
        event_filename,
        ['mit.recommender'],
        lambda x: 'event_type' not in x or x['event_type'] not in considered_events
      )

      for event in events:
        event_info = json.loads(event['event'])
        try:
          if event['event_type'] in ['mit.recommender.arrowDown', 'mit.recommender.arrowUp', 'mit.recommender.hover', 'mit.recommender.pagination']:
            if (
              event['event_type'] not in prev_action_time or
              analytics_util.time_diff(prev_action_time[event['event_type']], event['time']) > closest_event_diff
            ):
              update_counts(event_counts, module_counts, event['event_type'], event_info['element'])
            prev_action_time = {event['event_type']: event['time']}
          else:
            prev_action_time = {}
            if (
              event['event_type'] in [
                'mit.recommender.addResource',
                'mit.recommender.editResource',
                'mit.recommender.endorseResource',
                'mit.recommender.exportResource',
                'mit.recommender.importResource',
                'mit.recommender.removeResource',
                'mit.recommender.flagResource',
                'mit.recommender.backToView',
                'mit.recommender.clickResource'
              ] or (event['event_type'] in ['mit.recommender.hideShow'] and event_info['status'] in ['show'])
            ):
              update_counts(event_counts, module_counts, event['event_type'], event_info['element'])
              if event_info['status'] in ['Add new resource', 'Edit existing resource', 'Endorse resource', 'Export resources', 'Import resources', 'Remove resource', 'Flag resource']:
                update_counts(event_counts, module_counts, '%s.success' % event['event_type'], event_info['element'])
              elif event_info['status'] in ['Unflag resource', 'Unendorse resource']:
                update_counts(event_counts, module_counts, '%s.undo' % event['event_type'], event_info['element'])
        except KeyError:
          print 'KeyError: ' + str(event)

      # user_id
      f_o.write('%d\t' % user)
      for event in considered_events:
        if event in ['mit.recommender.arrowDown', 'mit.recommender.arrowUp', 'mit.recommender.backToView', 'mit.recommender.clickResource', 'mit.recommender.hideShow', 'mit.recommender.hover', 'mit.recommender.pagination']:
          # downvote, upvote, back_to_view, click_resource, access_RXB, hover_resource, click_pagination
          write_statistics(f_o, event_counts, module_counts, event)
        else:
          # add_a/s, edit_a/s, endorse_s/u, export_a/s, flag_a/s/u import_a/s, remove_a/s
          # attempt
          if event not in ['mit.recommender.endorseResource']:
            write_statistics(f_o, event_counts, module_counts, event)
          # success
          if event not in ['mit.recommender.removeResource']:
            write_statistics(f_o, event_counts, module_counts, '%s.success' % event)
          else:
            write_statistics(f_o, event_counts, module_counts, '%s.success' % event, True)
          # undo
          if event in ['mit.recommender.endorseResource', 'mit.recommender.flagResource']:
            write_statistics(f_o, event_counts, module_counts, '%s.undo' % event)

if __name__ == '__main__':
  _main( )
