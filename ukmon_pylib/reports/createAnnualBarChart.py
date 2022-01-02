#
# Create an annual bar chart of daily matches
#

import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import datetime

import fileformats.UOFormat as uof 
from wmpl.Utils.TrajConversions import jd2Date


def createBarChart(fname, yr):
    if not os.path.isfile(fname):
        print('{} missing', fname)
        return None
    matches = uof.MatchedCsv(fname)
    v1=int(matches.rawdata['_mjd'][0])
    v2=int(matches.rawdata['_mjd'][len(matches.rawdata)-1])+2
    ranges=list(range(v1,v2))
    li=matches.rawdata.groupby(pd.cut(matches.rawdata['_mjd'], ranges)).count()['_mjd'].tolist()

    dts=[]
    for d in ranges:
        dt = jd2Date(d + 2400000.5, dt_obj=True) # add 2400000.5 to convert to JD
        dts.append(dt)

    fig, ax = plt.subplots()
    width = 0.35       
    nowdt=datetime.datetime.now()
    ax.set_ylabel('# matches')
    ax.set_xlabel('Date')
    ax.set_title('Number of matched events per day. Last updated {}'.format(nowdt.strftime('%Y-%m-%d %H:%M:%S')))

    li.append(0) # comes up one short
    ax.bar(dts, li, width, label='Events')
    fig = plt.gcf()
    fig.set_size_inches(12, 5)
    fig.tight_layout()

    plt.savefig('Annual-{}.jpg'.format(yr), dpi=100)

    return matches


if __name__ == '__main__':
    if len(sys.argv) > 1:
        fname = sys.argv[1]
        yr = sys.argv[2]
    else:
        yr=2021
        datadir=os.getenv('DATADIR')
        fname = os.path.join(datadir, 'matched', 'matches-{}.csv'.format(yr))
        
    m = createBarChart(fname, yr)
#    print(m.selectByMag(minMag=-2))
