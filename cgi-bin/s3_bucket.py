#!/usr/bin/env python3

import boto3
import cgi
import cgitb
import json
import os
import sys
from urllib.parse import unquote

cgitb.enable()
print("Content-Type: application/json\n")

AWS_ACCESS_KEY = ""
AWS_SECRET_KEY = ""

form = cgi.FieldStorage()
action = form.getvalue("action")
bucket_name = form.getvalue("bucket_name")
region = form.getvalue("region")
key = form.getvalue("key")
prefix = form.getvalue("prefix")
policy = form.getvalue("policy")
acl = form.getvalue("acl")

# S3 client (region is required for some ops)
def get_s3(region=None):
    return boto3.client('s3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=region or 'us-east-1')

try:
    if action == "list_buckets":
        s3 = get_s3()
        buckets = s3.list_buckets().get('Buckets', [])
        print(json.dumps({"buckets": [b['Name'] for b in buckets]}))

    elif action == "list_objects":
        s3 = get_s3(region)
        if not bucket_name:
            print(json.dumps({"error": "Bucket name required"}))
            sys.exit()
        resp = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix or "")
        objs = resp.get('Contents', [])
        print(json.dumps({"objects": [o['Key'] for o in objs]}))

    elif action == "upload":
        s3 = get_s3(region)
        if not bucket_name or 'file' not in form:
            print(json.dumps({"error": "Bucket and file required"}))
            sys.exit()
        fileitem = form['file']
        filename = fileitem.filename
        s3.upload_fileobj(fileitem.file, bucket_name, filename)
        print(json.dumps({"message": f"Uploaded {filename} to {bucket_name}"}))

    elif action == "download":
        s3 = get_s3(region)
        if not bucket_name or not key:
            print(json.dumps({"error": "Bucket and key required"}))
            sys.exit()
        url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': key}, ExpiresIn=300)
        print(json.dumps({"url": url}))

    elif action == "delete_object":
        s3 = get_s3(region)
        if not bucket_name or not key:
            print(json.dumps({"error": "Bucket and key required"}))
            sys.exit()
        s3.delete_object(Bucket=bucket_name, Key=key)
        print(json.dumps({"message": f"Deleted {key} from {bucket_name}"}))

    elif action == "create_bucket":
        s3 = get_s3(region)
        if not bucket_name or not region:
            print(json.dumps({"error": "Bucket name and region required"}))
            sys.exit()
        if region == 'us-east-1':
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': region})
        print(json.dumps({"message": f"Bucket '{bucket_name}' created in {region}"}))

    elif action == "delete_bucket":
        s3 = get_s3(region)
        if not bucket_name:
            print(json.dumps({"error": "Bucket name required"}))
            sys.exit()
        s3.delete_bucket(Bucket=bucket_name)
        print(json.dumps({"message": f"Bucket '{bucket_name}' deleted."}))

    elif action == "set_bucket_policy":
        s3 = get_s3(region)
        if not bucket_name or not policy:
            print(json.dumps({"error": "Bucket and policy required"}))
            sys.exit()
        s3.put_bucket_policy(Bucket=bucket_name, Policy=policy)
        print(json.dumps({"message": "Policy set."}))

    elif action == "get_bucket_policy":
        s3 = get_s3(region)
        if not bucket_name:
            print(json.dumps({"error": "Bucket name required"}))
            sys.exit()
        pol = s3.get_bucket_policy(Bucket=bucket_name)
        print(json.dumps({"policy": pol['Policy']}))

    elif action == "generate_presigned_url":
        s3 = get_s3(region)
        if not bucket_name or not key:
            print(json.dumps({"error": "Bucket and key required"}))
            sys.exit()
        url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': key}, ExpiresIn=3600)
        print(json.dumps({"url": url}))

    elif action == "set_object_acl":
        s3 = get_s3(region)
        if not bucket_name or not key or not acl:
            print(json.dumps({"error": "Bucket, key, and ACL required"}))
            sys.exit()
        s3.put_object_acl(Bucket=bucket_name, Key=key, ACL=acl)
        print(json.dumps({"message": f"ACL '{acl}' set for {key}"}))

    elif action == "get_object_metadata":
        s3 = get_s3(region)
        if not bucket_name or not key:
            print(json.dumps({"error": "Bucket and key required"}))
            sys.exit()
        meta = s3.head_object(Bucket=bucket_name, Key=key)
        print(json.dumps({"metadata": {
            "ContentLength": meta.get('ContentLength'),
            "LastModified": str(meta.get('LastModified')),
            "StorageClass": meta.get('StorageClass', 'STANDARD'),
            "ContentType": meta.get('ContentType'),
        }}))

    elif action == "search_objects":
        s3 = get_s3(region)
        if not bucket_name:
            print(json.dumps({"error": "Bucket name required"}))
            sys.exit()
        resp = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix or "")
        objs = resp.get('Contents', [])
        print(json.dumps({"objects": [o['Key'] for o in objs]}))

    elif action == "copy_object":
        s3 = get_s3(region)
        dest_bucket = form.getvalue("dest_bucket")
        dest_key = form.getvalue("dest_key")
        if not bucket_name or not key or not dest_bucket or not dest_key:
            print(json.dumps({"error": "Source and destination required"}))
            sys.exit()
        copy_source = { 'Bucket': bucket_name, 'Key': key }
        s3.copy_object(CopySource=copy_source, Bucket=dest_bucket, Key=dest_key)
        print(json.dumps({"message": f"Copied {key} to {dest_bucket}/{dest_key}"}))

    elif action == "move_object":
        s3 = get_s3(region)
        dest_bucket = form.getvalue("dest_bucket")
        dest_key = form.getvalue("dest_key")
        if not bucket_name or not key or not dest_bucket or not dest_key:
            print(json.dumps({"error": "Source and destination required"}))
            sys.exit()
        copy_source = { 'Bucket': bucket_name, 'Key': key }
        s3.copy_object(CopySource=copy_source, Bucket=dest_bucket, Key=dest_key)
        s3.delete_object(Bucket=bucket_name, Key=key)
        print(json.dumps({"message": f"Moved {key} to {dest_bucket}/{dest_key}"}))

    else:
        print(json.dumps({"error": "Invalid or missing action."}))

except Exception as e:
    print(json.dumps({"error": str(e)}))
