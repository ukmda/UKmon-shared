#
# Python code to analyse meteor shower data
#

import sys
import os
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
#from matplotlib import dates as mdates
#import datetime

from utils import getShowerDates as sd

SMALL_SIZE = 8
MEDIUM_SIZE = 10
BIGGER_SIZE = 12


def getStatistics(sngldta, matchdta, outdir):
    numcams = len(sngldta.groupby('ID').size())
    numsngl = len(sngldta)
    nummatch = len(matchdta)
    matchgrps = matchdta.groupby('_Nos').size()
    nummatched = 0
    for index,row in matchgrps.items():
        nummatched += index * row
    return numcams, numsngl, nummatch, nummatched


def stationGraph(dta, shwrname, outdir, maxStats=20):
    print('creating count by station')
    # set paper size so fonts look good
    plt.clf()
    fig = plt.gcf()
    fig.set_size_inches(11.6, 8.26)

    grps=dta.groupby('ID').size()
    ax=grps.sort_values(ascending=False).plot.bar()
    for lab in ax.get_xticklabels():
        lab.set_fontsize(SMALL_SIZE)

    fname = os.path.join(outdir, '01_streamcounts_plot_by_station.jpg')
    plt.title('Count of single observations by station ({})'.format(shwrname))
    plt.savefig(fname)
    return len(grps)


def timeGraph(dta, shwrname, outdir, binmins=10):
    print('Creating single station binned graph')
    fname = os.path.join(outdir, '02_stream_plot_timeline_single.jpg')
    if shwrname == "All Showers":
        # we already have this graph
        return len(dta)
    # set paper size so fonts look good
    plt.clf()
    fig = plt.gcf()
    fig.set_size_inches(11.6, 8.26)

    # add a datetime column so i can bin the data
    dta = dta.assign(dt = pd.to_datetime(dta['Dtstamp'], unit='s'))
    # set the datetime to be the index
    dta = dta.set_index('dt')
    #select just the shower ID col
    countcol = dta['Shwr']
    # resample it 
    binned = countcol.resample('{}min'.format(binmins)).count()
    binned.plot(kind='bar')

    # set ticks and labels every 144 intervals
    plt.locator_params(axis='x', nbins=len(binned)/144)
    #plt.xticks(rotation=0)
    # set font size
    ax = plt.gca()
    for lab in ax.get_xticklabels():
        lab.set_fontsize(SMALL_SIZE)
        
    # format x-axes
    x_labels = binned.index.strftime('%b-%d')
    ax.set_xticklabels(x_labels)
    ax.set(xlabel="Date", ylabel="Count")

    plt.title('Observed stream activity {}min intervals ({})'.format(binmins, shwrname))
    plt.tight_layout()
    plt.savefig(fname)
    return len(dta)


def matchesGraphs(dta, shwrname, outdir, binmins=60):
    print('Creating matches binned graph')
    # set paper size so fonts look good
    plt.clf()
    fig = plt.gcf()
    fig.set_size_inches(11.6, 8.26)

    # add a datetime column so i can bin the data
    mdta = dta.assign(dt = pd.to_datetime(dta['_localtime'], format='_%Y%m%d_%H%M%S'))
    # set the datetime to be the index
    mdta = mdta.set_index('dt')
    #select just the shower ID col
    mcountcol = mdta['_ID1']
    # resample it 
    mbinned = mcountcol.resample('{}min'.format(binmins)).count()
    mbinned.plot(kind='bar')

    # set ticks and labels every 144 intervals
    plt.locator_params(axis='x', nbins=len(mbinned)/24)
    #plt.xticks(rotation=0)
    # set font size
    ax = plt.gca()
    for lab in ax.get_xticklabels():
        lab.set_fontsize(SMALL_SIZE)
        
    # format x-axes
    x_labels = mbinned.index.strftime('%b-%d')
    ax.set_xticklabels(x_labels)
    ax.set(xlabel="Date", ylabel="Count")

    fname = os.path.join(outdir, '03_stream_plot_timeline_matches.jpg')
    plt.title('Confirmed stream activity {}min intervals ({})'.format(binmins, shwrname))
    plt.tight_layout()
    plt.savefig(fname)

    plt.clf()
    # set paper size so fonts look good
    fig = plt.gcf()
    fig.set_size_inches(11.6, 8.26)


    matchgrps = dta.groupby('_Nos').size()
    matchgrps.plot.barh()
    ax = plt.gca()
    ax.set(xlabel="Count", ylabel="# Stations")

    fname = os.path.join(outdir, '04_stream_plot_by_correllation.jpg')
    plt.title('Number of Matched Observations ({})'.format(shwrname))
    plt.tight_layout()
    plt.savefig(fname)

    nummatched = 0
    for index,row in matchgrps.items():
        nummatched += index * row

    return len(dta), nummatched


