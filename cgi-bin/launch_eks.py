#!/usr/bin/python3
import cgi
import cgitb
import boto3
import json
import sys
cgitb.enable()
print("Content-Type: application/json\n")
sys.stderr = sys.stdout

form = cgi.FieldStorage()
action = form.getvalue('action')
region_name = form.getvalue('regionName', 'us-east-1')

# Helper to get EKS client

def get_eks_client(region):
    return boto3.client(
        'eks',
        aws_access_key_id='',
        aws_secret_access_key='',
        region_name=region
    )

def list_clusters():
    eks = get_eks_client(region_name)
    try:
        clusters = []
        names = eks.list_clusters()['clusters']
        for name in names:
            desc = eks.describe_cluster(name=name)['cluster']
            clusters.append({
                'name': name,
                'status': desc['status'],
                'version': desc['version'],
                'arn': desc['arn']
            })
        return json.dumps({'clusters': clusters})
    except Exception as e:
        return json.dumps({'error': str(e)})

def create_cluster():
    eks = get_eks_client(region_name)
    cluster_name = form.getvalue('clusterName')
    version = form.getvalue('version')
    eks_role_arn = form.getvalue('eksRoleArn')
    subnet_ids = [s.strip() for s in form.getvalue('subnetIds', '').split(',') if s.strip()]
    try:
        resp = eks.create_cluster(
            name=cluster_name,
            version=version,
            roleArn=eks_role_arn,
            resourcesVpcConfig={
                'subnetIds': subnet_ids,
                'endpointPublicAccess': True
            }
        )
        return json.dumps({'message': f'Cluster {cluster_name} launch initiated.'})
    except Exception as e:
        return json.dumps({'error': str(e)})

def create_nodegroup():
    eks = get_eks_client(region_name)
    cluster_name = form.getvalue('clusterName')
    node_group = form.getvalue('nodeGroupName')
    instance_type = form.getvalue('instanceType')
    node_count = int(form.getvalue('nodeCount', 2))
    nodegroup_role_arn = form.getvalue('nodegroupRoleArn')
    subnet_ids = [s.strip() for s in form.getvalue('subnetIds', '').split(',') if s.strip()]
    try:
        eks.create_nodegroup(
            clusterName=cluster_name,
            nodegroupName=node_group,
            scalingConfig={'minSize': 1, 'maxSize': node_count, 'desiredSize': node_count},
            diskSize=20,
            subnets=subnet_ids,
            instanceTypes=[instance_type],
            nodeRole=nodegroup_role_arn
        )
        return json.dumps({'message': f'Node group {node_group} creation initiated for cluster {cluster_name}.'})
    except Exception as e:
        return json.dumps({'error': str(e)})

def describe_cluster():
    eks = get_eks_client(region_name)
    cluster_name = form.getvalue('clusterName')
    try:
        desc = eks.describe_cluster(name=cluster_name)['cluster']
        return json.dumps({'metadata': desc}, default=str)
    except Exception as e:
        return json.dumps({'error': str(e)})

def delete_cluster():
    eks = get_eks_client(region_name)
    cluster_name = form.getvalue('clusterName')
    try:
        eks.delete_cluster(name=cluster_name)
        return json.dumps({'message': f'Cluster {cluster_name} deletion initiated.'})
    except Exception as e:
        return json.dumps({'error': str(e)})

def list_nodegroups():
    eks = get_eks_client(region_name)
    cluster_name = form.getvalue('clusterName')
    try:
        nodegroups = eks.list_nodegroups(clusterName=cluster_name)['nodegroups']
        return json.dumps({'nodegroups': nodegroups})
    except Exception as e:
        return json.dumps({'error': str(e)})

def delete_nodegroup():
    eks = get_eks_client(region_name)
    cluster_name = form.getvalue('clusterName')
    node_group = form.getvalue('nodeGroupName')
    try:
        eks.delete_nodegroup(clusterName=cluster_name, nodegroupName=node_group)
        return json.dumps({'message': f'Node group {node_group} deletion initiated for cluster {cluster_name}.'})
    except Exception as e:
        return json.dumps({'error': str(e)})

