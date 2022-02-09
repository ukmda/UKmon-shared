#
# Create additional information from pickled Trajectory file
#
import os
import sys
import glob
import shutil
import platform

from wmpl.Utils.Pickling import loadPickle 
from wmpl.Utils.TrajConversions import jd2Date
from datetime import datetime, timedelta
from traj.ufoTrajSolver import createAdditionalOutput, calcAdditionalValues, loadMagData
from fileformats import CameraDetails as cdet


def generateExtraFiles(outdir, cinfo, datadir, archdir, skipimgs = False):
    outdir=os.path.normpath(outdir)
    try:
        picklefile = glob.glob1(outdir, '*.pickle')[0]
    except Exception:
        print('no pickle found in ', outdir)
    else:
        traj = loadPickle(outdir, picklefile)
        traj.save_results = True
        print(picklefile)
        createAdditionalOutput(traj, outdir)
        if skipimgs is False:
            # findMatchingJpgs(traj, outdir)
            findMatchingOtherFiles(traj, outdir, cinfo, datadir, archdir)
    return


def getBestView(outdir):
    try:
        picklefile = glob.glob1(outdir, '*.pickle')[0]
    except Exception:
        print('no picklefile in ', outdir)
        return ''
    else:
        traj = loadPickle(outdir, picklefile)
        _, statids, vmags = loadMagData(traj)
        bestvmag = min(vmags)
        beststatid = statids[vmags.index(bestvmag)]
        imgfn = glob.glob1(outdir, '*{}*.jpg'.format(beststatid))
        if len(imgfn) > 0:
            bestimg = imgfn[0]
        else:
            with open(os.path.join(outdir, 'jpgs.lst')) as inf:
                lis = inf.readlines()
            bestimg=''
            worstmag = max(vmags)
            for mag, stat in zip(vmags, statids):
                res=[stat in ele for ele in lis]    
                imgfn = lis[res is True].strip()
                if mag <= worstmag:
                    if len(imgfn) > 0:
                        bestimg = imgfn

        return bestimg


def getVMagCodeAndStations(outdir):

    picklefile = glob.glob1(outdir, '*.pickle')[0]
    traj = loadPickle(outdir, picklefile)
    _, bestvmag, _, _, cod, _, _, _, _, _, _, stations = calcAdditionalValues(traj)
    return bestvmag, cod, stations


def findMatchingJpgs(traj, outdir):
    try:
        datadir = os.getenv('DATADIR')
    except Exception:
        datadir='/home/ec2-user/prod/data'

    jpgs = None
    # file to write JPGs html to, for performance benefits
    jpghtml = open(os.path.join(outdir, 'jpgs.html'), 'w')
    # loop over observations adding jpgs to the listing file
    with open(os.path.join(outdir, 'jpgs.lst'), 'w') as outf:
        for obs in traj.observations:
            statid = obs.station_id
            evtdate = jd2Date(obs.jdt_ref, dt_obj=True)
            if jpgs is None:
                with open(os.path.join(datadir, 'singleJpgs-{}.csv'.format(evtdate.year))) as inf:
                    jpgs = inf.readlines()
            compstr = statid + '_' + evtdate.strftime('%Y%m%d_%H%M%S')
            mtch=[line.strip() for line in jpgs if compstr[:-1] in line]
            if len(mtch) > 1: 
                for m in mtch:
                    fn = os.path.basename(m)
                    spls=fn.split('_')
                    dtstamp = datetime.strptime(spls[2] + '_' + spls[3], '%Y%m%d_%H%M%S')
                    if (evtdate - dtstamp).seconds < 10:
                        outf.write('{}\n'.format(m))
                        break
            elif len(mtch) == 0:
                tmped = evtdate + timedelta(seconds=-10)
                compstr = statid + '_' + tmped.strftime('%Y%m%d_%H%M%S')
                mtch=[line.strip() for line in jpgs if compstr[:-1] in line]
                if len(mtch) > 0:
                    outf.write('{}\n'.format(mtch[0]))
                    jpghtml.write(f'<a href="/{mtch[0]}"><img src="/{mtch[0]}" width="20%"></a>\n')
            else: 
                outf.write('{}\n'.format(mtch[0]))
                jpghtml.write(f'<a href="/{mtch[0]}"><img src="/{mtch[0]}" width="20%"></a>\n')
    jpghtml.close()