def velDistribution(dta, shwrname, outdir, vg_or_vs, binwidth=0.2):
    print('Creating velocity distribution histogram')
    plt.clf()

    if vg_or_vs == 'vg':
        idx = '_vg'
        fname = '05_stream_plot_vel.jpg'
        title = 'Geocentric Velocity'
    else:
        idx = '_vs'
        fname = '06_heliocentric_velocity.jpg'
        title = 'Heliocentric Velocity'

    magdf = pd.DataFrame(dta[idx])
    bins = np.arange(10,80+binwidth,binwidth)
    magdf['bins'] = pd.cut(magdf[idx], bins=bins, labels=bins[:-1])

    _ = magdf.groupby(magdf.bins).count().plot(kind='bar', legend=None)
    ax = plt.gca()
    ax.set(xlabel='Velocity (km/s)', ylabel="Count")
    plt.locator_params(axis='x', nbins=12)
    for lab in ax.get_xticklabels():
        lab.set_fontsize(SMALL_SIZE)

    # format x-axes
    x_labels=["%.0f" % number for number in bins[:-1]]
    ax.set_xticklabels(x_labels)
    fig = plt.gcf()
    fig.set_size_inches(11.6, 8.26)

    fname = os.path.join(outdir, fname)
    plt.title('{} Distribution in bins of width {} ({})'.format(title, binwidth, shwrname))
    plt.tight_layout()
    plt.savefig(fname)
    return 


def durationDistribution(dta, shwrname, outdir, binwidth=0.2):
    print('Creating duration distribution histogram')
    plt.clf()

    max_dist = 100 # maximum sensible value - data over this is borked

    idx = '_dur'
    fname = '13_meteor_duration.jpg'
    title = 'Duration'
    xlab = 'Seconds'

    magdf = pd.DataFrame(dta[idx])
    magdf = magdf[magdf[idx] < max_dist]
    maxlen = max(magdf[idx])
    bins = np.arange(0, maxlen + binwidth, binwidth)
    magdf['bins'] = pd.cut(magdf[idx], bins=bins, labels=bins[:-1])

    _ = magdf.groupby(magdf.bins).count().plot(kind='bar', legend=None)
    ax = plt.gca()
    ax.set(xlabel='{} (s)'.format(xlab), ylabel="Count")
    plt.locator_params(axis='x', nbins=12)
    for lab in ax.get_xticklabels():
        lab.set_fontsize(SMALL_SIZE)

    # format x-axes
    x_labels=["%.1f" % number for number in bins[:-1]]
    ax.set_xticklabels(x_labels)
    fig = plt.gcf()
    fig.set_size_inches(11.6, 8.26)

    fname = os.path.join(outdir, fname)
    plt.title('{} Distribution ({})'.format(title, shwrname))
    plt.tight_layout()
    plt.savefig(fname)
    return maxlen


