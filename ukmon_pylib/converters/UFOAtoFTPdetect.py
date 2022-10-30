#
# Python module to convert UFO data to RMS format
#
# Usage: python UFOAtoFTPdetect myfolder
#   will create an ftpdetect and stationinfo file for every A.xml file in "myfolder"
#

import os
import sys
import shutil
import fnmatch
import datetime
import glob
from fileformats import ReadUFOAnalyzerXML as UA
from fileformats import CameraDetails as cdet

CAMINFOFILE = 'CameraSites.txt'
CAMOFFSETSFILE = 'CameraTimeOffsets.txt'
FTPFILE = 'FTPdetectinfo_UFO.txt'


def loadRMSdata(fldr):
    rmsdata = []
    stations = []
    listOfFiles = os.listdir(fldr)
    for entry in listOfFiles:
        if fnmatch.fnmatch(entry, 'data*.txt'):
            fullname = os.path.join(fldr, entry)
            rmsdata.append(fullname)
        if fnmatch.fnmatch(entry, 'stat*.txt'):
            fullname = os.path.join(fldr, entry)
            stations.append(fullname)
    return rmsdata, stations


def loadAXMLs(fldr):
    """
    Load all the A.xml files in the given folder
    """
    axmls = []
    try:
        listOfFiles = os.listdir(fldr)
    except Exception:
        print('not a folder')
        return axmls, 0, 0
    pattern = '*A.XML'
    metcount = 0
    evttime = datetime.datetime.now()
    for entry in listOfFiles:
        if fnmatch.fnmatch(entry, pattern):
            fullname = os.path.join(fldr, entry)
            xmlf = UA.UAXml(fullname)
            axmls.append(xmlf)
            metcount += xmlf.getObjectCount()
            evttime = xmlf.getDateTime()
    return axmls, metcount, evttime


def writeFTPHeader(ftpf, metcount, stime, fldr):
    """
    Create the header of the FTPDetect file
    """
    l1 = 'Meteor Count = {:06d}\n'.format(metcount)
    ftpf.write(l1)
    ftpf.write('-----------------------------------------------------\n')
    ftpf.write('Processed with UFOAnalyser\n')
    ftpf.write('-----------------------------------------------------\n')
    l1 = 'FF  folder = {:s}\n'.format(fldr)
    ftpf.write(l1)
    l1 = 'CAL folder = {:s}\n'.format(fldr)
    ftpf.write(l1)
    ftpf.write('-----------------------------------------------------\n')
    ftpf.write('FF  file processed\n')
    ftpf.write('CAL file processed\n')
    ftpf.write('Cam# Meteor# #Segments fps hnr mle bin Pix/fm Rho Phi\n')
    ftpf.write('Per segment:  Frame# Col Row RA Dec Azim Elev Inten Mag\n')


