#!/bin/bash

echo "This script will install the UKMON LIVE software"
echo "on your Pi. If you don't want to continue press Ctrl-C now"
echo " "
echo "You will need the location code, access key and secret provided by UKMON"
echo "If you don't have these press crtl-c and come back after getting them".
echo "nb: its best to copy/paste the keys from email to avoid typos."
echo " " 

read -p "continue? " yn
if [ $yn == "n" ] ; then
  exit 0
fi

echo "Installing the AWS CLI...."
sudo apt-get install -y awscli

mkdir ~/ukmon
echo "Installing the package...."
ARCHIVE=`awk '/^__ARCHIVE_BELOW__/ {print NR + 1; exit 0; }' $0`
tail -n+$ARCHIVE $0 | tar xzv -C ~/ukmon

CREDFILE=~/ukmon/.livecreds

if [ -f $CREDFILE ] ; then
  read -p "Credentials already exist; overwrite? (yn) " yn
  if [[ "$yn" == "y" || "$yn" == "Y" ]] ; then 
    redocreds=1
  else
    redocreds=0
  fi
else
  redocreds=1
fi

if [ $redocreds -eq 1 ] ; then 
  while true; do
    read -p "Location: " loc
    read -p "Access Key: " key
    read -p "Secret: " sec 
    echo "you entered: "
    echo $loc
    echo $key
    echo $sec
    read -p " is this correct? (yn) " yn
    if [[ "$yn" == "y" || "$yn" == "Y" ]] ; then 
      break 
    fi
  done 
    
  echo "Creating credentials...."
  echo "export AWS_ACCESS_KEY_ID=$key" > $CREDFILE
  echo "export AWS_SECRET_ACCESS_KEY=$sec" >> $CREDFILE
  if [ "LIVE" == "ARCHIVE" ] ; then 
    echo "export AWS_DEFAULT_REGION=eu-west-2" >> $CREDFILE
  else
    echo "export AWS_DEFAULT_REGION=eu-west-1" >> $CREDFILE
  fi
  echo "export loc=$loc" >> $CREDFILE
  chmod 0600 $CREDFILE
fi 
echo "Scheduling job..."
if [ "LIVE" == "ARCHIVE" ] ; then 
  crontab -l | grep archToUKmon.sh
  if [ $? == 1 ] ; then
    crontab -l > /tmp/tmpct
    echo "0 11 * * * /home/pi/ukmon/archToUKmon.sh >> /home/pi/ukmon/archiver.log 2>&1" >> /tmp/tmpct
    crontab /tmp/tmpct
    \rm -f /tmp/tmpct
  fi 
else
  crontab -l | grep liveMonitor.sh > /dev/null
  if [ $? == 1 ] ; then
    crontab -l > /tmp/tmpct
    echo "@reboot sleep 3600 && /home/pi/ukmon/liveMonitor.sh >> /home/pi/ukmon/monitor.log 2>&1" >> /tmp/tmpct
    crontab /tmp/tmpct
    \rm -f /tmp/tmpct
  fi 
fi
echo ""
echo "done"
exit 0

__ARCHIVE_BELOW__
� ���^ �W�O�H�y����:$��I���T�W$����D�w�a{��:�R��߬����r}��I�{���=�ݙM.f�H�BKկ��'���F��G��������A}�_C�(���{�t>GS�X�U��z����X�Ž�{�!��
�3o�N �SH�q�-dI��F�����|tQ��:vQP��;1� :9*!��!5!I\1���T�
�.Z��c�����Kظ��(58��Ƅ�$��d<���#����[ڽ# W��9(0%���$�Z�1L��]V%U�E? o9��-�hk"R�����\��% M˸�����~Q����� h*��A�p�0�~���|�)W��}t��B�n�����e̸9��t_�]�ʩh��W�N2��0��e�K��7P��Ҙ�S��B�"?{C[|��!O��za��ǡ�c����������_�F%|�<�fo$���N2�v��8f����Q�W-�tQ�6���ܲ�s���;U@/]�q7	I��1�)�L�/I�}�U4}k�!USgY]�f�j�3YB��3-���iS��Z���?ՔT�bK7w��a�5�`�c�����RT5�3�	+��f�M<3��hpX�����c@�)�A0!L]<����bb'/P�SDd����A��P��HF�s�? ��MH����o�w!�L��? i㐒_�ёs����s����<��[R��:��x��YK\@}�5xQ����E��k�KQ�o�v޸��\ݺ�k�����+�)�y��y�:ln�W��P+S������*	�v�����ܐ��.�!��mhL˝R�ë�u��ɂ����z fg����-�3陳���k��������>U�����k��G��?Rcoh�0l��x����W5^�#��=
�L$�]D�N�{�(��&/�T��Q7���]*vg�#
�3I[m�#Q<������2�ǐBQ<��ȧ�*l��1`n���T���9��H������b�M���!��:�� 9	f1��BO�������?":@�t�b�0QI�P�x�1���|ѡQ�%��yQs��G�X!��pM�靖���ႵY�Ԇ�{?Wy��䋋�-�)Y��7\k��bo�{������������������������ſ� (  