def distanceDistribution(dta, shwrname, outdir, binwidth=1.0):
    print('Creating distance distribution histogram')
    plt.clf()

    max_dist = 100 # maximum sensible value - data over this is borked

    idx = '_LD21'
    fname = '07_observed_trajectory_LD21.jpg'
    title = 'Observed Track Length'
    xlab = 'Length'

    magdf = pd.DataFrame(dta[idx])
    magdf = magdf[magdf[idx] < max_dist]
    maxlen = max(magdf[idx])
    bins = np.arange(0, maxlen + binwidth, binwidth)
    magdf['bins'] = pd.cut(magdf[idx], bins=bins, labels=bins[:-1])

    _ = magdf.groupby(magdf.bins).count().plot(kind='bar', legend=None)
    ax = plt.gca()
    ax.set(xlabel='{} (km)'.format(xlab), ylabel="Count")
    plt.locator_params(axis='x', nbins=12)
    for lab in ax.get_xticklabels():
        lab.set_fontsize(SMALL_SIZE)

    # format x-axes
    x_labels=["%.0f" % number for number in bins[:-1]]
    ax.set_xticklabels(x_labels)
    fig = plt.gcf()
    fig.set_size_inches(11.6, 8.26)

    fname = os.path.join(outdir, fname)
    plt.title('{} Distribution ({})'.format(title, shwrname))
    plt.tight_layout()
    plt.savefig(fname)
    return maxlen


def ablationDistribution(dta, shwrname, outdir):
    print('Creating ablation zone distribution histogram')
    plt.clf()

    idx = '_H1'
    idx2 = '_H2'
    fname = '11_stream_ablation.jpg'
    title = 'Ablation Zone'

    magdf = dta[[idx, idx2]].copy()
    
    magdf = magdf[magdf[idx] < 140.0]
    magdf = magdf[magdf[idx2] > 0.0]
    magdf = magdf.sort_values(by=['_H1', '_H2'], ascending=[False, True])

    magdf.plot(kind='bar', width=1.0, alpha=1, legend=None)
    ax = plt.gca()
    ax.set(xlabel='', ylabel="km")
    plt.locator_params(axis='x', nbins=12)
    for lab in ax.get_xticklabels():
        lab.set_fontsize(SMALL_SIZE)

    fig = plt.gcf()
    fig.set_size_inches(11.6, 8.26)

    fname = os.path.join(outdir, fname)
    plt.title('{} Distribution ({})'.format(title, shwrname))
    plt.tight_layout()
    plt.savefig(fname)
    return min(magdf[idx2])


def radiantDistribution(dta, shwrname, outdir):
    print('Creating radiant scatterplot')
    plt.clf()

    idx = '_ra_o'
    idx2 = '_dc_o'
    fname = '12_stream_plot_radiant.jpg'
    title = 'Radiant Position'

    magdf = dta[[idx, idx2]].copy()
    
    magdf = magdf.sort_values(by=[idx, idx2], ascending=[False, True])

    #bins = np.arange(0,maxalt+binwidth,binwidth)
#    magdf['bins'] = pd.cut(magdf[idx], bins=bins, labels=bins[:-1])

    magdf.plot.scatter(x=idx, y=idx2)
    ax = plt.gca()
    ax.set(xlabel='RA (deg)', ylabel="Dec (deg)")
    #plt.locator_params(axis='x', nbins=12)
    #for lab in ax.get_xticklabels():
    #    lab.set_fontsize(SMALL_SIZE)

    # format x-axes
    #x_labels=["%.0f" % number for number in bins[:-1]]
    #ax.set_xticklabels(x_labels)
    fig = plt.gcf()
    fig.set_size_inches(11.6, 8.26)

    fname = os.path.join(outdir, fname)
    plt.title('{} Distribution ({})'.format(title, shwrname))
    plt.tight_layout()
    plt.savefig(fname)
    return 


