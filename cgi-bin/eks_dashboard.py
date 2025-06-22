#!/usr/bin/env python3
import boto3
import json
import cgi
import cgitb
from botocore.exceptions import ClientError
import datetime

cgitb.enable()
print("Content-Type: application/json\n")

form = cgi.FieldStorage()
region_name = form.getvalue("regionName", "us-east-1")
action = form.getvalue("action")
cluster_name = form.getvalue("clusterName")

AWS_KEY = ""
AWS_SECRET = ""

def get_eks_client(region):
    return boto3.client("eks", aws_access_key_id=AWS_KEY, aws_secret_access_key=AWS_SECRET, region_name=region)

def get_cloudwatch_client(region):
    return boto3.client("cloudwatch", aws_access_key_id=AWS_KEY, aws_secret_access_key=AWS_SECRET, region_name=region)

def list_clusters(region):
    eks = get_eks_client(region)
    try:
        clusters = []
        names = eks.list_clusters()['clusters']
        for name in names:
            desc = eks.describe_cluster(name=name)['cluster']
            clusters.append({
                'name': name,
                'status': desc['status'],
                'version': desc['version'],
                'endpoint': desc.get('endpoint', ''),
                'createdAt': str(desc.get('createdAt', '')),
                'vpc': desc.get('resourcesVpcConfig', {}).get('vpcId', ''),
                'subnets': desc.get('resourcesVpcConfig', {}).get('subnetIds', []),
                'arn': desc['arn']
            })
        return json.dumps({'clusters': clusters}, default=str)
    except Exception as e:
        return json.dumps({'error': str(e)})

def describe_cluster(region, cluster_name):
    eks = get_eks_client(region)
    try:
        desc = eks.describe_cluster(name=cluster_name)['cluster']
        return json.dumps({'metadata': desc}, default=str)
    except Exception as e:
        return json.dumps({'error': str(e)})

def delete_cluster(region, cluster_name):
    eks = get_eks_client(region)
    try:
        eks.delete_cluster(name=cluster_name)
        return json.dumps({'message': f'Cluster {cluster_name} deletion initiated.'})
    except Exception as e:
        return json.dumps({'error': str(e)})

def list_nodegroups(region, cluster_name):
    eks = get_eks_client(region)
    try:
        nodegroups = eks.list_nodegroups(clusterName=cluster_name)['nodegroups']
        result = []
        for ng_name in nodegroups:
            ng = eks.describe_nodegroup(clusterName=cluster_name, nodegroupName=ng_name)['nodegroup']
            result.append({
                'name': ng_name,
                'status': ng['status'],
                'scalingConfig': ng.get('scalingConfig', {}),
                'instanceTypes': ng.get('instanceTypes', []),
                'subnets': ng.get('subnets', []),
                'nodeRole': ng.get('nodeRole', ''),
                'amiType': ng.get('amiType', ''),
                'createdAt': str(ng.get('createdAt', '')),
                'tags': ng.get('tags', {})
            })
        return json.dumps({'nodegroups': result}, default=str)
    except Exception as e:
        return json.dumps({'error': str(e)})

def nodegroup_details(region, cluster_name, nodegroup_name):
    eks = get_eks_client(region)
    try:
        ng = eks.describe_nodegroup(clusterName=cluster_name, nodegroupName=nodegroup_name)['nodegroup']
        return json.dumps({'nodegroup': ng}, default=str)
    except Exception as e:
        return json.dumps({'error': str(e)})

def get_metric(region, cluster_name, metric_name, nodegroup_name=None):
    cw = get_cloudwatch_client(region)
    dims = [
        {'Name': 'ClusterName', 'Value': cluster_name}
    ]
    if nodegroup_name:
        dims.append({'Name': 'NodegroupName', 'Value': nodegroup_name})
    try:
        response = cw.get_metric_statistics(
            Namespace='AWS/EKS',
            MetricName=metric_name,
            Dimensions=dims,
            StartTime=datetime.datetime.utcnow() - datetime.timedelta(hours=1),
            EndTime=datetime.datetime.utcnow(),
            Period=300,
            Statistics=['Average']
        )
        datapoints = response.get('Datapoints', [])
        datapoints.sort(key=lambda x: x['Timestamp'])
        return [
            {'Timestamp': dp['Timestamp'].isoformat(), 'Average': dp['Average']} for dp in datapoints
        ]
    except Exception as e:
        return [{'Error': str(e)}]