def writeOneMeteor(ftpf, metno, sta, evttime, fcount, fps, fno, ra, dec, az, alt, b, mag):
    """
    Write one meteor event into the file in FTPDetectInfo style
    """
    ftpf.write('-------------------------------------------------------\n')
    ms = '{:03d}'.format(int(evttime.microsecond / 1000))

    fname = 'FF_' + sta + '_' + evttime.strftime('%Y%m%d_%H%M%S_') + ms + '_0000000.fits\n'
    ftpf.write(fname)

    ftpf.write('UFO UKMON DATA recalibrated on: ')
    ftpf.write(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f UTC\n'))
    li = sta + ' 0001 {:04d} {:04.2f} '.format(fcount, fps) + '000.0 000.0  00.0 000.0 0000.0 0000.0\n'
    ftpf.write(li)

    for i in range(len(fno)):
        #    204.4909 0422.57 0353.46 262.3574 +16.6355 267.7148 +23.0996 000120 3.41
        li = '{:08.4f} {:07.2f} {:07.2f} '.format(fno[i] - fno[0], 0, 0)  # UFO is timestamped as at the first detection
        li += '{:s} {:s} {:s} {:s} '.format('{:.4f}'.format(ra[i]).zfill(8),
            '{:+.4f}'.format(dec[i]).zfill(8),
            '{:.4f}'.format(az[i]).zfill(8),
            '{:+.4f}'.format(alt[i]).zfill(8))
        li += '{:06d} {:.2f}\n'.format(int(b[i]), mag[i])
        ftpf.write(li)


def createStationHeader(fldr):
    statinfo = os.path.join(fldr, CAMINFOFILE)
    statf = open(statinfo, 'w')
    statf.write('# CAMS compatible station info file\n')
    statf.write('# station_id, lat(+N degs), long (+W degs), Altitude (km)\n')
    statf.close()


def createStationInfo(fldr, sta, lat, lng, alt):
    """
    Create CAMS style station info file. For some reason CAMS uses km as the altitude.
    Lati and Longi are in degrees, North positive but WEST positive so not standard
    """
    statinfo = os.path.join(fldr, CAMINFOFILE)
    # sta = sta.replace('_', '')
    with open(statinfo, 'a') as statf:
        dets = '{:s} {:.4f} {:.4f} {:.3f}\n'.format(sta, lat, -lng, alt / 1000.0)
        statf.write(dets)


def convertFolder(fldr):
    """
    Read all the A.XML files and create an RMS ftpdetect file plus station info file
    Then check for any RMS data and append it onto the files
    """
    axmls, metcount, stime = loadAXMLs(fldr)

    # create an empty station info file
    createStationHeader(fldr)

    # create and populate the ftpdetectinfo file
    ftpfile = os.path.join(fldr, FTPFILE)
    with open(ftpfile, 'w') as ftpf:
        writeFTPHeader(ftpf, metcount, stime, fldr)
        metno = 1
        for thisxml in axmls:
            evttime = thisxml.getDateTime()
            sta, lid, sid, lat, lng, alt = thisxml.getStationDetails()
            fps, cx, cy, isintl = thisxml.getCameraDetails()
            lid = lid + sid
            lid = lid.replace('_','')
            createStationInfo(fldr, sta, lat, lng, alt)
            if isintl == 1:
                fps *= 2
            numobjs = thisxml.getObjectCount()
            # print(evttime, sta, lid, sid, numobjs)

            for i in range(numobjs):
                fno, tt, ra, dec, mag, fcount, alt, az, b, lsum = thisxml.getPathVector(i)
                metno += 1
                writeOneMeteor(ftpf, metno, sta, evttime, fcount, fps, fno, ra, dec, az, alt, b, mag)
                # print(fno, tt, ra, dec, alt, az, b, mag)

    rmsdata, statfiles = loadRMSdata(fldr)
    with open(os.path.join(fldr, FTPFILE), 'a') as wfd:
        for f in rmsdata:
            print(os.path.basename(f))
            with open(f, 'r') as fd:
                shutil.copyfileobj(fd, wfd)
    with open(os.path.join(fldr, CAMINFOFILE), 'a') as wfd:
        for f in statfiles:
            with open(f, 'r') as fd:
                shutil.copyfileobj(fd, wfd)
                wfd.write('\n')

    return


def convertUFOFolder(fldr, outfldr):
    """
    Read all the A.XML files and create an RMS ftpdetect file and platepars file
    """
    print('reading from', fldr)
    axmls, metcount, stime = loadAXMLs(fldr)
    if len(axmls) == 0:
        print('no a.xml files found')
        return 

    _, ymd = os.path.split(fldr)
    _, lid, sid, _, _, _ = axmls[0].getStationDetails()
    if lid == 'Blackfield' and sid == '':
        sid = 'c1'

    ci = cdet.SiteInfo()
    statid = ci.getDummyCode(lid, sid)
    if statid == 'Unknown':
        statid = 'XX9999'

    arcdir = statid + '_' + ymd + '_180000_000000'
    ftpfile = 'FTPdetectinfo_' + arcdir + '.txt'

    fulloutfldr = os.path.join(outfldr,statid, arcdir)
    print('writing to', fulloutfldr)
    os.makedirs(fulloutfldr, exist_ok=True)

    plateparfile = open(os.path.join(fulloutfldr, 'platepars_all_recalibrated.json'), 'w')
    plateparfile.write('{\n')

    # create and populate the ftpdetectinfo file
    ftpfile = os.path.join(fulloutfldr, ftpfile)
    with open(ftpfile, 'w') as ftpf:
        writeFTPHeader(ftpf, metcount, stime, fldr)
        metno = 1
        for thisxml in axmls:
            if metno > 1: 
                plateparfile.write(',\n')
            evttime = thisxml.getDateTime()
            fps, cx, cy, isintl = thisxml.getCameraDetails()
            if isintl == 1:
                fps *= 2
            numobjs = thisxml.getObjectCount()

            for i in range(numobjs):
                fno, tt, ra, dec, mag, fcount, alt, az, b, lsum = thisxml.getPathVector(i)
                metno += 1
                writeOneMeteor(ftpf, metno, statid, evttime, fcount, fps, fno, ra, dec, az, alt, b, mag)
            
            pp = thisxml.makePlateParEntry(statid)
            plateparfile.write(pp)

    plateparfile.write('\n}\n')
    plateparfile.close()
    return


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage python UFOtoFTPdetect.py srcfolder targfolder')
        print('  will convert all UFO A.xml files in srcfolder to a single FTPDetectInfo file in targfolder')
        print('Usage python UFOtoFTPdetect.py yyyymmdd targfolder')
        print('  will convert all UFO data for all cameras for the given date. dd is optional')
    else:
        if len(sys.argv[1]) < 9:
            # its a date
            ymdin = sys.argv[1]
            outroot = sys.argv[2]
            archdir=os.getenv('ARCHDIR', default='/home/ec2-user/ukmon-shared/archive')
            
            yr = ymdin[:4] 
            ym = ymdin[:6] 
            if len(ymdin) > 7:
                ymd = ymdin[:8] 
            else:
                ymd = None
            print(yr, ym, ymd)
            ci = cdet.SiteInfo()
            ufos = ci.getUFOCameras(True)
            for cam in ufos:
                site = cam['Site']
                camid = cam['CamID']
                dum = cam['dummycode']
                if ymd is None:
                    inroot = os.path.join(archdir,site, camid, yr, ym)
                    days = glob.glob1(inroot, '*')
                    for d in days:
                        inpth = os.path.join(inroot, d)
                        fils = glob.glob1(inpth, "*.*")
                        if len(fils) > 0: 
                            try:
                                convertUFOFolder(inpth, outroot)
                            except:
                                continue
                else:
                    inpth = os.path.join(archdir,site, camid, yr, ym, ymd)
                    convertUFOFolder(inpth, outroot)
        else:
            # its a folder
            convertUFOFolder(sys.argv[1], sys.argv[2])
