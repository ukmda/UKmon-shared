#!/bin/bash
here="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
source $here/../config.ini >/dev/null 2>&1
source $HOME/venvs/$WMPL_ENV/bin/activate

if [ "$1" != "" ] ; then
    rundate=$1
    logfile=$DATADIR/lastlogs/lastlog-${rundate}.html
else
    rundate=$(date +%Y%m%d)
    logfile=$DATADIR/lastlog.html
fi 

# create performance metrics
cd $SRC/logs
matchlog=$( ls -1 ${SRC}/logs/matches-*.log | tail -1)
python -m metrics.timingMetrics $matchlog 'M' >> $SRC/logs/perfMatching.csv

nightlog=$( ls -1 ${SRC}/logs/nightlyJob-*.log | tail -1)
python -m metrics.timingMetrics $nightlog 'N' >> $SRC/logs/perfNightly.csv


lastlog=$(ls -1tr $SRC/logs/nightlyJob-${rundate}-*.log | tail -1)
lastmtch=$(ls -1tr $SRC/logs/matches-${rundate}-*.log | tail -1)

egrep "nightlyJob|consolidateOutput|createMthlyExtracts|createShwrExtracts|createSearchable|createFireballPage|showerReport|reportYear|createSummaryTable|createLatestTable|stationReports" $lastlog > /tmp/logmsgs.txt
egrep "findAllMatches1|convertUfoToRms|getRMSSingleData|runDistrib" $lastmtch > /tmp/matchpt1.txt
egrep "findAllMatches2|updateIdexPages|createOrbitIndex" $lastmtch > /tmp/matchpt2.txt

python -m reports.findFailedMatches $rundate

cp $TEMPLATES/header.html $logfile
echo "<p>" >> $logfile
echo "Jump to:<p>" >> $logfile
echo "<li><a href=#correl>Correlation Results</a></li>" >> $logfile
echo "<li><a href=#uncal>Uncalibrated Data</a></li>" >> $logfile
echo "<li><a href=#fails>Match Fails</a></li>" >> $logfile
echo "<li><a href=/reports/lastlogs/index.html>Previous Logs</a></li>" >> $logfile
echo "</p>" >> $logfile

echo "<h2 id=batch>Batch Job Report</h2>" >> $logfile
echo "<p>This section shows the output of the daily batch.</p>">> $logfile
echo "<pre>" >> $logfile
head -2 /tmp/logmsgs.txt >> $logfile
cat /tmp/matchpt1.txt >> $logfile
cat /tmp/matchpt2.txt >> $logfile
len=$(wc -l /tmp/logmsgs.txt|awk '{print $1}')
len=$((len-2))
tail -$len /tmp/logmsgs.txt >> $logfile
echo "</pre>" >> $logfile

echo "<h2 id=correl>Correlator Report</h2>" >> $logfile
echo "<p>This section shows the output of the trajectory solver. ">> $logfile
echo "The first part lists any previous solutions for which potential new data were ">> $logfile
echo "available. Subsequent sections show the results of new solutions.</p>">> $logfile
echo "<pre>" >> $logfile
python -m reports.getSolutionStati $lastmtch >> $logfile
ls -1 $SRC/logs/distrib/$rundate*.log | while read i ; do
    python -m reports.getSolutionStati $i >> $logfile
done
echo "</pre>" >> $logfile

echo "<h2 id=uncal>Uncalibrated Data Report</h2>" >> $logfile
echo "<p>This section shows detections that were not included in the correlation run, ">> $logfile
echo "either because RMS was not able to recalibrate the detection or because ">> $logfile
echo "the entire night was uncalibrated (indicated by the 'skipping' warning).</p>">> $logfile
echo "<p>To interpret these data, see " >> $logfile
echo "<a href=https://github.com/markmac99/ukmon-pitools/wiki/UKMON-Pi-Toolset-FAQ#Interpreting_the_Uncalibrated_Report>here</a></p>" >> $logfile
echo "<pre>" >> $logfile
grep "Skipping" $lastmtch >> $logfile
echo "</pre>" >> $logfile

echo "<h2 id=fails>Failed Match Report</h2>" >> $logfile
echo "<p>This section shows groups of potential matches that could not be solved. ">> $logfile
echo "<p>To interpret these data, see " >> $logfile
echo "<a href=https://github.com/markmac99/ukmon-pitools/wiki/Trajectory-Solver-Failures>here</a></p>" >> $logfile
echo "<pre>" >> $logfile
cat $DATADIR/failed/${rundate}_failed.txt >> $logfile
echo "</pre>" >> $logfile

cat $TEMPLATES/footer.html >> $logfile
rm /tmp/matchpt1.txt /tmp/matchpt2.txt /tmp/logmsgs.txt

if [ ! -d $DATADIR/lastlogs ] ; then mkdir $DATADIR/lastlogs ; fi
if [ "$1" == "" ] ; then 
    aws s3 cp $logfile  $WEBSITEBUCKET/reports/ --quiet
    cp $logfile $DATADIR/lastlogs/lastlog-${rundate}.html
fi 
aws s3 cp $logfile  $WEBSITEBUCKET/reports/lastlogs/lastlog-${rundate}.html --quiet

cp $TEMPLATES/header.html $DATADIR/lastlogs/index.html
ls -1r $DATADIR/lastlogs/last*.html  | head -90 | while read i ; do
    bn=$(basename $i)
    echo "<a href=/reports/lastlogs/$bn>$bn</a><br>" >> $DATADIR/lastlogs/index.html
done
cat $TEMPLATES/footer.html >> $DATADIR/lastlogs/index.html
aws s3 cp $DATADIR/lastlogs/index.html  $WEBSITEBUCKET/reports/lastlogs/ --quiet