def get_events(region, cluster_name, nodegroup_name=None):
    eks = get_eks_client(region)
    try:
        if nodegroup_name:
            ng = eks.describe_nodegroup(clusterName=cluster_name, nodegroupName=nodegroup_name)['nodegroup']
            events = ng.get('health', {}).get('issues', [])
            return events
        else:
            cl = eks.describe_cluster(name=cluster_name)['cluster']
            return cl.get('health', {}).get('issues', [])
    except Exception as e:
        return [{'Error': str(e)}]

def cluster_health(region, cluster_name):
    eks = get_eks_client(region)
    try:
        cl = eks.describe_cluster(name=cluster_name)['cluster']
        health = cl.get('health', {})
        if not health or not health.get('issues'):
            return 'Healthy'
        return 'Degraded'
    except Exception:
        return 'Unknown'

def nodegroup_health(region, cluster_name, nodegroup_name):
    eks = get_eks_client(region)
    try:
        ng = eks.describe_nodegroup(clusterName=cluster_name, nodegroupName=nodegroup_name)['nodegroup']
        health = ng.get('health', {})
        if not health or not health.get('issues'):
            return 'Healthy'
        return 'Degraded'
    except Exception:
        return 'Unknown'

def security_access(region, cluster_name, nodegroup_name=None):
    eks = get_eks_client(region)
    try:
        if nodegroup_name:
            ng = eks.describe_nodegroup(clusterName=cluster_name, nodegroupName=nodegroup_name)['nodegroup']
            return json.dumps({
                'nodeRole': ng.get('nodeRole', ''),
                'amiType': ng.get('amiType', ''),
                'oidc': ng.get('tags', {}).get('eks.amazonaws.com/oidc-enabled', 'Unknown')
            })
        else:
            cl = eks.describe_cluster(name=cluster_name)['cluster']
            vpc_cfg = cl.get('resourcesVpcConfig', {})
            endpoint_access = {
                'publicAccess': vpc_cfg.get('endpointPublicAccess', False),
                'privateAccess': vpc_cfg.get('endpointPrivateAccess', False),
                'publicAccessCidrs': vpc_cfg.get('publicAccessCidrs', [])
            }
            oidc = cl.get('identity', {}).get('oidc', {}).get('issuer', 'Not enabled')
            return json.dumps({
                'clusterRole': cl.get('roleArn', ''),
                'endpointAccess': endpoint_access,
                'oidcIssuer': oidc
            })
    except Exception as e:
        return json.dumps({'error': str(e)})

def networking(region, cluster_name):
    eks = get_eks_client(region)
    try:
        cl = eks.describe_cluster(name=cluster_name)['cluster']
        vpc_cfg = cl.get('resourcesVpcConfig', {})
        return json.dumps({
            'vpcId': vpc_cfg.get('vpcId', ''),
            'subnetIds': vpc_cfg.get('subnetIds', []),
            'securityGroupIds': vpc_cfg.get('securityGroupIds', []),
            'endpointPublicAccess': vpc_cfg.get('endpointPublicAccess', False),
            'endpointPrivateAccess': vpc_cfg.get('endpointPrivateAccess', False),
            'publicAccessCidrs': vpc_cfg.get('publicAccessCidrs', [])
        })
    except Exception as e:
        return json.dumps({'error': str(e)})

EC2_PRICING = {
    't3.medium': 0.0416, 't3.large': 0.0832, 't2.micro': 0.0116, 't2.small': 0.023, 't2.medium': 0.0464, 't2.large': 0.0928
}
EKS_CONTROL_PLANE_COST_PER_HOUR = 0.10  # $0.10 per hour per cluster

