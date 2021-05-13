#!/bin/bash
here="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
source $here/../config/config.ini >/dev/null 2>&1

if [ $# -lt 1 ] ; then
    echo usage: updateRMSShowerAssocs.sh yearmth
    exit
fi
ym=$1
yr=${ym:0:4}   
mth=${ym:4:6}

logger -s -t updateRMSShowerAssocs "starting"

cat $CAMINFO | while read li ; do 
    typ=$(echo $li | awk -F, '{printf("%s", $12)}') 

    if [ "${li:0:1}" != "#" ] ; then
        if [ ${typ:0:1} -eq 2 ] ; then 
            sitename=$(echo $li | awk -F, '{printf("%s", $1)}')
            camname=$(echo $li | awk -F, '{printf("%s", $2)}')
            if [ "$mth" == "" ] ; then
                for j in {01,02,03,04,05,06,07,08,09,10,11,12}
                do
                    if compgen -G ""$ARCHDIR/$sitename/$camname/$yr/${yr}${j}"/*" > /dev/null ; then 
                        ls -1 "$ARCHDIR/$sitename/$camname/$yr/${yr}${j}" | while read i
                        do 
                            $here/addRMSShowerDets.sh "$sitename" $camname $i 
                        done
                    fi
                done
            else
                if compgen -G ""$ARCHDIR/$sitename/$camname/$yr/${yr}${mth}"/*" > /dev/null ; then 
                    ls -1 "$ARCHDIR/$sitename/$camname/$yr/${yr}${mth}" | while read i
                    do 
                        $here/addRMSShowerDets.sh "$sitename" $camname "$i" 
                    done
                fi
            fi
        fi 
    fi
done
logger -s -t updateRMSShowerAssocs "finished"

