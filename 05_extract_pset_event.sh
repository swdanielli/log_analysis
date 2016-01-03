#!/bin/bash

groups=("dis_no_rec" "no_dis_no_rec" "dis_rec" "no_dis_rec")
#groups=("test")

#for group in "${groups[@]}"
#do
#  user_list=$group"/user_list"
#  user_event_dir=$group"/event_by_user"
#  pset_event_analysis_dir=$group"/pset_event_analysis"
#  mkdir $pset_event_analysis_dir

#  ./script/extract_pset_event.py $user_list $user_event_dir $pset_event_analysis_dir
#done

lectures=("all" "lecture_2")
for group in "${groups[@]}"
do
  user_list=$group"/user_list"
  user_event_dir=$group"/event_by_user"
  prac_pset_event_analysis_dir=$group"/prac_pset_event_analysis"
  mkdir $prac_pset_event_analysis_dir

  for part_of_lecture in "${lectures[@]}"
  do
    mkdir $prac_pset_event_analysis_dir/$part_of_lecture

    ./script/extract_prac_pset_event.py $user_list $user_event_dir $prac_pset_event_analysis_dir/$part_of_lecture $part_of_lecture
  done
done

