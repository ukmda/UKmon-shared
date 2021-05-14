#!/bin/bash
here="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

source $here/../config/config.ini >/dev/null 2>&1

logger -s -t createSummaryTable "starting"
cd $here/../analysis
echo "\$(function() {" > $here/data/summarytable.js
echo "var table = document.createElement(\"table\");" >> $here/data/summarytable.js
echo "table.className = \"table table-striped table-bordered table-hover table-condensed\";" >> $here/data/summarytable.js
echo "var header = table.createTHead();" >> $here/data/summarytable.js
echo "header.className = \"h4\";" >> $here/data/summarytable.js

yr=$(date +%Y)
until [ $yr -lt 2013 ]; do
    if [ $yr -gt 2019 ] ; then 
        detections=$(grep "OTHER Matched" $SRC/logs/ALL$yr.log | awk '{print $4}')
    else
        detections=`cat $DATADIR/consolidated/M_${yr}-unified.csv | wc -l`
    fi
    matches=`grep "UNIFIED Matched" $SRC/logs/ALL${yr}.log  | awk '{print $4}'`
    fireballs=`tail -n +2 $DATADIR/reports/$yr/ALL/TABLE_Fireballs.csv |wc -l`
    echo "var row = table.insertRow(-1);" >> $here/data/summarytable.js
    echo "var cell = row.insertCell(0);" >> $here/data/summarytable.js
    echo "cell.innerHTML = \"<a href="/reports/$yr/ALL/index.html">$yr</a>\";" >> $here/data/summarytable.js
    echo "var cell = row.insertCell(1);" >> $here/data/summarytable.js
    echo "cell.innerHTML = \"$detections\";" >> $here/data/summarytable.js
    echo "var cell = row.insertCell(2);" >> $here/data/summarytable.js
    echo "cell.innerHTML = \"<a href="/reports/$yr/orbits/index.html">$matches</a>\";" >> $here/data/summarytable.js
    echo "var cell = row.insertCell(3);" >> $here/data/summarytable.js
    echo "cell.innerHTML = \"$fireballs\";" >> $here/data/summarytable.js
    ((yr=yr-1))
done
echo "var row = header.insertRow(0);" >> $here/data/summarytable.js
echo "var cell = row.insertCell(0);" >> $here/data/summarytable.js
echo "cell.innerHTML = \"Year\";" >> $here/data/summarytable.js
echo "cell.className = \"small\";" >> $here/data/summarytable.js
echo "var cell = row.insertCell(1);" >> $here/data/summarytable.js
echo "cell.innerHTML = \"Detections\";" >> $here/data/summarytable.js
echo "cell.className = \"small\";" >> $here/data/summarytable.js
echo "var cell = row.insertCell(2);" >> $here/data/summarytable.js
echo "cell.innerHTML = \"Matches\";" >> $here/data/summarytable.js
echo "cell.className = \"small\";" >> $here/data/summarytable.js
echo "var cell = row.insertCell(3);" >> $here/data/summarytable.js
echo "cell.innerHTML = \"Fireballs\";" >> $here/data/summarytable.js
echo "cell.className = \"small\";" >> $here/data/summarytable.js

echo "var outer_div = document.getElementById(\"summarytable\");" >> $here/data/summarytable.js
echo "outer_div.appendChild(table);" >> $here/data/summarytable.js
echo "})" >> $here/data/summarytable.js

logger -s -t createSummaryTable "create a coverage map from the kmls"
source ~/venvs/${RMS_ENV}/bin/activate
python $PYLIB/utils/makeCoverageMap.py $CONFIG/config.ini $ARCHDIR/kmls $here/data

logger -s -t createSummaryTable "Add last nights log file to the website"
cp $TEMPLATES/header.html /tmp/lastlog.html
echo "<pre>" >> /tmp/lastlog.html
lastlog=$(ls -1tr $SRC/logs/matches | tail -1)
cat $SRC/logs/matches/$lastlog >> /tmp/lastlog.html
echo "</pre>" >> /tmp/lastlog.html
cat $TEMPLATES/footer.html >> /tmp/lastlog.html

logger -s -t createSummaryTable "copying to website"
source $WEBSITEKEY
aws s3 cp $here/data/summarytable.js  $WEBSITEBUCKET/data/ --quiet
aws s3 cp $here/data/coverage.html  $WEBSITEBUCKET/data/ --quiet
aws s3 cp /tmp/lastlog.html  $WEBSITEBUCKET/reports/ --quiet

logger -s -t createSummaryTable "finished"