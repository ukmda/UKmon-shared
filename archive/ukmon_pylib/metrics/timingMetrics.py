#
# nightly job metrics
#
# Copyright (C) 2018-2023 Mark McIntyre

import pandas as pd
import sys
import os
import matplotlib.pyplot as plt
import glob
import datetime


def graphOfData(logf, dtstr):
    with open(logf,'r') as inf:
        lis = inf.readlines()
    dta = [li for li in lis if li[:8]==dtstr]

    # note: timings in log are the start times of the process
    # so we offset the labels by 1 to align with the end times
    times = []
    events = ['start']
    elapsed = []
    lasttime = 0
    for li in dta:
        spls = li.split(',')
        elapsed.append(int(spls[2]))        # runtime so far
        events.append(spls[4].strip())      # event name
        times.append(int(spls[2])-lasttime) # duration of event
        lasttime = int(spls[2])
    
    # add two dummy end-time values
    elapsed.append(elapsed[-1])
    times.append(0)

    fig, ax = plt.subplots()
    width = 0.35       

    ax.set_ylabel('Task')
    ax.set_xlabel('Duration (s)')
    ax.set_title('Batch Phases: {}'.format(dtstr))
    ax.barh(events, times, width)
    fig = plt.gcf()
    fig.set_size_inches(12, 12)
    fig.tight_layout()
    plt.xlim([0,5000])
    plt.grid(axis='x')
    plt.gca().invert_yaxis()
    logname, _ = os.path.splitext(os.path.basename(logf))
    plt.savefig(f'./{dtstr}-{logname}.jpg', dpi=100)
    plt.close()



def getLogStats(nightlogf, matchlogf, thisdy):
    with open(nightlogf,'r') as inf:
        loglines = inf.readlines()
    
    #logf = os.path.basename(nightlogf)
    #spls = logf.split('-')
    #thisdy= spls[1]
    matchstr = 'RUNTIME'    

    # <13>Nov  1 11:49:55 nightlyJob: RUNTIME 10554 showerReport ALL 202211
    startFAM = 0
    startRD = 0
    dts = []
    tss = []
    tsks = []
    secs = []
    msgs = []
    for li in loglines:
        if matchstr in li:
            li = ' '.join(li.split()) # remove double-spaces eg when date is ' 6 Jan' as opposed to '16 Jan'
            spls = li.split()
            msg = ''
            for s in range(6, len(spls)):
                msg = msg + ' ' + spls[s]
            if 'start findAllMatches' in msg:
                startFAM = int(spls[5])
            dts.append(thisdy)
            tss.append(spls[2])
            tsks.append(spls[3].replace(':',''))
            secs.append(int(spls[5]))
            msgs.append(msg.strip())

    with open(matchlogf,'r') as inf:
        loglines = inf.readlines()
    
    # scan for findAllMatches data first
    for li in loglines:
        if matchstr in li:
            spls = li.split()
            if 'runDistrib' in spls[3]: 
                continue
            msg = ''
            for s in range(6, len(spls)):
                msg = msg + ' ' + spls[s]
            if 'start runDistrib' in msg:
                startRD = int(spls[5])
            dts.append(thisdy)
            tss.append(spls[2])
            tsks.append(spls[3].replace(':',''))
            secs.append(int(spls[5])+startFAM)
            msgs.append(msg.strip())

    # rescan for runDistrib data
    for li in loglines:
        if matchstr in li:
            spls = li.split()
            if 'runDistrib' not in spls[3]: 
                continue
            msg = ''
            for s in range(6, len(spls)):
                msg = msg + ' ' + spls[s]
            dts.append(thisdy)
            tss.append(spls[2])
            tsks.append(spls[3].replace(':',''))
            secs.append(int(spls[5]) + startFAM + startRD)
            msgs.append(msg.strip())

    df = pd.DataFrame(zip(dts,tss,secs,tsks,msgs), columns=['dts','tss','secs','tsk','msgs'])
    df = df.sort_values(by=['tss'])
    #print(df)
    df.to_csv('perfNightly.csv', mode='a', header=False, index=False)
    

if __name__ == '__main__':
    dtstr = sys.argv[1]
    logdir = os.path.join(os.getenv('SRC', default='/home/ec2-user/prod'), 'logs')
    nowdt = datetime.datetime.now().strftime('%Y%m%d')
    if nowdt == dtstr:
        nightf = os.path.join(logdir, 'nightlyJob.log')
        matchf = os.path.join(logdir, 'matchJob.log')
    else:
        logs = glob.glob(os.path.join(logdir, f'*{dtstr}*.log'))
        nightf = None
        matchf = None
        for fn in logs:
            if 'matches' in fn:
                matchf = fn
            if 'nightlyJob' in fn:
                nightf = fn
    if nightf is None or matchf is None or not os.path.isfile(nightf) or not os.path.isfile(matchf):
        print('logfile missing')
        print(nightf, matchf)
    else:        
        getLogStats(nightf, matchf, dtstr)
        graphOfData('perfNightly.csv', dtstr)
