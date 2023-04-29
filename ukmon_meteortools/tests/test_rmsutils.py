# test the RMS and WMPL utils in the library

import os
from ukmon_meteortools.rmsutils import multiDayRadiant, multiTrackStack #, multiEventGroundMap,


here = os.path.split(os.path.abspath(__file__))[0]


def test_multiDayRadiant():
    datadir=os.path.join(here, 'data','mdr')
    outdir=os.path.join(here, 'data')
    multiDayRadiant(['UK0006','UK000F'], '20230421','20230423',outdir=outdir, shwr=None, datadir=datadir)
    assert os.path.isfile(os.path.join(outdir, 'ALL_20230423_195211_138993_radiants.png'))
    assert os.path.isfile(os.path.join(outdir, 'ALL_20230423_195211_138993_radiants.txt'))
    os.remove(os.path.join(outdir, 'ALL_20230423_195211_138993_radiants.png'))
    os.remove(os.path.join(outdir, 'ALL_20230423_195211_138993_radiants.txt'))


def test_multiEventGroundMap():
    #multiEventGroundMap()
    assert 1==0


def test_multiTrackStack():
    datadir=os.path.join(here, 'data','mdr')
    outdir=os.path.join(here, 'data')
    multiTrackStack(['UK0006','UK000F'], '20230421','20230423', outdir=outdir, datadir=datadir)
    assert os.path.isfile(os.path.join(outdir, '2CAMS_20230423_195211_138993_track_stack.jpg'))
    #os.remove(os.path.join(outdir, 'UK000F_20230423_195211_138993_track_stack.jpg'))
