import cgi
import cgitb
import boto3
import time
import json
from botocore.exceptions import ClientError
import sys
import datetime
sys.stderr = sys.stdout

cgitb.enable()
print("Content-Type: application/json\n")

form = cgi.FieldStorage()
action = form.getvalue('action')
instance_type = form.getvalue('instanceType')
image_id = form.getvalue('imageId')
region_name = form.getvalue('regionName')
key_name = form.getvalue('keyName')
security_group_id = form.getvalue('securityGroup')
num_instances = int(form.getvalue('count', 1))
instance_id = form.getvalue('instanceId')  # For stop/start/terminate
instance_name = form.getvalue('instanceName', 'LaunchedViaWebForm')
volume_size = int(form.getvalue('volumeSize', 8))  # default to 8 GB

def get_ec2_client(region):
    return boto3.client(
        'ec2',
        aws_access_key_id='',
        aws_secret_access_key='',
        region_name=region
    )

def ensure_key_pair(ec2, key_name):
    try:
        ec2.describe_key_pairs(KeyNames=[key_name])
        return {"message": "Key pair exists."}
    except ClientError as e:
        if 'InvalidKeyPair.NotFound' in str(e):
            key_response = ec2.create_key_pair(KeyName=key_name)
            with open(f"/tmp/{key_name}.pem", "w") as key_file:
                key_file.write(key_response['KeyMaterial'])
            return {"message": f"Key pair '{key_name}' created.", "keyMaterial": key_response['KeyMaterial']}
        else:
            raise

def ensure_key_pair(ec2, key_name):
    try:
        ec2.describe_key_pairs(KeyNames=[key_name])
        return {"message": "Key pair exists."}
    except ClientError as e:
        if 'InvalidKeyPair.NotFound' in str(e):
            key_response = ec2.create_key_pair(KeyName=key_name)
            with open(f"/tmp/{key_name}.pem", "w") as key_file:
                key_file.write(key_response['KeyMaterial'])
            return {"message": f"Key pair '{key_name}' created.", "keyMaterial": key_response['KeyMaterial']}
        else:
            raise

def launch_instances():
    ec2 = get_ec2_client(region_name)
    try:
        key_result = ensure_key_pair(ec2, key_name)
        
        response = ec2.run_instances(
            InstanceType=instance_type,
            ImageId=image_id,
            MinCount=num_instances,
            MaxCount=num_instances,
            KeyName=key_name,
            SecurityGroupIds=[security_group_id],
            BlockDeviceMappings=[
                {
                    'DeviceName': '/dev/xvda',
                    'Ebs': {
                        'VolumeSize': volume_size,
                        'VolumeType': 'gp2',
                        'DeleteOnTermination': True
                    }
                }
            ],
            TagSpecifications=[
                {
            'ResourceType': 'instance',
            'Tags': [{'Key': 'Name', 'Value': instance_name}]
        }
    ]
)

        instance_ids = [inst['InstanceId'] for inst in response['Instances']]
        ec2.get_waiter('instance_running').wait(InstanceIds=instance_ids)

        details = ec2.describe_instances(InstanceIds=instance_ids)
        result_list = []
        for res in details['Reservations']:
            for inst in res['Instances']:
                result_list.append({
                    'InstanceID': inst['InstanceId'],
                    'State': inst['State']['Name'],
                    'PublicIP': inst.get('PublicIpAddress', 'Pending'),
                    'LaunchTime': str(inst['LaunchTime'])
                })
        return json.dumps({
            "keyPairMessage": key_result['message'],
            "instances": result_list,
            "privateKey": key_result.get('keyMaterial')  # Optional: can remove this from response for security
        })
    except ClientError as e:
        return json.dumps({"error": str(e)})

def manage_instance(action):
    ec2 = get_ec2_client(region_name)
    try:
        if action == "start":
            ec2.start_instances(InstanceIds=[instance_id])
        elif action == "stop":
            ec2.stop_instances(InstanceIds=[instance_id])
        elif action == "terminate":
            ec2.terminate_instances(InstanceIds=[instance_id])
        return json.dumps({"message": f"{action.capitalize()} request sent for instance {instance_id}"})
    except ClientError as e:
        return json.dumps({"error": str(e)})

def list_instances():
    ec2 = get_ec2_client(region_name if region_name else 'us-east-1')
    try:
        instances = []
        response = ec2.describe_instances()
        for reservation in response['Reservations']:
            for inst in reservation['Instances']:
                instances.append({
                    "InstanceId": inst['InstanceId'],
                    "InstanceType": inst['InstanceType'],
                    "State": inst['State']['Name'],
                    "PublicIpAddress": inst.get('PublicIpAddress', ''),
                    "LaunchTime": str(inst['LaunchTime'])
                })
        return json.dumps({"instances": instances})
    except ClientError as e:
        return json.dumps({"error": str(e)})

def json_serial(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def get_instance_metadata():
    ec2 = get_ec2_client(region_name if region_name else 'us-east-1')
    try:
        if not instance_id:
            return json.dumps({"error": "Missing instanceId"})
        response = ec2.describe_instances(InstanceIds=[instance_id])
        if not response['Reservations'] or not response['Reservations'][0]['Instances']:
            return json.dumps({"error": "Instance not found"})
        metadata = response['Reservations'][0]['Instances'][0]
        return json.dumps({"metadata": metadata}, default=json_serial)
    except ClientError as e:
        return json.dumps({"error": str(e)})

# Router
if action == "metadata":
    print(get_instance_metadata())
elif action == "list":
    print(list_instances())
elif action in ["start", "stop", "terminate"]:
    print(manage_instance(action))
elif all([instance_type, image_id, region_name, key_name, security_group_id]):
    print(launch_instances())
else:
    print(json.dumps({"error": "Missing required fields"}))
