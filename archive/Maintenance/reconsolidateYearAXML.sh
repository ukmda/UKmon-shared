#!/bin/bash

# script to reconsolidate the A.XML files for a whole year
#!/bin/bash
here="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

if [[ "$here" == *"prod"* ]] ; then
    source $HOME/prod/config/config.ini >/dev/null 2>&1
else
    source $HOME/src/config/config.ini >/dev/null 2>&1
fi

if [ $# -eq 0 ]; then
    yr=$(date +%Y)
else
    yr=$1
fi

for j in {01,02,03,04,05,06,07,08,09,10,11,12} ;
do
    $here/findAllMatches.sh ${yr}${j}
done