def findMatchingOtherFiles(traj, outdir, cinfo, datadir, archdir):
    mp4s = None
    jpgs = None
    mp4html = open(os.path.join(outdir, 'mpgs.html'), 'w')
    jpghtml = open(os.path.join(outdir, 'jpgs.html'), 'w')
    mp4outf = open(os.path.join(outdir, 'mpgs.lst'), 'w')
    jpgoutf = open(os.path.join(outdir, 'jpgs.lst'), 'w')
    for obs in traj.observations:
        statid = obs.station_id
        fldr = cinfo.getFolder(statid)
        evtdate = jd2Date(obs.jdt_ref, dt_obj=True)
        if mp4s is None:
            with open(os.path.join(datadir, 'singleMp4s-{}.csv'.format(evtdate.year))) as inf:
                mp4s = inf.readlines()
        if jpgs is None:
            with open(os.path.join(datadir, 'singleJpgs-{}.csv'.format(evtdate.year))) as inf:
                jpgs = inf.readlines()

        compstr = statid + '_' + evtdate.strftime('%Y%m%d_%H%M%S')
        #print(compstr)
        # look for matching jpgs
        mtch=[line.strip() for line in jpgs if compstr[:-1] in line]
        if len(mtch) > 1: 
            for m in mtch:
                fn = os.path.basename(m)
                spls=fn.split('_')
                dtstamp = datetime.strptime(spls[2] + '_' + spls[3], '%Y%m%d_%H%M%S')
                if (evtdate - dtstamp).seconds < 10:
                    jpgoutf.write('{}\n'.format(m))
                    break
        elif len(mtch) == 0:
            tmped = evtdate + timedelta(seconds=-10)
            compstr = statid + '_' + tmped.strftime('%Y%m%d_%H%M%S')
            mtch=[line.strip() for line in jpgs if compstr[:-1] in line]
            if len(mtch) > 0:
                jpgoutf.write('{}\n'.format(mtch[0]))
                jpghtml.write(f'<a href="/{mtch[0]}"><img src="/{mtch[0]}" width="20%"></a>\n')
        else: 
            jpgoutf.write('{}\n'.format(mtch[0]))
            jpghtml.write(f'<a href="/{mtch[0]}"><img src="/{mtch[0]}" width="20%"></a>\n')

        #now do MP4s            
        mtch=[line.strip() for line in mp4s if compstr[:-1] in line]
        if len(mtch) > 1: 
            for m in mtch:
                fn = os.path.basename(m)
                spls=fn.split('_')
                dtstamp = datetime.strptime(spls[2] + '_' + spls[3], '%Y%m%d_%H%M%S')
                if (evtdate - dtstamp).seconds < 10:
                    mp4outf.write('{}\n'.format(m))
                    mp4html.write(f'<a href="/{m}"><video width="20%"><source src="/{m}" width="20%" type="video/mp4"></video></a>\n')
                    break
        elif len(mtch) == 0:
            tmped = evtdate + timedelta(seconds=-10)
            compstr = statid + '_' + tmped.strftime('%Y%m%d_%H%M%S')
            mtch=[line.strip() for line in mp4s if compstr[:-1] in line]
            if len(mtch) > 0:
                mp4outf.write('{}\n'.format(mtch[0]))
                mp4html.write(f'<a href="/{mtch[0]}"><video width="20%"><source src="/{mtch[0]}" width="20%" type="video/mp4"></video></a>\n')
        else: 
            mp4outf.write('{}\n'.format(mtch[0]))
            mp4html.write(f'<a href="/{mtch[0]}"><video width="20%"><source src="/{mtch[0]}" width="20%" type="video/mp4"></video></a>\n')

        # if the event is after midnight the folder will have the previous days date
        if evtdate.hour < 12:
            evtdate += timedelta(days=-1)
        yr = evtdate.year
        ym = evtdate.year * 100 + evtdate.month
        ymd = ym *100 + evtdate.day

        thispth = '{:s}/{:04d}/{:06d}/{:08d}/'.format(fldr, yr, ym, ymd)
        srcpath = os.path.join(archdir, thispth)
        print('R90 CSV, KML and FTPDetect file')
        try:
            flist=glob.glob1(srcpath, '*.csv')
            for f in flist:
                shutil.copy2(os.path.join(srcpath, f), outdir)
            flist=glob.glob1(srcpath, '*.kml')
            for f in flist:
                shutil.copy2(os.path.join(srcpath, f), outdir)
            flist = glob.glob1(srcpath, "FTPdetectinfo*.txt")
            for fil in flist:
                shutil.copy2(os.path.join(srcpath, f), outdir)
        except:
            continue
    mp4html.close()
    mp4outf.close()
    jpghtml.close()
    jpgoutf.close()
    return


if __name__ == '__main__':
    archdir = os.getenv('ARCHDIR')
    if archdir is None:
        archdir='/home/ec2-user/ukmon-shared/archive'
    try:
        datadir = os.getenv('DATADIR')
    except Exception:
        datadir='/home/ec2-user/prod/data'

    fl = sys.argv[1]
    skipimgs = False
    if platform.system() == 'Windows':
        skipimgs = True
    cinfo = cdet.SiteInfo()
    if os.path.isdir(fl):
        generateExtraFiles(fl, cinfo, datadir, archdir, skipimgs=skipimgs)
    else:
        with open(fl,'r') as inf:
            dirs = inf.readlines()
            for li in dirs:
                fl = li.split(',')[1]
                generateExtraFiles(fl, cinfo, datadir, archdir, skipimgs=skipimgs)
