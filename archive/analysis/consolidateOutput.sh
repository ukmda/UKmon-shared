#!/bin/bash
#
# consolidate the raw RMS and UFO data. 
#
# Parameters:
#   year to process
#
# Consumes:
#   single-station data preprocessed by getRMSSingleData.sh (which includes converted UFO data)
#   csv and extracsv files created by the matching engine 
#
# Produces:
#   Updated consolidated ukmon single-event CSV file in standard UFO R91 format
#   Updated matched data files (matches-{yr} and matches-extras-{yr})
#   
# The outputs are used for downstream processing and reporting

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
        echo $bn $mrgfile
        sed '1d' $csvf >> $mrgfile
        rm $csvf
    fi
done

logger -s -t consolidateOutput "pushing consolidated information back"
source $UKMONSHAREDKEY
aws s3 sync ${DATADIR}/consolidated s3://ukmon-shared/consolidated/  --quiet --exclude 'UKMON*'

# this creates an R91 compatible file with four extra columns which UFO Orbit ignores
#logger -s -t consolidateOutput "Getting latest ukmon-format data"
#python -m converters.UKMONtoUFOR91 ${yr} $DATADIR/UKMON-all-single.csv
# no longer used for anything
 
logger -s -t consolidateOutput "Getting latest trajectory data"

# collect the latest trajectory CSV files
# make sure target folders exist
if [ ! -d ${DATADIR}/orbits/$yr/csv/ ] ; then
    mkdir -p ${DATADIR}/orbits/$yr/csv/processed/
    mkdir -p ${DATADIR}/orbits/$yr/extracsv/processed/
fi
# get the list of orbits
dailyrep=$(ls -1tr $DATADIR/dailyreports/20* | tail -1)
trajlist=$(cat $dailyrep | awk -F, '{print $2}')

# copy the orbit file for consolidation and reporting
for traj in $trajlist 
do
    cp $traj/*orbit.csv ${DATADIR}/orbits/$yr/csv/
    cp $traj/*orbit_extras.csv ${DATADIR}/orbits/$yr/extracsv/
done

# get the latest matched data generated by WMPL
logger -s -t consolidateOutput "getting matched detections for $yr"
if [ ! -f ${DATADIR}/matched/matches-$yr.csv ] ; then 
    cp $here/templates/UO_header.txt ${DATADIR}/matched/matches-$yr.csv
    mkdir ${DATADIR}/orbits/${yr}/csv/processed > /dev/null 2>&1
fi
cat ${DATADIR}/orbits/$yr/csv/$yr*.csv >> ${DATADIR}/matched/matches-$yr.csv
mv ${DATADIR}/orbits/$yr/csv/$yr*.csv ${DATADIR}/orbits/${yr}/csv/processed

logger -s -t consolidateOutput "getting extra orbit data for $yr"
if [ ! -f ${DATADIR}/matched/matches-extras-$yr.csv ] ; then 
    cp $here/templates/extracsv.txt ${DATADIR}/matched/matches-extras-$yr.csv
    mkdir ${DATADIR}/orbits/${yr}/extracsv/processed > /dev/null 2>&1
fi
cat ${DATADIR}/orbits/$yr/extracsv/$yr*.csv >> ${DATADIR}/matched/matches-extras-$yr.csv
mv ${DATADIR}/orbits/$yr/extracsv/$yr*.csv ${DATADIR}/orbits/${yr}/extracsv/processed

python << EOD
import pandas as pd 
df = pd.read_csv('${DATADIR}/matched/matches-${yr}.csv')
df = df.drop_duplicates()
df.to_csv('${DATADIR}/matched/matches-${yr}.csv', index=False)
EOD
python << EOD2
import pandas as pd 
df = pd.read_csv('${DATADIR}/matched/matches-extras-${yr}.csv')
df = df.drop_duplicates()
df.to_csv('${DATADIR}/matched/matches-extras-${yr}.csv', index=False)
EOD2
logger -s -t consolidateOutput "consolidation done"

