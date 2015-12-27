#! /usr/bin/env python

analytics_util_dir = '/usr/users/swli/program/analytics_util'
#import copy
import datetime
import gzip
import itertools
import json
import math
import os.path
import re
#import string
#import subprocess
import sys
sys.path.append(analytics_util_dir)

import analytics_util

start_date = datetime.date(2015, 7, 14)
end_date = datetime.date(2015, 12, 22)

def _main( ):
  user_list = sys.argv[1]
  user_event_dir = sys.argv[2]
  video_event_analysis_dir = sys.argv[3]
  considered_events = [
    'speed_change_video',
    'play_video',
    'edx.video.played',
    'pause_video',
    'edx.video.paused',
    'stop_video',
    'edx.video.stopped',
    'seek_video',
    'edx.video.position.changed',
    'page_close',
    'seq_goto',
    'seq_next',
    'seq_prev'
  ]
  watch_time_cap = 2.0 * 60 * 60  # max watch time in one video: 2 hours
  users = analytics_util.load_users(user_list)

  for single_date in itertools.chain(analytics_util.date_range_gen(start_date, end_date), ['accumulation']):
    f_o = open('%s/%s' % (video_event_analysis_dir, single_date), 'w')
    f_o.write('\t'.join(['user_id', 'watch_time', 'n_played_videos', 'covered_video_time', 'watch_2_cover', 'f_seek', 'b_seek', 'n_speed_changes', 'avg_changed_speed']) + '\n')

    for user in users:
      event_filename = '%s/%d/%s' % (user_event_dir, user, single_date)
      if not os.path.isfile(event_filename):
        continue

      backward_seek = 0 # replay
      forward_seek = 0
      played_video_id = None
      speed_changes = []
      real_start_time = None
      accumulated_real_watch_time = 0.0
      play_start_time = None
      played_videos = {}

      events = analytics_util.load_time_sorted_event(
        event_filename,
        ['video', 'page_close', 'seq_'],
        lambda x: 'event_type' not in x or 'event' not in x or x['event_type'] not in considered_events
      )

      for event in events:
        event_info = json.loads(event['event'])
        try:
          if event['event_type'] in ['speed_change_video']:
            speed_changes.append(float(event_info['new_speed']))
          elif event['event_type'] in ['play_video', 'edx.video.played']:
            if not played_video_id or played_video_id != event_info['code']:
              if played_video_id:
                print event

              played_video_id = event_info['code']
              real_start_time = event['time']
              play_start_time = int(math.ceil(event_info['currentTime']))
          elif event['event_type'] in ['pause_video', 'edx.video.paused', 'stop_video', 'edx.video.stopped', 'page_close', 'seq_goto', 'seq_next', 'seq_prev']:
            if played_video_id:
              if 'code' in event_info and played_video_id != event_info['code']:
                print event
              else:
                time_diff = analytics_util.time_diff(real_start_time, event['time'])
                if time_diff < watch_time_cap:
                  accumulated_real_watch_time += time_diff
                  if event['event_type'] not in ['page_close', 'seq_goto', 'seq_next', 'seq_prev']:
                    play_end_time = int(event_info['currentTime']) + 1
                    if play_end_time > play_start_time:
                      if played_video_id not in played_videos:
                        played_videos[played_video_id] = []
                      played_videos[played_video_id].append((play_start_time, play_end_time))

              played_video_id = None
              real_start_time = None
              play_start_time = None
          elif event['event_type'] in ['seek_video', 'edx.video.position.changed']:
            new_time = event_info['new_time']
            old_time = event_info['old_time']
            if old_time > new_time:
              backward_seek += 1
            else:
              forward_seek += 1

            if played_video_id:
              if played_video_id != event_info['code']:
                print event
              else:
                play_end_time = int(old_time) + 1
                if play_end_time > play_start_time:
                  if played_video_id not in played_videos:
                    played_videos[played_video_id] = []
                  played_videos[played_video_id].append((play_start_time, play_end_time))
                play_start_time = int(math.ceil(new_time))
        except KeyError:
          print 'KeyError: ' + str(event)

      # user_id
      f_o.write('%d\t' % user)
      # watch_time
      f_o.write('%f\t' % accumulated_real_watch_time)
      # n_played_videos
      f_o.write('%d\t' % len(played_videos.keys()))
      # covered_video_time
      covered_video_time = 0
      for watch_sessions in played_videos.values():
        watched_seconds = []
        for watch_session in watch_sessions:
          for i in range(watch_session[0], watch_session[1]):
            watched_seconds.append(i)
        covered_video_time += len(list(set(watched_seconds)))
      f_o.write('%d\t' % covered_video_time)
      # watch_2_cover
      f_o.write('%f\t' % (accumulated_real_watch_time/covered_video_time if covered_video_time else 0.0))
      # f_seek
      f_o.write('%d\t' % forward_seek)
      # b_seek
      f_o.write('%d\t' % backward_seek)
      # n_speed_changes
      f_o.write('%d\t' % len(speed_changes))
      # avg_changed_speed
      f_o.write('%f\n' % (float(sum(speed_changes))/len(speed_changes) if len(speed_changes) > 0 else 0.0))
      #staticvoid

if __name__ == '__main__':
  _main( )
