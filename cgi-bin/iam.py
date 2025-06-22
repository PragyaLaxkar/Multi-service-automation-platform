#!/usr/bin/python3
print("Access-Control-Allow-Origin: *")
print("Access-Control-Allow-Methods: POST, GET, OPTIONS")
print("Content-type: text/html")
print()

import boto3
import cgi
import json
import sys
import csv
import io

form = cgi.FieldStorage()
name = form.getvalue("name")
action = form.getvalue("action")
policy_arn = form.getvalue("policy_arn")
group_name = form.getvalue("group_name")
key_id = form.getvalue("key_id")

access_key = ''  # Replace with actual access key
secret_key = ''  # Replace with actual secret key

session = boto3.Session(
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    region_name='ap-south-1'
)

iam_client = session.client('iam')

def success(msg):
    print(f"<div class='alert alert-success'>{msg}</div>")

def error(msg):
    print(f"<div class='alert alert-danger'>Error: {msg}</div>")

try:
    if action == "create":
        iam_client.create_user(UserName=name)
        success(f"IAM user '{name}' created successfully!")

    elif action == "delete":
        iam_client.delete_user(UserName=name)
        success(f"IAM user '{name}' deleted successfully!")

    elif action == "list-users" or action == "list_users":
        response = iam_client.list_users()
        users = response.get('Users', [])
        user_list = [{
            'UserName': u['UserName'],
            'UserId': u['UserId'],
            'Arn': u['Arn'],
            'CreateDate': str(u['CreateDate'])
        } for u in users]
        print(json.dumps(user_list))
        sys.exit(0)

    elif action == "attach_policy":
        iam_client.attach_user_policy(UserName=name, PolicyArn=policy_arn)
        success(f"Policy attached to '{name}'")

    elif action == "detach_policy":
        iam_client.detach_user_policy(UserName=name, PolicyArn=policy_arn)
        success(f"Policy detached from '{name}'")

    elif action == "list-policies" or action == "list_policies":
        policies = iam_client.list_policies(Scope='AWS', MaxItems=1000)
        policy_list = [
            {"PolicyName": pol['PolicyName'], "Arn": pol['Arn']} for pol in policies['Policies']
        ]
        print(json.dumps(policy_list))
        sys.exit(0)

    elif action == "create_access_key":
        response = iam_client.create_access_key(UserName=name)
        print(json.dumps(response['AccessKey']))

    elif action == "delete_access_key":
        iam_client.delete_access_key(UserName=name, AccessKeyId=key_id)
        success(f"Access Key {key_id} deleted for '{name}'")

    elif action == "list_access_keys":
        response = iam_client.list_access_keys(UserName=name)
        print(json.dumps(response['AccessKeyMetadata']))

    elif action == "create_login_profile":
        iam_client.create_login_profile(UserName=name, Password='YourPassword123', PasswordResetRequired=True)
        success(f"Login profile created for '{name}'")

    elif action == "delete_login_profile":
        iam_client.delete_login_profile(UserName=name)
        success(f"Login profile deleted for '{name}'")

    elif action == "list_attached_policies" or action == "list-attached-policies":
        response = iam_client.list_attached_user_policies(UserName=name)
        attached_policies = response.get('AttachedPolicies', [])
        policy_list = [{
            'PolicyName': p['PolicyName'],
            'PolicyArn': p['PolicyArn']
        } for p in attached_policies]
        print(json.dumps(policy_list))
        sys.exit(0)

    elif action == "get-user" or action == "get_user":
        response = iam_client.get_user(UserName=name)
        user = response['User']
        # Convert datetime fields to string for JSON serialization
        for k, v in user.items():
            if hasattr(v, 'isoformat'):
                user[k] = v.isoformat()
        print(json.dumps(user))
        sys.exit(0)

    elif action == "create_group":
        iam_client.create_group(GroupName=group_name)
        success(f"Group '{group_name}' created successfully!")

    elif action == "delete_group":
        iam_client.delete_group(GroupName=group_name)
        success(f"Group '{group_name}' deleted successfully!")

    elif action == "add_user_to_group":
        iam_client.add_user_to_group(GroupName=group_name, UserName=name)
        success(f"User '{name}' added to group '{group_name}'")

    elif action == "remove_user_from_group":
        iam_client.remove_user_from_group(GroupName=group_name, UserName=name)
        success(f"User '{name}' removed from group '{group_name}'")

    elif action == "attach_group_policy":
        iam_client.attach_group_policy(GroupName=group_name, PolicyArn=policy_arn)
        success(f"Policy attached to group '{group_name}'")

    elif action == "detach_group_policy":
        iam_client.detach_group_policy(GroupName=group_name, PolicyArn=policy_arn)
        success(f"Policy detached from group '{group_name}'")

    elif action == "credential_report":
        iam_client.generate_credential_report()
        report = iam_client.get_credential_report()['Content']
        print("<pre>" + report.decode('utf-8') + "</pre>")

    elif action == "download_users_json":
        response = iam_client.list_users()
        users = [
            {"UserName": user['UserName'], "CreateDate": str(user['CreateDate'])}
            for user in response['Users']
        ]
        print(json.dumps(users))

    elif action == "download_users_csv":
        response = iam_client.list_users()
        users = response['Users']
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['UserName', 'CreateDate'])
        writer.writeheader()
        for user in users:
            writer.writerow({
                'UserName': user['UserName'],
                'CreateDate': user['CreateDate']
            })
        print(output.getvalue())

    elif action == "get_policies":
        policies = iam_client.list_policies(Scope='AWS', OnlyAttached=False)
        policy_list = [{'PolicyName': p['PolicyName'], 'Arn': p['Arn']} for p in policies['Policies']]
        print(json.dumps(policy_list))

    else:
        error(f"Invalid action '{action}' specified.")

except Exception as e:
    error(str(e))
