#!/bin/bash
#
# consolidate the raw RMS and UFO data. 
#
# Parameters:
#   year to process
#
# Consumes:
#   R05B25 and R91 csv files uploaded from cameras
#   csv files created by the matching engine 
#
# Produces:
#   Updated consolidated ukmon single-event CSV file in standard UFO formats
#   Updated matched data files matches-full-{yr}
#   
# The data are used for downstream processing and reporting

here="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
source $here/../config/config.ini >/dev/null 2>&1
source $HOME/venvs/${WMPL_ENV}/bin/activate

yr=$1
if [ "$yr" == "" ] ; then
    yr=$(date +%Y)
fi 

cd ${DATADIR}
# consolidate UFO and RMS original CSVs.
logger -s -t consolidateOutput "getting latest consolidated information"
source $UKMONSHAREDKEY
aws s3 sync s3://ukmon-shared/consolidated/ ${DATADIR}/consolidated --quiet --exclude 'temp/*'

logger -s -t consolidateOutput "Consolidating RMS and UFO CSVs"
consdir=$ARCHDIR/../consolidated/temp
ls -1 $consdir/*.csv | while read csvf
do
    bn=$(basename $csvf)
    typ=${bn:0:3}
    if [ "$typ" != "M20" ] ; then 
        pref="P"
        yr=${bn:7:4}
    else
        pref="M"
        yr=${bn:1:4}
    fi 
    mrgfile=$DATADIR/consolidated/${pref}_${yr}-unified.csv
    if [ ! -f $mrgfile ] ; then
        cat $csvf >> $mrgfile
    else
        #echo $bn $mrgfile
        sed '1d' $csvf >> $mrgfile
        rm $csvf
    fi
done

logger -s -t consolidateOutput "pushing consolidated information back"
source $UKMONSHAREDKEY
aws s3 sync ${DATADIR}/consolidated s3://ukmon-shared/consolidated/  --quiet --exclude 'UKMON*'
 
logger -s -t consolidateOutput "Getting latest trajectory data"

# collect the latest trajectory CSV files
# make sure target folders exist
mkdir -p ${DATADIR}/orbits/$yr/fullcsv/processed/ > /dev/null 2>&1

# copy the orbit file for consolidation and reporting
mv ${MATCHDIR}/${yr}/fullcsv/*.csv ${DATADIR}/orbits/${yr}/fullcsv/

# get the latest matched data generated by WMPL
logger -s -t consolidateOutput "getting matched detections for $yr"
if [ ! -f ${DATADIR}/matched/matches-full-$yr.csv ] ; then 
    cp $here/templates/match_hdr_full.txt ${DATADIR}/matched/matches-full-$yr.csv
    mkdir ${DATADIR}/orbits/${yr}/fullcsv/processed > /dev/null 2>&1
fi
cat ${DATADIR}/orbits/$yr/fullcsv/$yr*.csv >> ${DATADIR}/matched/matches-full-$yr.csv
mv ${DATADIR}/orbits/$yr/fullcsv/$yr*.csv ${DATADIR}/orbits/${yr}/fullcsv/processed

python << EOD3
import pandas as pd 
df = pd.read_csv('${DATADIR}/matched/matches-full-${yr}.csv', skipinitialspace=True)
df = df.drop_duplicates(subset=['_mjd','_sol','_ID1','_ra_o','_dc_o','_amag','_ra_t','_dc_t'])
df.to_csv('${DATADIR}/matched/matches-full-${yr}.csv', index=False)
EOD3

python -m converters.toParquet $DATADIR/matched/matches-full-${yr}.csv

source $UKMONSHAREDKEY
aws s3 sync $DATADIR/matched/ $UKMONSHAREDBUCKET/matches/matched/ --quiet --include "*" --exclude "*.gzip" --exclude "*.bkp"
aws s3 sync $DATADIR/matched/ $UKMONSHAREDBUCKET/matches/matchedpq/ --quiet --exclude "*" --include "*.gzip" --exclude "*.bkp"

logger -s -t consolidateOutput "consolidation done"
