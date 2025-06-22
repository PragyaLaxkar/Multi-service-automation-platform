#!/usr/bin/python3

import cgi
import cgitb
import boto3
from datetime import datetime, timedelta

cgitb.enable()

print("Content-Type: text/plain\n")

form = cgi.FieldStorage()
instance_id = form.getvalue("instanceId")
aws_access_key_id = form.getvalue("awsAccessKey")
aws_secret_access_key = form.getvalue("awsSecretKey")
region_name = form.getvalue("regionName")

cloudwatch = boto3.client(
    'cloudwatch',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=region_name
)

namespace = 'AWS/EC2' 
metric_name = 'CPUUtilization' 

end_time = datetime.utcnow()
start_time = end_time - timedelta(days=1)

response = cloudwatch.get_metric_statistics(
    Namespace=namespace,
    MetricName=metric_name,
    Dimensions=[
        {
            'Name': 'InstanceId',
            'Value': instance_id
        },
    ],
    StartTime=start_time,
    EndTime=end_time,
    Period=300, 
    Statistics=['Average'], 
    Unit='Percent'  
)

for data_point in response['Datapoints']:
    print(f"Time: {data_point['Timestamp']}, Average: {data_point['Average']}")
