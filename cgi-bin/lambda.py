#!/usr/bin/python3
import cgi
import cgitb
import boto3
import json
import base64
import os
import requests
cgitb.enable()
print('Content-Type: application/json\n')

# AWS credentials (replace with your own or use environment variables for security)
AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''

form = cgi.FieldStorage()
action = form.getvalue('action')
region = form.getvalue('region') or 'ap-south-1'
lambda_client = boto3.client(
    'lambda',
    region_name=region,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)
cloudwatch_logs = boto3.client(
    'logs',
    region_name=region,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

def list_functions():
    try:
        resp = lambda_client.list_functions()
        return json.dumps({'functions': resp.get('Functions', [])}, default=str)
    except Exception as e:
        return json.dumps({'error': str(e)})

def create_function():
    try:
        function_name = form.getvalue('functionName')
        runtime = form.getvalue('runtime')
        handler = form.getvalue('handler')
        role = form.getvalue('role')
        description = form.getvalue('description', '')
        timeout = int(form.getvalue('timeout', 3))
        memory_size = int(form.getvalue('memorySize', 128))
        # Environment variables
        env_vars = form.getvalue('envVars', '')
        env_dict = {}
        if env_vars:
            try:
                env_dict = json.loads(env_vars)
            except Exception as e:
                return json.dumps({'error': f'Invalid environment variables JSON: {e}'})
        # Prefer inline code if present
        inline_code = form.getvalue('inlineCode')
        code_bytes = b''
        file_name = ''
        if inline_code:
            # User wrote code in the modal; determine file type
            if runtime.startswith('nodejs'):
                file_name = 'index.js'
            else:
                file_name = 'lambda_function.py'
            with open(f'/tmp/{file_name}', 'w', encoding='utf-8') as f:
                f.write(inline_code)
            import zipfile
            zip_path = f'/tmp/{function_name}.zip'
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                zipf.write(f'/tmp/{file_name}', file_name)
            with open(zip_path, 'rb') as zf:
                code_bytes = zf.read()
            os.remove(f'/tmp/{file_name}')
            os.remove(zip_path)
        elif 'codeFile' in form and form['codeFile'].filename:
            # User uploaded a .js or .py file
            fileitem = form['codeFile']
            file_name = fileitem.filename
            with open(f'/tmp/{file_name}', 'wb') as f:
                f.write(fileitem.file.read())
            import zipfile
            zip_path = f'/tmp/{function_name}.zip'
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                zipf.write(f'/tmp/{file_name}', file_name)
            with open(zip_path, 'rb') as zf:
                code_bytes = zf.read()
            os.remove(f'/tmp/{file_name}')
            os.remove(zip_path)
        else:
            return json.dumps({'error': 'No code provided. Please upload a file or write code.'})
        kwargs = dict(
            FunctionName=function_name,
            Runtime=runtime,
            Role=role,
            Handler=handler,
            Description=description,
            Timeout=timeout,
            MemorySize=memory_size,
            Code={'ZipFile': code_bytes},
            Publish=True
        )
        if env_dict:
            kwargs['Environment'] = {'Variables': env_dict}
        response = lambda_client.create_function(**kwargs)
        return json.dumps({'message': f'Function {function_name} created.'})
    except Exception as e:
        return json.dumps({'error': str(e)})

def function_details():
    try:
        function_name = form.getvalue('functionName')
        resp = lambda_client.get_function(FunctionName=function_name)
        return json.dumps({'details': resp}, default=str)
    except Exception as e:
        return json.dumps({'error': str(e)})

def delete_function():
    try:
        function_name = form.getvalue('functionName')
        lambda_client.delete_function(FunctionName=function_name)
        return json.dumps({'message': f'Function {function_name} deleted.'})
    except Exception as e:
        return json.dumps({'error': str(e)})

def invoke_function():
    try:
        function_name = form.getvalue('functionName')
        payload = form.getvalue('payload', '{}')
        resp = lambda_client.invoke(FunctionName=function_name, Payload=payload, LogType='Tail')
        result = resp['Payload'].read().decode('utf-8')
        logs = base64.b64decode(resp.get('LogResult', '')).decode('utf-8') if 'LogResult' in resp else ''
        return json.dumps({'result': json.loads(result), 'logs': logs})
    except Exception as e:
        return json.dumps({'error': str(e)})

def update_function_code():
    try:
        function_name = form.getvalue('functionName')
        runtime = None
        # Find runtime for handler extension
        for fn in lambda_client.list_functions()['Functions']:
            if fn['FunctionName'] == function_name:
                runtime = fn['Runtime']
                break
        if not runtime:
            return json.dumps({'error': 'Function not found'})
        inline_code = form.getvalue('inlineCode')
        code_bytes = b''
        file_name = ''
        if inline_code:
            if runtime.startswith('nodejs'):
                file_name = 'index.js'
            else:
                file_name = 'lambda_function.py'
            with open(f'/tmp/{file_name}', 'w', encoding='utf-8') as f:
                f.write(inline_code)
            import zipfile
            zip_path = f'/tmp/{function_name}_update.zip'
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                zipf.write(f'/tmp/{file_name}', file_name)
            with open(zip_path, 'rb') as zf:
                code_bytes = zf.read()
            os.remove(f'/tmp/{file_name}')
            os.remove(zip_path)
        elif 'codeFile' in form and form['codeFile'].filename:
            fileitem = form['codeFile']
            file_name = fileitem.filename
            with open(f'/tmp/{file_name}', 'wb') as f:
                f.write(fileitem.file.read())
            import zipfile
            zip_path = f'/tmp/{function_name}_update.zip'
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                zipf.write(f'/tmp/{file_name}', file_name)
            with open(zip_path, 'rb') as zf:
                code_bytes = zf.read()
            os.remove(f'/tmp/{file_name}')
            os.remove(zip_path)
        else:
            return json.dumps({'error': 'No code provided. Please upload a file or write code.'})
        resp = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=code_bytes,
            Publish=True
        )
        return json.dumps({'message': f'Code updated for {function_name}.'})
    except Exception as e:
        return json.dumps({'error': str(e)})

