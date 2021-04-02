#
# Create additional information from pickled Trajectory file
#
import os
import sys
import glob
import csv

import boto3

from wmpl.Trajectory.Trajectory import Trajectory
from wmpl.Utils.Pickling import loadPickle 
from wmpl.Utils.TrajConversions import jd2Date
from datetime import datetime, timedelta


from ufoTrajSolver import createAdditionalOutput, loadCameraSites


def getCameraDetails():
    # fetch camera details from the CSV file
    fldrs = []
    cams = []
    lati = []
    alti = []
    longi = []
    camtyp = []
    fullcams = []
    camfile = 'camera-details.csv'

    s3 = boto3.resource('s3')
    s3.meta.client.download_file('ukmon-shared', 'consolidated/' + camfile, camfile)
    with open(camfile, 'r') as f:
        r = csv.reader(f)
        for row in r:
            if row[0][:1] != '#':
                if row[1] == '':
                    fldrs.append(row[0])
                else:
                    fldrs.append(row[0] + '/' + row[1])
                if int(row[11]) == 1:
                    cams.append(row[2] + '_' + row[3])
                else:
                    cams.append(row[2])
                fullcams.append(row[0] + '_' + row[3])
                longi.append(float(row[8]))
                lati.append(float(row[9]))
                alti.append(float(row[10]))
                camtyp.append(int(row[11]))
    os.remove(camfile)
    return cams, fldrs, lati, longi, alti, camtyp, fullcams


def generateExtraFiles(outdir):

    picklefile = glob.glob1(outdir, '*.pickle')[0]
    traj = loadPickle(outdir, picklefile)

    createAdditionalOutput(traj, outdir)
    fetchJpgsAndMp4s(traj, outdir)
    return


def fetchJpgsAndMp4s(traj, outdir):

    print('getting camera details file')
    cams, fldrs, lati, longi, alti, camtyps, fullcams = getCameraDetails()
    for obs in traj.observations:
        statid = obs.station_id
        ci = cams.index(statid)
        fldr = fldrs[ci]

        evtdate = jd2Date(obs.jdt_ref, dt_obj=True)

        # if the event is after midnight the folder will have the previous days date
        if evtdate.hour < 12:
            evtdate += timedelta(days=-1)
        yr = evtdate.year
        ym = evtdate.year * 100 + evtdate.month
        ymd = ym *100 + evtdate.day

        srcpath = '/home/ec2-user/ukmon-shared/archive/{:s}/{:04d}/{:06d}/{:08d}'.format(fldr, yr, ym, ymd)
        print(srcpath)
    return


if __name__ == '__main__':
    generateExtraFiles(sys.argv[1])