def semimajorDistribution(dta, shwrname, outdir, binwidth=0.5):
    print('Creating semimajor axis histogram')
    plt.clf()

    magdf=pd.DataFrame(dta['_a'])
    magdf = magdf[magdf['_a'] > 0]
    magdf = magdf[magdf['_a'] < 20]
    maxval = max(magdf['_a'])
    bins=np.arange(0, maxval + binwidth,binwidth)
    magdf['bins']=pd.cut(magdf['_a'], bins=bins, labels=bins[:-1])

    _ = magdf.groupby(magdf.bins).count().plot(kind='bar', legend=None)
    ax = plt.gca()
    ax.set(xlabel="Semimajor Axis (AU)", ylabel="Count")
    plt.locator_params(axis='x', nbins=12)
    for lab in ax.get_xticklabels():
        lab.set_fontsize(SMALL_SIZE)

    # format x-axes
    x_labels=["%.0f" % number for number in bins[:-1]]
    ax.set_xticklabels(x_labels)
    fig = plt.gcf()
    fig.set_size_inches(11.6, 8.26)

    fname = os.path.join(outdir, '10_semimajoraxisfreq.jpg')
    plt.title('Semimajor Axis Distribution in bins of width {} ({})'.format(binwidth, shwrname))
    plt.tight_layout()
    plt.savefig(fname)
    return 


def magDistributionAbs(dta, shwrname, outdir, binwidth=0.2):
    print('Creating matches abs mag histogram')
    plt.clf()

    bestvmag = min(dta['_mag'])
    magdf=pd.DataFrame(dta['_amag'])
    bins=np.arange(-6,6+binwidth,binwidth)
    magdf['bins']=pd.cut(magdf['_amag'], bins=bins, labels=bins[:-1])

    _ = magdf.groupby(magdf.bins).count().plot(kind='bar', legend=None)
    ax = plt.gca()
    ax.set(xlabel="Magnitude", ylabel="Count")
    plt.locator_params(axis='x', nbins=12)
    for lab in ax.get_xticklabels():
        lab.set_fontsize(SMALL_SIZE)

    # format x-axes
    x_labels=["%.0f" % number for number in bins[:-1]]
    ax.set_xticklabels(x_labels)
    fig = plt.gcf()
    fig.set_size_inches(11.6, 8.26)

    fname = os.path.join(outdir, '08_stream_plot_mag.jpg')
    plt.title('Abs Magnitude Distribution in bins of width {} ({})'.format(binwidth, shwrname))
    plt.tight_layout()
    plt.savefig(fname)
    return min(magdf['_amag']), bestvmag