def get_code():
    try:
        import zipfile
        import tempfile
        function_name = form.getvalue('functionName')
        # Get function details to find runtime and code location
        resp = lambda_client.get_function(FunctionName=function_name)
        code_url = resp['Code']['Location']
        runtime = resp['Configuration']['Runtime']
        code_resp = requests.get(code_url)
        if code_resp.status_code == 200:
            # Save ZIP to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_zip:
                tmp_zip.write(code_resp.content)
                tmp_zip_path = tmp_zip.name
            # Extract main code file
            code_file = None
            if runtime.startswith('nodejs'):
                code_file = 'index.js'
            elif runtime.startswith('python'):
                code_file = 'lambda_function.py'
            elif runtime.startswith('java'):
                code_file = None # Java is jar/compiled, skip
            elif runtime.startswith('go'):
                code_file = 'main'
            elif runtime.startswith('ruby'):
                code_file = 'lambda_function.rb'
            code = ''
            if code_file:
                with zipfile.ZipFile(tmp_zip_path, 'r') as zf:
                    try:
                        code = zf.read(code_file).decode('utf-8')
                    except Exception:
                        code = '// Could not extract code file from ZIP.'
            else:
                code = '// Runtime not supported for code preview.'
            os.remove(tmp_zip_path)
            return json.dumps({'code': code})
        else:
            return json.dumps({'error': 'Failed to fetch code from AWS'})
    except Exception as e:
        return json.dumps({'error': str(e)})

def update_function_config():
    try:
        function_name = form.getvalue('functionName')
        region = form.getvalue('region') or 'ap-south-1'
        description = form.getvalue('description', '')
        timeout = int(form.getvalue('timeout', 3))
        memory_size = int(form.getvalue('memorySize', 128))
        env_vars = form.getvalue('envVars', '')
        env_dict = {}
        if env_vars:
            try:
                env_dict = json.loads(env_vars)
            except Exception as e:
                return json.dumps({'error': f'Invalid environment variables JSON: {e}'})
        kwargs = {
            'FunctionName': function_name,
            'Description': description,
            'Timeout': timeout,
            'MemorySize': memory_size
        }
        if env_dict:
            kwargs['Environment'] = {'Variables': env_dict}
        resp = lambda_client.update_function_configuration(**kwargs)
        return json.dumps({'message': f'Config updated for {function_name}.'})
    except Exception as e:
        return json.dumps({'error': str(e)})

