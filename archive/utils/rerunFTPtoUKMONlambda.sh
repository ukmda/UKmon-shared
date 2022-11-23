#!/bin/bash

# reads from $DATADIR/single/new/processed to find list of files

dt=$1
if [ "$dt" == "" ] ; then echo "need date" ; exit ; fi 
if [ -f ./ftp2ukmon.txt ] ; then rm ./ftp2ukmon.txt ; fi

# create list of ftpdetect files to reprocess
ls -1 $SRC/data/single/new/processed/*${dt}*.csv | while read i 
do 
	fn=$(basename $i)
	sid=${fn:6:6}
	dtdir=${fn:6:29}
	ftpn=$(echo $fn | sed 's/ukmon/FTPdetectinfo/g;s/csv/txt/g')
	echo matches/RMSCorrelate/$sid/$dtdir/$ftpn >> ./ftp2ukmon.txt
done 

# reprocess them 
cat ftp2ukmon.txt | while read i
do
	fullname=${i}
	cat cftpd_templ.json | sed "s|KEYGOESHERE|${fullname}|g" > tmp.json
	aws lambda invoke --profile ukmonshared --function-name ftpToUkmon --log-type Tail  --payload file://./tmp.json  --region eu-west-2 --cli-binary-format raw-in-base64-out res.log
done