def cost_utilization(region, cluster_name, nodegroup_name=None):
    eks = get_eks_client(region)
    ec2 = boto3.client("ec2", aws_access_key_id=AWS_KEY, aws_secret_access_key=AWS_SECRET, region_name=region)
    try:
        if nodegroup_name:
            ng = eks.describe_nodegroup(clusterName=cluster_name, nodegroupName=nodegroup_name)['nodegroup']
            instance_types = ng.get('instanceTypes', ['t3.medium'])
            scaling = ng.get('scalingConfig', {})
            desired = scaling.get('desiredSize', 2)
            price_per_hour = sum(EC2_PRICING.get(t, 0.1) for t in instance_types) * desired
            # Node count and instance info
            asg_names = ng.get('resources', {}).get('autoScalingGroups', [])
            node_count = desired
            return json.dumps({
                'estimatedHourlyCost': round(price_per_hour, 4),
                'estimatedMonthlyCost': round(price_per_hour * 24 * 30, 2),
                'nodeCount': node_count,
                'instanceTypes': instance_types
            })
        else:
            # Cluster cost is $0.10/hr + sum of node group costs
            cl = eks.describe_cluster(name=cluster_name)['cluster']
            nodegroups = eks.list_nodegroups(clusterName=cluster_name)['nodegroups']
            total_node_cost = 0
            nodegroup_details = []
            for ng_name in nodegroups:
                ng = eks.describe_nodegroup(clusterName=cluster_name, nodegroupName=ng_name)['nodegroup']
                instance_types = ng.get('instanceTypes', ['t3.medium'])
                scaling = ng.get('scalingConfig', {})
                desired = scaling.get('desiredSize', 2)
                ng_cost = sum(EC2_PRICING.get(t, 0.1) for t in instance_types) * desired
                total_node_cost += ng_cost
                nodegroup_details.append({'name': ng_name, 'nodeCount': desired, 'instanceTypes': instance_types, 'hourlyCost': round(ng_cost, 4)})
            hourly = EKS_CONTROL_PLANE_COST_PER_HOUR + total_node_cost
            return json.dumps({
                'estimatedHourlyCost': round(hourly, 4),
                'estimatedMonthlyCost': round(hourly * 24 * 30, 2),
                'nodegroups': nodegroup_details
            })
    except Exception as e:
        return json.dumps({'error': str(e)})

# Router
if action == 'list':
    print(list_clusters(region_name))
elif action == 'describe' and cluster_name:
    print(describe_cluster(region_name, cluster_name))
elif action == 'delete' and cluster_name:
    print(delete_cluster(region_name, cluster_name))
elif action == 'list_nodegroups' and cluster_name:
    print(list_nodegroups(region_name, cluster_name))
elif action == 'nodegroup_details' and cluster_name and form.getvalue('nodegroupName'):
    print(nodegroup_details(region_name, cluster_name, form.getvalue('nodegroupName')))
elif action == 'metrics' and cluster_name:
    metric = form.getvalue('metric')
    nodegroup = form.getvalue('nodegroupName')
    print(json.dumps({'metrics': get_metric(region_name, cluster_name, metric, nodegroup)}, default=str))
elif action == 'events' and cluster_name:
    nodegroup = form.getvalue('nodegroupName')
    print(json.dumps({'events': get_events(region_name, cluster_name, nodegroup)}, default=str))
elif action == 'health' and cluster_name:
    nodegroup = form.getvalue('nodegroupName')
    if nodegroup:
        print(json.dumps({'health': nodegroup_health(region_name, cluster_name, nodegroup)}))
    else:
        print(json.dumps({'health': cluster_health(region_name, cluster_name)}))
elif action == 'security_access' and cluster_name:
    nodegroup = form.getvalue('nodegroupName')
    print(security_access(region_name, cluster_name, nodegroup))
elif action == 'networking' and cluster_name:
    print(networking(region_name, cluster_name))
elif action == 'cost_utilization' and cluster_name:
    nodegroup = form.getvalue('nodegroupName')
    print(cost_utilization(region_name, cluster_name, nodegroup))
else:
    print(json.dumps({'error': 'Invalid or missing action'}))