def get_logs():
    try:
        function_name = form.getvalue('functionName')
        region = form.getvalue('region') or 'ap-south-1'
        log_group = f'/aws/lambda/{function_name}'
        logs_client = boto3.client(
            'logs',
            region_name=region,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        streams = logs_client.describe_log_streams(logGroupName=log_group, orderBy='LastEventTime', descending=True, limit=1)
        if not streams['logStreams']:
            return json.dumps({'logs': '', 'error': 'No logs found.'})
        log_stream = streams['logStreams'][0]['logStreamName']
        events = logs_client.get_log_events(logGroupName=log_group, logStreamName=log_stream, limit=50)
        logs = '\n'.join([e['message'] for e in events['events']])
        return json.dumps({'logs': logs})
    except Exception as e:
        return json.dumps({'error': str(e)})

def set_state():
    try:
        function_name = form.getvalue('functionName')
        region = form.getvalue('region') or 'ap-south-1'
        enabled = form.getvalue('enabled') == '1'
        lambda_client_reg = boto3.client(
            'lambda',
            region_name=region,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        # List all event source mappings for this function
        mappings = lambda_client_reg.list_event_source_mappings(FunctionName=function_name)
        count = 0
        for mapping in mappings.get('EventSourceMappings', []):
            uuid = mapping['UUID']
            lambda_client_reg.update_event_source_mapping(UUID=uuid, Enabled=enabled)
            count += 1
        if count == 0:
            msg = 'No event source mappings found. Function cannot be disabled directly, but is still invokable.'
        else:
            msg = f'Set {count} event source mapping(s) to {"enabled" if enabled else "disabled"}.'
        return json.dumps({'message': msg})
    except Exception as e:
        return json.dumps({'error': str(e)})

# Version and Alias Management

def publish_version():
    try:
        function_name = form.getvalue('functionName')
        region = form.getvalue('region') or 'ap-south-1'
        lambda_client_reg = boto3.client(
            'lambda',
            region_name=region,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        resp = lambda_client_reg.publish_version(FunctionName=function_name)
        return json.dumps({'message': f'Published new version: {resp["Version"]}', 'version': resp["Version"]})
    except Exception as e:
        return json.dumps({'error': str(e)})

def list_versions():
    try:
        function_name = form.getvalue('functionName')
        region = form.getvalue('region') or 'ap-south-1'
        lambda_client_reg = boto3.client(
            'lambda',
            region_name=region,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        resp = lambda_client_reg.list_versions_by_function(FunctionName=function_name)
        return json.dumps({'versions': resp['Versions']})
    except Exception as e:
        return json.dumps({'error': str(e)})

def list_aliases():
    try:
        function_name = form.getvalue('functionName')
        region = form.getvalue('region') or 'ap-south-1'
        lambda_client_reg = boto3.client(
            'lambda',
            region_name=region,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        resp = lambda_client_reg.list_aliases(FunctionName=function_name)
        return json.dumps({'aliases': resp['Aliases']})
    except Exception as e:
        return json.dumps({'error': str(e)})

def create_alias():
    try:
        function_name = form.getvalue('functionName')
        alias_name = form.getvalue('aliasName')
        version = form.getvalue('version')
        description = form.getvalue('description', '')
        region = form.getvalue('region') or 'ap-south-1'
        lambda_client_reg = boto3.client(
            'lambda',
            region_name=region,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        resp = lambda_client_reg.create_alias(FunctionName=function_name, Name=alias_name, FunctionVersion=version, Description=description)
        return json.dumps({'message': f'Alias {alias_name} created for version {version}.'})
    except Exception as e:
        return json.dumps({'error': str(e)})

def update_alias():
    try:
        function_name = form.getvalue('functionName')
        alias_name = form.getvalue('aliasName')
        version = form.getvalue('version')
        description = form.getvalue('description', '')
        region = form.getvalue('region') or 'ap-south-1'
        lambda_client_reg = boto3.client(
            'lambda',
            region_name=region,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        resp = lambda_client_reg.update_alias(FunctionName=function_name, Name=alias_name, FunctionVersion=version, Description=description)
        return json.dumps({'message': f'Alias {alias_name} updated to version {version}.'})
    except Exception as e:
        return json.dumps({'error': str(e)})

# Router
if action == 'list':
    print(list_functions())
elif action == 'create':
    print(create_function())
elif action == 'details':
    print(function_details())
elif action == 'delete':
    print(delete_function())
elif action == 'invoke':
    print(invoke_function())
elif action == 'update_code':
    print(update_function_code())
elif action == 'get_code':
    print(get_code())
elif action == 'update_config':
    print(update_function_config())
elif action == 'get_logs':
    print(get_logs())
elif action == 'set_state':
    print(set_state())
elif action == 'publish_version':
    print(publish_version())
elif action == 'list_versions':
    print(list_versions())
elif action == 'list_aliases':
    print(list_aliases())
elif action == 'create_alias':
    print(create_alias())
elif action == 'update_alias':
    print(update_alias())
else:
    print(json.dumps({'error': 'Invalid or missing action'}))