#!/bin/bash

# bash script to create index page for an individual orbit report

here="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

source $here/../config/config.ini >/dev/null 2>&1
logger -s -t createPageIndex "starting"
cd $SRC/orbits
source ~/venvs/$WMPL_ENV/bin/activate
export PYTHONPATH=$wmpl_loc:$PYLIB
export ARCHDIR # used by extraDataFiles.py
logger -s -t createPageIndex "generate extra data files and copy other data of interest"
python $PYLIB/traj/extraDataFiles.py $1
cd $here

logger -s -t createPageIndex "generating orbit page index.html"
ym=$(basename $1)
yr=${ym:0:4}
mth=${ym:0:6}
ymd=${ym:0:8}
targ=${WEBSITEBUCKET}/reports/${yr}/orbits/${mth}/${ymd}/$ym

#Examples of arg1
#/home/ec2-user/ukmon-shared/matches/RMSCorrelate/trajectories/20211009_043016.566_UK
#/home/ec2-user/ukmon-shared/matches/RMSCorrelate/trajectories/2021/202101/20210131/20210131_052556.356_UK
srcdata=$1

idxfile=${srcdata}/index.html
repf=$(ls -1 ${srcdata}/$yr*report.txt)
repfile=$(basename $repf)
pref=${repfile:0:16}

fldr=$(basename $srcdata)

cp $TEMPLATES/header.html $idxfile
echo "<h2>Orbital Analysis for matched events on $ym</h2>" >> $idxfile
echo "<a href=\"../index.html\">Back to daily index</a><hr>" >> $idxfile
echo "<pre>" >> $idxfile
cat ${srcdata}/summary.html >> $idxfile
echo "Click <a href=\"./$fldr.zip\">here</a> to download a zip of the raw and processed data." >> $idxfile
echo "</pre>" >>$idxfile
echo "<p><b>Detailed report below graphs</b></p>" >>$idxfile
echo "<h3>Click on an image to see a larger view</h3>" >> $idxfile

echo "<div class=\"top-img-container\">" >> $idxfile
echo "<a href=\"${pref}orbit_top.png\"><img src=\"${pref}orbit_top.png\" width=\"20%\"></a>" >> $idxfile
echo "<a href=\"${pref}orbit_side.png\"><img src=\"${pref}orbit_side.png\" width=\"20%\"></a>" >> $idxfile
echo "<a href=\"${pref}ground_track.png\"><img src=\"${pref}ground_track.png\" width=\"20%\"></a>" >> $idxfile
echo "<a href=\"${pref}velocities.png\"><img src=\"${pref}velocities.png\" width=\"20%\"></a>" >> $idxfile
echo "<br>">>$idxfile
\rm ${srcdata}/available_jpgs.txt
if [ -f ${srcdata}/jpgs.lst ] ; then
    cat ${srcdata}/jpgs.lst | while read i 
    do
        echo "<a href=\"/$i\"><img src=\"/$i\" width=\"20%\"></a>" >> $idxfile
        echo "https://archive.ukmeteornetwork.co.uk/$i" >> ${srcdata}/available_jpgs.txt
    done
fi
\rm ${srcdata}/jpgs.lst
echo "<a href=\"${pref}lengths.png\"><img src=\"${pref}lengths.png\" width=\"20%\"></a>" >> $idxfile
echo "<a href=\"${pref}lags_all.png\"><img src=\"${pref}lags_all.png\" width=\"20%\"></a>" >> $idxfile
echo "<a href=\"${pref}abs_mag.png\"><img src=\"${pref}abs_mag.png\" width=\"20%\"></a>" >> $idxfile
echo "<a href=\"${pref}abs_mag_ht.png\"><img src=\"${pref}abs_mag_ht.png\" width=\"20%\"></a>" >> $idxfile
echo "<a href=\"${pref}all_angular_residuals.png\"><img src=\"${pref}all_angular_residuals.png\" width=\"20%\"></a>" >> $idxfile
echo "<a href=\"${pref}all_spatial_total_residuals_height.png\"><img src=\"${pref}all_spatial_total_residuals_height.png\" width=\"20%\"></a>" >> $idxfile
echo "</div>" >> $idxfile

echo "<pre>" >>$idxfile 
cat $repf >>$idxfile
echo "</pre>" >>$idxfile
echo "<br>">>$idxfile

echo "<script> \$('.top-img-container').magnificPopup({ " >> $idxfile
echo "delegate: 'a', type: 'image', image:{verticalFit:false}, gallery:{enabled:true} }); " >> $idxfile
echo "</script>" >> $idxfile

cat $TEMPLATES/footer.html >> $idxfile

logger -s -t createPageIndex "adding zip file"
pushd ${srcdata}
zip -r -9 /tmp/$fldr.zip . -x ./$fldr.zip --quiet
cp /tmp/$fldr.zip ${srcdata}/
rm -f /tmp/$fldr.zip
popd

logger -s -t createPageIndex "copying to website"
source $WEBSITEKEY
aws s3 sync ${srcdata}/ ${targ}/ --include "*"  --quiet

logger -s -t createPageIndex "finished"
