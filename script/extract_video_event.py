#! /usr/bin/env python

analytics_util_dir = '/usr/users/swli/program/analytics_util'
#import copy
import datetime
import gzip
import json
import math
import os.path
import re
#import string
#import subprocess
import sys
sys.path.append(analytics_util_dir)

import analytics_util

def write_event(event_handlers, user_id, user_event_dir, user_event_fname, event):
  if user_id not in event_handlers:
    if user_event_fname == 'accumulation':
      os.makedirs('%s/%s' % (user_event_dir, str(user_id)))
    event_handlers[user_id] = open('%s/%s/%s' % (user_event_dir, str(user_id), user_event_fname), 'w')
  event_handlers[user_id].write(event)

def _main( ):
  user_list = sys.argv[1]
  user_event_dir = sys.argv[2]
  video_event_analysis = sys.argv[3]
  f_o.open(video_event_analysis, 'w')
  f_o.write('\t'.join(['user_id', 'watch_time', 'n_played_videos', 'covered_video_time', 'watch_2_cover', 'f_seek', 'b_seek', 'n_speed_changes', 'avg_changed_speed']))

  users = analytics_util.load_users(user_list)
  for user in users:
    event_name = '%s/%d/accumulation' % (user_event_dir, user)
    if not os.path.isfile(event_name):
      continue

    backward_seek = 0 # replay
    forward_seek = 0
    played_video_id = None
    speed_changes = []
    real_start_time = None
    accumulated_real_watch_time = 0.0
    play_start_time = None
    played_videos = {}

    for line in open(event_name):
      if not analytics_util.filter_event(line, ['video']):
        continue
      event = json.loads(line)
      if 'event_type' not in event or 'event' not in event:
        continue

      event_info = json.loads(event['event'])
      try:
        if event['event_type'] in ['speed_change_video']:
          speed_changes.append(float(event_info['new_speed']))
        elif event['event_type'] in ['play_video', 'edx.video.played']:
          if not played_video_id or played_video_id != event_info['code']:
            if played_video_id:
              print line

            played_video_id = event_info['code']
            real_start_time = event['time']
            play_start_time = int(math.ceil(event_info['currentTime']))
        elif event['event_type'] in ['pause_video', 'edx.video.paused', 'stop_video', 'edx.video.stopped']:
          if played_video_id:
            if played_video_id != event_info['code']:
              print line
            else:
              accumulated_real_watch_time += analytics_util.time_diff(real_start_time, event['time'])
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
              print line
            else:
              play_end_time = int(old_time) + 1
              if play_end_time > play_start_time:
                if played_video_id not in played_videos:
                  played_videos[played_video_id] = []
                played_videos[played_video_id].append((play_start_time, play_end_time))
              play_start_time = int(math.ceil(new_time))
      except KeyError:
          print 'KeyError: ' + line

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
    f_o.write('%f\t' % (accumulated_real_watch_time/covered_video_time))
    # f_seek
    f_o.write('%d\t' % forward_seek)
    # b_seek
    f_o.write('%d\t' % backward_seek)
    # n_speed_changes
    f_o.write('%d\t' % len(speed_changes))
    # avg_changed_speed
    f_o.write('%f\n' % float(sum(speed_changes))/len(speed_changes) if len(speed_changes) > 0 else 0.0)

if __name__ == '__main__':
  _main( )
