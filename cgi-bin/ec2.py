#!/usr/bin/python3
print("content-type: text/html")
print()
import cgi
import boto3

ec2 = boto3.client('ec2', aws_access_key_id='Enter your access key here',
                   aws_secret_access_key='Enter your secret access key here',
                   region_name='ap-south-1')

instances = ec2.run_instances(
    ImageId='ami-0e1d06225679bc1c5',
    MinCount=1,
    MaxCount=1,
    InstanceType='t2.micro'
)
print(f'Instance created with ID: {instances["Instances"][0]["InstanceId"]}')
