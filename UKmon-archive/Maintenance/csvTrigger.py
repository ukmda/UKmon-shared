#
# function to be triggered when a csv file arrives in ukmon-shared
# to copy it to the temp area for consolidation later
#
import boto3
from urllib.parse import unquote_plus


def lambda_handler(event, context):

    s3 = boto3.resource('s3')

    record = event['Records'][0]

    s3bucket = record['s3']['bucket']['name']
    s3object = record['s3']['object']['key']
    target = 'ukmon-shared'

    x = s3object.find('M20')
    if x == -1:
        # its not a standard ufoa file, check if its an rms file
        # print ('its not a ufoa file')
        x = s3object.find('_20')
        if x == -1:
            # yep not interested
            return 0
        else:
            x = x - 6

    outf = 'consolidated/temp/' + s3object[x:]
    s3object = unquote_plus(s3object)
    print(s3object)
    print(outf)
    src = {'Bucket': s3bucket, 'Key': s3object}
    s3.meta.client.copy_object(Bucket=target, Key=outf, CopySource=src)

    return 0
