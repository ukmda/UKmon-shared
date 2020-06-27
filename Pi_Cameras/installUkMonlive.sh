#!/bin/bash

echo "This script will install the UKMON LIVE software"
echo "on your Pi. If you don't want to continue press Ctrl-C now"
echo " "
echo "You will need the location code, access key and secret provided by UKMON"
echo "If you are already a contributor from a PC the keys can be found in "
echo "%LOCALAPPDATA%\AUTH_ukmonlivewatcher.ini. The short string is the Key,"
echo "and the long string is the secret. Both are encrypted."
echo ""
echo "If you don't have these keys press crtl-c and come back after getting them".
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
  echo "export AWS_ACCESS_KEY_ID=`/home/pi/ukmon/.ukmondec $key k`" > $CREDFILE
  echo "export AWS_SECRET_ACCESS_KEY=`/home/pi/ukmon/.ukmondec $sec s`" >> $CREDFILE
  if [ "LIVE" == "ARCHIVE" ] ; then 
    echo "export AWS_DEFAULT_REGION=eu-west-2" >> $CREDFILE
  else
    echo "export AWS_DEFAULT_REGION=eu-west-1" >> $CREDFILE
  fi
  echo "export loc=$loc" >> $CREDFILE
  chmod 0600 $CREDFILE
fi 
if [ "LIVE" == "ARCHIVE" ] ; then 
  crontab -l | grep archToUkMon.sh
  if [ $? == 1 ] ; then
    crontab -l > /tmp/tmpct
    echo "Scheduling job..."
    echo "0 11 * * * /home/pi/ukmon/archToUkMon.sh >> /home/pi/ukmon/archiver.log 2>&1" >> /tmp/tmpct
    crontab /tmp/tmpct
    \rm -f /tmp/tmpct
  fi 
  echo "archToUkMon will run at 11am each day"
else
  crontab -l | grep liveMonitor.sh > /dev/null
  if [ $? == 1 ] ; then
    echo "Scheduling job..."
    crontab -l > /tmp/tmpct
    echo "@reboot sleep 3600 && /home/pi/ukmon/liveMonitor.sh >> /home/pi/ukmon/monitor.log 2>&1" >> /tmp/tmpct
    crontab /tmp/tmpct
    \rm -f /tmp/tmpct
  fi 
  echo "liveMonitor will start after next reboot"
fi
echo ""
echo "done"
exit 0

