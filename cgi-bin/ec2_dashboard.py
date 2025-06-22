#!/usr/bin/env python3
import boto3
import json
import cgi
import cgitb
import datetime
from botocore.exceptions import ClientError

cgitb.enable()
print("Content-Type: application/json\n")

form = cgi.FieldStorage()
region_name = form.getvalue("regionName", "us-east-1")
action = form.getvalue("action")
instance_id = form.getvalue("instanceId")

AWS_KEY = ""
AWS_SECRET = ""

def get_ec2_client(region):
    return boto3.client("ec2", aws_access_key_id=AWS_KEY, aws_secret_access_key=AWS_SECRET, region_name=region)

def get_cloudwatch_client(region):
    return boto3.client("cloudwatch", aws_access_key_id=AWS_KEY, aws_secret_access_key=AWS_SECRET, region_name=region)

def perform_instance_action(ec2, action, instance_id):
    try:
        if action == "start":
            ec2.start_instances(InstanceIds=[instance_id])
        elif action == "stop":
            ec2.stop_instances(InstanceIds=[instance_id])
        elif action == "terminate":
            ec2.terminate_instances(InstanceIds=[instance_id])
        return json.dumps({"status": f"{action} action triggered for {instance_id}"})
    except Exception as e:
        return json.dumps({"error": str(e)})

def get_instance_uptime(launch_time):
    now = datetime.datetime.now(launch_time.tzinfo)
    uptime = now - launch_time
    return str(uptime).split('.')[0]

def get_cloudwatch_metrics(region, instance_id, metric_name):
    cw = get_cloudwatch_client(region)
    try:
        response = cw.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName=metric_name,
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=datetime.datetime.utcnow() - datetime.timedelta(minutes=60),
            EndTime=datetime.datetime.utcnow(),
            Period=300,
            Statistics=['Average']
        )
        datapoints = response.get('Datapoints', [])
        datapoints.sort(key=lambda x: x['Timestamp'])
        return [round(dp['Average'], 2) for dp in datapoints]
    except Exception as e:
        return [f"Error: {str(e)}"]

def get_all_instances(region):
    ec2 = get_ec2_client(region)
    try:
        instances_info = []
        response = ec2.describe_instances()
        for reservation in response['Reservations']:
            for inst in reservation['Instances']:
                instance_id = inst['InstanceId']
                instance_data = {
                    "InstanceID": instance_id,
                    "Name": next((tag['Value'] for tag in inst.get('Tags', []) if tag['Key'] == 'Name'), "N/A"),
                    "State": inst['State']['Name'],
                    "InstanceType": inst['InstanceType'],
                    "PublicIP": inst.get('PublicIpAddress', 'N/A'),
                    "PrivateIP": inst.get('PrivateIpAddress', 'N/A'),
                    "SecurityGroups": [sg['GroupName'] for sg in inst.get('SecurityGroups', [])],
                    "AMI": inst.get('ImageId', 'N/A'),
                    "KeyName": inst.get('KeyName', 'N/A'),
                    "LaunchTime": inst.get('LaunchTime').isoformat(),
                    "Uptime": get_instance_uptime(inst.get('LaunchTime')),
                    "VolumeInfo": [],
                    "CPU": get_cloudwatch_metrics(region, instance_id, 'CPUUtilization'),
                    "NetworkIn": get_cloudwatch_metrics(region, instance_id, 'NetworkIn')
                }

                for mapping in inst.get('BlockDeviceMappings', []):
                    volume_id = mapping['Ebs']['VolumeId']
                    vol = ec2.describe_volumes(VolumeIds=[volume_id])['Volumes'][0]
                    instance_data["VolumeInfo"].append({
                        "VolumeId": volume_id,
                        "Size (GiB)": vol['Size'],
                        "Type": vol['VolumeType'],
                        "State": vol['State']
                    })

                instances_info.append(instance_data)

        return json.dumps(instances_info)
    except ClientError as e:
        return json.dumps({"error": str(e)})

if action in ['start', 'stop', 'terminate'] and instance_id:
    ec2_client = get_ec2_client(region_name)
    print(perform_instance_action(ec2_client, action, instance_id))
else:
    print(get_all_instances(region_name))
