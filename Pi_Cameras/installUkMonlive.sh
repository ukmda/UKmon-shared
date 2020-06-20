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
� !)�^ �W�O�8��Ŝ�	i7��WE*�+�S���zbC�l|$qd;[J��'t�-�=N��a3��q�o.f�@��H���ʓ��������E��J���a8z�
r�aozO��ר���J%�������_�3Q�g��Y��� &����r9��7<1B�9i4�5t�೏Z�,6��mֻ���X䨄T�c�Ԅ$qń�&S�+��h�����S�kT�/�a��R�4����&�'��$�ɹ(��i���p�����sQrx	L"�qA=ˤ��fP`UR��	x��̀n@�6&"���{���R6�i<����;�lm�����.��z ���vی��r���g�>/d��x�O�\ƌ��^���F9�c����El���'LdiDY㒣�5Tb��&���0_����~wvȓ�x�������F�qo`��h���3�����U�ͣk�F�8ӄ��6�S-���`|�g~Y�9����*��.���$�j�>�ئN�g��FRasjmsZvAHU�!���NR�M&K�pbD����^��k�^O�WY�SMI%+�ps�y�� N/1�S#0�E�qf)NXy;�ֻ��v��aV����(Hj�����̷��	1߱܌<l��qT������|1H���ɰ3��HƝ�-��b��]�$}G�$MR�4:𮘹>��Las���pM�YS�we���k�hn�/��C���ѵ�����������������o|���e{�ﱹ%߼=A�L5:{�'�;�$����ﾧ�%���}�($�Ҙ�?����w�M~6B��vg.����5�����k����<'���?U��G����?v��n�����?�^��:�J��>�A�G���dx�����n��כ�U�J�<�Z�S��K�n��`HaQ{\)`7��Q��"��BQ{HQ���R���I�(��
��Y���m���?��R[������=��Q̳1v8��\Ft"'�,��:��S8����������ͻ���DC�CT�F��9�հ��":��-���`� �4WX~D�r�,����y���yȢॱ$�����7%���M!Lɪ)߾�Z��{�yv��e�k (  