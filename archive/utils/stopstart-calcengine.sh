#!/bin/bash
# Copyright (C) 2018-2023 Mark McIntyre

# script to create RMS shower association details if not already present
here="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
source $here/../config.ini >/dev/null 2>&1

aws ec2 $1-instances --instance-ids $SERVERINSTANCEID --region eu-west-2 --profile ukmonshared