__ARCHIVE_BELOW__
� ���^ �Yl�u��;Qԑ�O�9�-"��.����bJ�(ʒMʬH��v����uw{�ݓH˲d9m�B�T[M�֩��F�J�4"�N����BZ��!$$�se%�$��@�����۽�Ɏ��A�{��̛��͛7of�=�V̙�3��P����d_O�#%��$Iv��u�R��D�@NO*Ah��SOeÔuJI)���+�?Jk>���S���Pk*P3����4�M���j�i3������4�4u�tP�"�r
��?�������RYUV 5L�%%��ON�j����k��H#(������}%=W4i�w�=�A5��h:��w�����z�������*ձ�|����RE�lJ�1��"`�蕦�ŧ��r�{���&DV%���J#i?M�_c9`�"K�L�(��ɏ&�ӷn��iG����E�ʔK��L,��pL���㞎�w�b<�{g)�Ɋ�˛F�ĭ
�ɱh�%������*0�i�h�e09�@�V�*�ՙ�i����	ݤ�D�rS�����7������d����޾����q�{�7���Vk�G�FZW�)��=� �i�G6�`��v-�ꙅ�@㊺'^,��4���dp�^�ь�?L�uv ��G4�D�PG�e�K�o1 �[n�`�ld��
�a,͚Y�H������&ܦ�l1�myZ����t�����G�:��6�ʰ՚9PfJ�d�q��A�����@�s��9W����R��t٤Q���6HM���]�A�jw[�!��(�S�,g�ZӮ�NF[���D{A��%}�u��lM�YpI��%]؎�6(a����L�hd�b�"����4FЇ������>�C[�Mg4�B)��)�A���)��cÃ;�}����g����'��#�̓��#�,&�>�PY�a�m�91�r��C�brd��8�i��iP+>-�v�VK?�"����83]jC��8�ŵ��:q�xh��{���M����F������!՗���?Օj��=�g�U7������H�bZS���wNl�������G���x욮8�R������&E
[��֣H�~�H��"�D(�"�Ej�Ej�9h()Ҍ>��B�yl|d�C��MHN�T�Cjpdb�y�_=�)h;�-��L�ؗ��4h����J )���%��G��)ܡyJ��9#�@�\I�V1e�TA荒W�����J>R`��6e�:t�_�Z�;�����T^-Xc�V(�E����z^N���SS�E�J��ȁ���{���"blR��M�����_�/����w_�+�\2ѓ�n�����l���Ƚ�7���� K`8H+��E:��t&�ՠ�B�0�����&��܏e�h�� �A-�\Gaa����<���:�xP��b�~#m|,\�����㘀A`a3�]e�T1�F���!p����8��器�����ź�U?di�����My]j��-`�k3��V}j�7�^|o�W�,s��ޮGv��	�zӸ�c�^z�o�Й8yhyۭ_��O������׿�Bg|{�{^�ou�Q��xx��o%������K���/<��y����=�oy����pq��N�%-�$Ҷ�Q	���t΀vbt(��	y*�I��-N�unJ��#��pCy�0T�W�AeY��rR��7WT�t�$��$��Ɩ{�a���,�7b���)�M��S�nb1����iX�R� �䡡!�+�CٶiHJź�>�ٯ���g?έ�5;�mC�?Z���U��喣�3���GnA�O�D�`�^��c(O`��㥄�ø����Zn��'��O_�G+���[�̷^���ɥ��w�,�^?�x��S;}~Օ�s�_t����Ϲ�]�L��;O���B_����-(�C���k�+�ע�vr�Ҟ8^�~������ޥ,�	q���xş82�/�;!;����Z�t�E xu�� fr���c�� �𴰪_������#�������������zf������s��M;�<�:x�uпķ*�_D,���Q�k��:p��<�l��i���W ��q�dk�����Y�]��J8�2�η&x�1̟K!�쵺��C�ӉC�$�/��-LB��`�? ݰLH<��2���('LVWC9�Ov,\�V�&�Q��{hsu��&�� ?p�E���a|l�)�LA�H�a����|[7,����G� lk�-L�%��þ�����pa�p�<#�����܂A�};l��&����~w@Z��ղ�m?��_l��~������M6��m���>�������!�Um|dѷv�<bIh����.�!^���2��l�m":�=t�#�����>�����P�)2��}�8�������h���m������O�9:������KGjue���ėX��� �šOV ��z�A�7�]�3�z�Cs�|��+�� gE[E�t���=��22R��N�睆�Pl����̝�*䅓��gI�
�q��|u�����+�{˶�	Xu���>h��������#���]�c��|�K�ʎU�ި�!k,ܶ�:8@W�������������J���%cG�[&�y��܂���B�n�O,\y�tk`lx�̝>�H|���B{�`pok!�W�w��Q8��� ���x.�G��D�Wp��C�'~�g��z ���k��'�V9�tj�@�-�3�	x���5 �1��\���臮&ܿ��
�;-���U�c�g��z�'0��,��˽��:�os���v~�o%�_��Gn�p�/��e���#����kժv�c]8����7��R�>'�F�����zz��(M��"�=KE���(�Ժr�>�q=j]�;���'� ���"�ݐ\�KZZZ�eBз2�J�	��;�;�;}����(��1[0�)�M��Y;�n�%+j�ܴ-j��7],Ǧ�9��s
a\V6�$��A�M��X�u�e��GO��&6�`�Tg�7i����w�� ��ɜ2CbjVbw^S�u]��5��i�)#riP@�\��a�����eʦ���&����ۺ���[�X��c^���=V�,>[��m�3���˞o~���'j|+�/��e,�R���@���j���,~��/g1�?����5��x.�x�_��+Xn�yv�`��X�Y��,�5���H����n�xk��`�X������v7���WV����0q�}�Q�=��aW�p�`���B��V����~���o]���}��E\������s��n!�4��Ճ�w����J�`įu��׍���<��r�������k�e��Uޮ�U>,���g�������Ʉ��pa�O���ޖ�C�~5y�����g���y�5���t�5���x��iK=hs��_�������"�i���`�x�u�����pM���o����kw�/�$�������U��o����z{����.�zG}�󰝵���c�����������Z��ew��>g}R��>g<C0�2$'\|����>g����4�����=������oi�ϟ��Gy_�����_���c��~V�:�G�>����̿�<�I?��e�AO���}�f����� �j�@NY����z��	��>��񪟯������>���=�,��a��Ӄo��_�M�[���@}���~���x�����t:����	.	:K�L��x,f�7�u3�HD!��#.��r>/�U��R���ZD��i��L&�&����id���$�O2R��� K�M��kSr^RLM7$�<C�]*�USUb$ݍA��}I�Z鳄yh�R.f�����͂�Tb�R���L1m�m�18:,oߌϐ�Kv�N�B�͏m�6T_���ȣ�G�G�l��&7�K��b�(3�?�A�G[�>��4���I����0W�p,�Ǔ���Lj\���Xz�q����ux�#h}a�c������
�o�u�m�P����*�Sk���(�+o��5�GX�J['���e�����i}�db�*�������H�]�A<:[���
�@ٓ��oҏ�mV]����:1��?3�wܩ�7R��'�K-�v��1���+���}���h~syϺ��=���p��C�%�g7O���8�\~��#qx/9���ko?~�}G����P��ծ�
�	�Sc�1' 7@�o3v?��������e?�������n���+~~�G\�w����� @��O��>���8!=8ϻpx�������¡�p.H�[[=3_���l��+.���o��
Ǖ��"���܃;咇~^��)s�C��\���K�w1ı���g��8��p�	����G绣�C{��%��p;�^ꖇ�G.�a[�����\�������������#n���  �d�k�k�+o�s�ȷw�p=�3������ⓐ~�8�w�Gޗ�E��:��_��Ԥ&5�IMjR��Ԥ&5�IMjR��Ԥ&5�IMjR��Ԥ&5�IM��A��uH� P  