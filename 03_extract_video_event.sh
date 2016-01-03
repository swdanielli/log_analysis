#!/bin/bash

groups=("dis_no_rec" "no_dis_no_rec" "dis_rec" "no_dis_rec")
#groups=("dis_no_rec")

#for group in "${groups[@]}"
#do
#  user_list=$group"/user_list"
#  user_event_dir=$group"/event_by_user"
#  video_event_analysis_dir=$group"/video_event_analysis"
#  mkdir $video_event_analysis_dir

#  ./script/extract_video_event.py $user_list $user_event_dir $video_event_analysis_dir
#done

for group in "${groups[@]}"
do
  user_list=$group"/user_list"
  user_event_dir=$group"/event_by_user"
  part_of_lecture='lecture_2'
  video_event_analysis_dir=$group"/video_event_analysis/"$part_of_lecture

  mkdir $video_event_analysis_dir

  ./script/extract_video_event.py $user_list $user_event_dir $video_event_analysis_dir $part_of_lecture
done