def magDistributionVis(dta, shwrname, outdir, binwidth=0.2):
    print('Creating detections visual mag histogram')

    magdf=pd.DataFrame(dta['Mag'])
    bins=np.arange(-6,6+binwidth,binwidth)
    magdf['bins']=pd.cut(magdf['Mag'], bins=bins, labels=bins[:-1])

    gd = magdf.groupby(magdf.bins).count()
    
    gd.plot(kind='bar', legend=None)
    ax = plt.gca()
    ax.set(xlabel="Magnitude", ylabel="Count")
    plt.locator_params(axis='x', nbins=12)
    for lab in ax.get_xticklabels():
        lab.set_fontsize(SMALL_SIZE)
        
    # format x-axes
    x_labels=["%.0f" % number for number in bins[:-1]]
    ax.set_xticklabels(x_labels)
    fig = plt.gcf()
    fig.set_size_inches(11.6, 8.26)

    fname = os.path.join(outdir, '07_stream_plot_vis_mag.jpg')
    plt.title('Visual Magnitude Distribution in bins of width {} ({})'.format(binwidth, shwrname))
    plt.tight_layout()
    plt.savefig(fname)
    return min(magdf['Mag'])


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage: python showerAnalysis.py GEM 2017')
        exit(0)
    yr=int(sys.argv[2])
    shwr = sys.argv[1]

    datadir = os.getenv('DATADIR')
    if datadir is None:
        print('define DATADIR first')
        exit(1)

    # set up paths, files etc
    outdir = os.path.join(datadir, 'reports', str(yr), shwr)
    os.makedirs(outdir, exist_ok=True)

    singleFile = os.path.join(datadir, 'single', 'singles-{}.csv'.format(yr))
    matchfile = os.path.join(datadir, 'matched', 'matches-full-{}.csv'.format(yr))

    # read the data
    sngl = pd.read_csv(singleFile)
    mtch = pd.read_csv(matchfile, skipinitialspace=True)

    # select the required data
    if shwr != 'ALL':
        id, shwrname, sl, dt = sd.getShowerDets(sys.argv[1])
        shwrfltr = sngl[sngl['Shwr']==shwr]
        mtchfltr = mtch[mtch['_stream']==shwr]
    else:
        shwrname = 'All Showers'
        shwrfltr = sngl
        mtchfltr = mtch

    numsngl = 0
    numcams = 0
    nummatch = 0
    nummatched = 0
    bestvmag = 0
    bestamag = 0
    lowest = 0
    longest = 0
    # now get the graphs and stats
    if len(shwrfltr) > 0:
        numsngl = timeGraph(shwrfltr, shwrname, outdir, 10)
        numcams = stationGraph(shwrfltr, shwrname, outdir, 20)
        bestvmag = magDistributionVis(shwrfltr, shwrname, outdir)
        pass
    if len(mtchfltr) > 0:
        if shwr == 'ALL':
            binsize = 1440
        else:
            binsize = 60
        nummatch, nummatched = matchesGraphs(mtchfltr, shwrname, outdir, binsize)
        bestamag, bestvmag = magDistributionAbs(mtchfltr, shwrname, outdir)
        velDistribution(mtchfltr, shwrname, outdir, 'vg')
        velDistribution(mtchfltr, shwrname, outdir, 'vs')
        longest = distanceDistribution(mtchfltr, shwrname, outdir)
        slowest = durationDistribution(mtchfltr, shwrname, outdir)
        lowest = ablationDistribution(mtchfltr, shwrname, outdir)
        if shwr != 'ALL':
            semimajorDistribution(mtchfltr, shwrname, outdir)
            radiantDistribution(mtchfltr, shwrname, outdir)
    
    outfname = os.path.join(outdir, 'statistics.txt')
    with open(outfname,'w') as outf:
        outf.write('Summary Statistics for {} {}\n'.format(shwrname, str(yr)))
        outf.write('=======================================\n\n')
        if shwr != 'ALL':
            outf.write('Shower ID and Code:                {} {}\n'.format(id, shwr))
            outf.write('Date of peak:                      {}-{}\n'.format(yr, dt))
            outf.write('Solar Longitide:                   {:.2f}\n\n'.format(sl))

        outf.write('Total Single-station Detections:   {}\n'.format(numsngl))
        outf.write('Total Matched Detections:          {}\n'.format(nummatched))
        outf.write('Leading to Solved Trajectories:    {}\n'.format(nummatch))
        outf.write('Number of Cameras with Detections: {}\n'.format(numcams))
        if numsngl > 0:
            convrate = nummatched / numsngl * 100
        else:
            convrate = 0
        outf.write('Conversion Rate:                   {:.2f}%\n\n'.format(convrate))

        outf.write('Brightest Magnitude seen:          {:.2f}\n'.format(bestvmag))
        outf.write('Lowest altitude seen:              {:.2f}km\n'.format(lowest))
        outf.write('Longest track seen:                {:.2f}km\n'.format(longest))
        outf.write('Longest event seen:                {:.2f}s\n'.format(slowest))

        outf.write('\nExplanation of the data\nThe correlator matches single station detections and where possible solves for the \n')
        outf.write('trajectory and orbit. Total matched detections is the number of single station detections \n')
        outf.write('that could be matched. Since two or more cameras are required for a match, the number \n')
        outf.write('of solved trajectories is always less than half the total matched detections.\n\n')
        outf.write('Note that its possible for no single station detections to be classified, but \n')
        outf.write('for the matching engine to identify previously missed shower members.\n\n')
        outf.write('Events with a lowest altitude below about 30km are potential meteorite droppers\n')

# to possibly add : 
# histogram of distance from radiant
# semimajor axis vs inclination and solar longitude
# abs mag vs lowest height
# abs mag vs track length
# abs mag vs lowest and highest heights
# UK map showing all  detections ground tracks
# sky map showing all detections sky tracks
