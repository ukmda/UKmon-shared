#
# Create and access dynamodb tables containing camera upload timings etc
#
# Copyright (C) 2018-2023 Mark McIntyre

import boto3
import os
import sys
import glob
from boto3.dynamodb.conditions import Key
import pandas as pd


def addRowCamTimings(s3bucket, s3object, ftpname, ddb=None):
    s3c = boto3.client('s3')
    dtstamp = s3c.head_object(Bucket=s3bucket, Key=s3object)['LastModified']

    if not ddb:
        ddb = boto3.resource('dynamodb', region_name='eu-west-1') #, endpoint_url="http://thelinux:8000")

    table = ddb.Table('uploadtimes')
    spls = ftpname.split('_')
    #print(spls[0], dtstamp)
    if spls[-1] == 'manual.txt':
        manflag = '_man'
        manual = True
    else:
        manflag = ''
        manual = False
    uploaddate = dtstamp.strftime('%Y%m%d')
    uploadtime = dtstamp.strftime('%H%M%S')
    table.put_item(
        Item={
            'stationid': spls[1],
            'dtstamp': uploaddate + '_' + uploadtime + manflag,
            'uploaddate': int(uploaddate),
            'uploadtime': int(uploadtime),
            'manual': manual
            #,'ExpiryDate', int(expirydate)
        }
    )    
    return 


# find matching entries based on stationid and upload date in yyyymmdd format
def findRowCamTimings(stationid, uploaddate, ddb=None):
    if not ddb:
        ddb = boto3.resource('dynamodb', region_name='eu-west-1') #, endpoint_url="http://thelinux:8000")
    table = ddb.Table('uploadtimes')
    response = table.query(
        KeyConditionExpression=Key('stationid').eq(stationid) & Key('dtstamp').begins_with(uploaddate)
    )
    try:
        items = response['Items']
        for item in items:
            print(item['stationid'], item['uploaddate'], item['uploadtime'],item['manual'])
    except Exception:
        print('record not found')
    return


# find matching entries based on upload date in yyyymmdd format
# aws dynamodb query --table-name uploadtimes 
# --index-name uploaddate-stationid-index 
# --key-condition-expression "uploaddate= :dt" 
# --expression-attribute-values '{":dt":{"N":"20220108"}}'

def getDayCamTimings(uploaddate, ddb=None, outfile=None, datadir=None):
    if datadir is None:
        datadir = os.getenv('DATADIR', default='/home/ec2-user/prod/data')
    if not ddb:
        ddb = boto3.resource('dynamodb', region_name='eu-west-1') #, endpoint_url="http://thelinux:8000")
    table = ddb.Table('uploadtimes')
    response = table.query(
        IndexName='uploaddate-stationid-index',
        KeyConditionExpression=Key('uploaddate').eq(int(uploaddate)))

    statids = []
    updtims = []
    manuals = []
    upddts = []
    rundts = []
    try:
        items = response['Items']

        for item in items:
            statids.append(item['stationid'])
            updtims.append(item['uploadtime'])
            manuals.append(item['manual'])
            upddts.append(uploaddate)
            try:
                rundts.append(item['rundate'])
            except:
                print(f"2fudging rundate for {item['stationid']}")
                estdt = f"{uploaddate}_{int(item['uploadtime']):06d}"
                rundts.append(estdt)

        if outfile is not None:
            with open(os.path.join(datadir, 'reports', outfile), 'w') as outf:
                outf.write('stationid,upddate,uploadtime,manual\n')
                for ss,dd,tt,mm in zip(statids, upddts, updtims, manuals):
                    outf.write(f'{ss},{dd},{int(tt):06d},{mm}\n')

    except Exception:
        print('record not found')
    return statids, upddts, updtims, manuals, rundts


# read a row based on stationid and datestamp
def readRowCamTimings(stationid, dtstamp, ddb=None):
    if not ddb:
        ddb = boto3.resource('dynamodb', region_name='eu-west-1') #, endpoint_url="http://thelinux:8000")
    table = ddb.Table('uploadtimes')
    response = table.get_item(Key={'stationid': stationid,'dtstamp': dtstamp})
    try:
        item = response['Item']
        print(item['stationid'], item['uploaddate'], item['uploadtime'],item['manual'])
    except Exception:
        print('record not found')
    return


# remove a row from the table keyed on stationid adn datestamp in yyyymmdd_hhmmss format
def deleteRowCamTimings(stationid, dtstamp, ddb=None):
    if not ddb:
        ddb = boto3.resource('dynamodb', region_name='eu-west-1') #, endpoint_url="http://thelinux:8000")
    table = ddb.Table('uploadtimes')
    table.delete_item(Key={'stationid': stationid, 'dtstamp': dtstamp})
    return 


def backPopulate(stationid):
    s3bucket = os.getenv('UKMONSHAREDBUCKET', default='s3://ukmda-shared')[5:]

    fldrs = glob.glob1(f'/home/ec2-user/ukmon-shared/matches/RMSCorrelate/{stationid}/', '*')
    for fldr in fldrs:
        s3objects = glob.glob1(f'/home/ec2-user/ukmon-shared/matches/RMSCorrelate/{stationid}/{fldr}/', 'FTPd*')
        if len(s3objects) > 0:
            s3obj = s3objects[0]
            fullobj = f'matches/RMSCorrelate/{stationid}/{fldr}/{s3obj}'
            print(fullobj, s3obj)
            addRowCamTimings(s3bucket, fullobj, s3obj)


if __name__ == '__main__':
    datadir = os.getenv('DATADIR', default='/home/ec2-user/prod/data')

    sts_client = boto3.client('sts')
    assumed_role_object=sts_client.assume_role(
        RoleArn="arn:aws:iam::183798037734:role/service-role/S3FullAccess",
        RoleSessionName="AssumeRoleSession1")
    credentials=assumed_role_object['Credentials']

    ddb = boto3.resource('dynamodb', region_name='eu-west-1',
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'])

    s,d,t,m,r = getDayCamTimings(sys.argv[1], ddb=ddb)
    newdata=pd.DataFrame(zip(s,d,t,m,r), columns=['stationid','upddate','uploadtime','manual','rundate'])

    outfile=os.path.join(datadir, 'reports', 'camuploadtimes.csv')
    if os.path.isfile(outfile):
        currdata = pd.read_csv(outfile)
        fulldf = pd.concat([currdata, newdata], ignore_index=True)
        fulldf = fulldf.sort_values(by=['stationid','upddate','uploadtime','rundate'])
        fulldf = fulldf.drop_duplicates(subset=['stationid'], keep='last')
    else:
        fulldf = newdata
    fulldf.to_csv(outfile, index=False)
