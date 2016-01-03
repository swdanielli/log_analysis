#!/bin/bash

base_dir='/scratch/600x_2015/600x/MITx-6.00.1x_7_3T2015'
database_dir=$base_dir"/database"
database_condition=$database_dir"/MITx-6.00.1x_7-3T2015-user_api_usercoursetag-prod-analytics.sql"
database_grades=$database_dir"/MITx-6.00.1x_7-3T2015-certificates_generatedcertificate-prod-analytics.sql"

user_list='user_list'
inactive_user_list='inactive_user_list'

./script/split_learner.py $database_condition $database_grades $user_list $inactive_user_list

