#!/bin/bash
#
# script to update match data each night and then recalc any necessary orbits

here="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
source $here/../config/config.ini >/dev/null 2>&1

thismth=`date '+%Y%m'`
thisyr=`date '+%Y'`

source ~/.ssh/ukmonarchive-keys
export AWS_DEFAULT_REGION=eu-west-2
aws lambda invoke --function-name ConsolidateCSVs out --log-type Tail

${SRC}/matches/findAllMatches.sh ${thismth}
#${SRC}/orbits/doaMonth.sh ${thismth}
#${SRC}/website/createOrbitIndex.sh ${thismth}
#${SRC}/website/createOrbitIndex.sh ${thisyr}
${SRC}/analysis/updateRMSShowerAssocs.sh ${thismth}
${SRC}/website/createMthlyExtracts.sh ${thismth}
${SRC}/website/createShwrExtracts.sh ${thismth}

${SRC}/analysis/monthlyReports.sh ALL ${thisyr} force

dom=`date '+%d'`
if [ $dom -lt 10 ] ; then 
    lastmth=`date --date='-1 month' '+%Y%m'`
    lastyr=`date --date='-1 month' '+%Y'`

    ${SRC}/analysis/updateRMSShowerAssocs.sh ${lastmth}
    ${SRC}/website/createMthlyExtracts.sh ${lastmth}
    ${SRC}/website/createShwrExtracts.sh ${lastmth}
fi
${SRC}/website/createSummaryTable.sh

find $SRC/logs -name "nightly*" -mtime +7 -exec rm -f {} \;