def scale_nodegroup():
    eks = get_eks_client(region_name)
    cluster_name = form.getvalue('clusterName')
    node_group = form.getvalue('nodeGroupName')
    min_size = int(form.getvalue('minSize', 1))
    max_size = int(form.getvalue('maxSize', 3))
    desired_size = int(form.getvalue('desiredSize', min_size))
    try:
        eks.update_nodegroup_config(
            clusterName=cluster_name,
            nodegroupName=node_group,
            scalingConfig={
                'minSize': min_size,
                'maxSize': max_size,
                'desiredSize': desired_size
            }
        )
        return json.dumps({'message': f'Node group {node_group} scaling update initiated for cluster {cluster_name}.'})
    except Exception as e:
        return json.dumps({'error': str(e)})

def list_vpcs():
    ec2 = boto3.client(
        'ec2',
        aws_access_key_id='AKIA4MI2J4VQ3FZRJZJX',
        aws_secret_access_key='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',
        region_name=region_name
    )
    try:
        vpcs = ec2.describe_vpcs()['Vpcs']
        vpc_list = [{'VpcId': v['VpcId'], 'CidrBlock': v['CidrBlock']} for v in vpcs]
        return json.dumps({'vpcs': vpc_list})
    except Exception as e:
        return json.dumps({'error': str(e)})

def list_subnets():
    ec2 = boto3.client(
        'ec2',
        aws_access_key_id='AKIA4MI2J4VQ3FZRJZJX',
        aws_secret_access_key='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',
        region_name=region_name
    )
    vpc_id = form.getvalue('vpcId')
    try:
        subnets = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['Subnets']
        subnet_list = [{'SubnetId': s['SubnetId'], 'CidrBlock': s['CidrBlock']} for s in subnets]
        return json.dumps({'subnets': subnet_list})
    except Exception as e:
        return json.dumps({'error': str(e)})

def eks_addons():
    eks = get_eks_client(region_name)
    cluster_name = form.getvalue('clusterName')
    addon_name = form.getvalue('addonName')
    action_type = form.getvalue('addonAction')  # enable/disable
    try:
        if action_type == 'enable':
            eks.create_addon(
                clusterName=cluster_name,
                addonName=addon_name
            )
            return json.dumps({'message': f'Addon {addon_name} enabled for cluster {cluster_name}.'})
        elif action_type == 'disable':
            eks.delete_addon(
                clusterName=cluster_name,
                addonName=addon_name
            )
            return json.dumps({'message': f'Addon {addon_name} disabled for cluster {cluster_name}.'})
        else:
            return json.dumps({'error': 'Invalid addon action'})
    except Exception as e:
        return json.dumps({'error': str(e)})

def upgrade_cluster():
    eks = get_eks_client(region_name)
    cluster_name = form.getvalue('clusterName')
    version = form.getvalue('version')
    try:
        eks.update_cluster_version(
            name=cluster_name,
            version=version
        )
        return json.dumps({'message': f'Cluster {cluster_name} upgrade to version {version} initiated.'})
    except Exception as e:
        return json.dumps({'error': str(e)})

def save_template():
    import os
    config = form.getvalue('config')
    name = form.getvalue('templateName')
    try:
        with open(f'/tmp/eks_template_{name}.json', 'w') as f:
            f.write(config)
        return json.dumps({'message': f'Template {name} saved.'})
    except Exception as e:
        return json.dumps({'error': str(e)})

def load_template():
    name = form.getvalue('templateName')
    try:
        with open(f'/tmp/eks_template_{name}.json', 'r') as f:
            config = f.read()
        return json.dumps({'config': config})
    except Exception as e:
        return json.dumps({'error': str(e)})

# Router
if action == 'list':
    print(list_clusters())
elif action == 'create':
    print(create_cluster())
elif action == 'create_nodegroup':
    print(create_nodegroup())
elif action == 'describe':
    print(describe_cluster())
elif action == 'delete':
    print(delete_cluster())
elif action == 'list_nodegroups':
    print(list_nodegroups())
elif action == 'delete_nodegroup':
    print(delete_nodegroup())
elif action == 'scale_nodegroup':
    print(scale_nodegroup())
elif action == 'list_vpcs':
    print(list_vpcs())
elif action == 'list_subnets':
    print(list_subnets())
elif action == 'eks_addons':
    print(eks_addons())
elif action == 'upgrade_cluster':
    print(upgrade_cluster())
elif action == 'save_template':
    print(save_template())
elif action == 'load_template':
    print(load_template())
else:
    print(json.dumps({'error': 'Invalid or missing action'}))