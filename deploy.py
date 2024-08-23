import argparse
import boto3
import os
import random
import requests
import string
import subprocess
import yaml

def create_key_pair(key_name, key_file_path, region):
    ec2 = boto3.client('ec2', region_name=region)
    response = ec2.create_key_pair(KeyName=key_name)
    
    with open(key_file_path, 'w') as key_file:
        key_file.write(response['KeyMaterial'])
    
    os.chmod(key_file_path, 0o400)
    print(f"Key pair {key_name} created and saved to {key_file_path}")

def run_cloudformation(stack_name, template_file, key_name, region):
    print(f"Creating CloudFormation stack {stack_name}...")
    subprocess.run([
        'aws', 'cloudformation', 'create-stack',
        '--stack-name', stack_name,
        '--template-body', f'file://{template_file}',
        '--parameters', f'ParameterKey=KeyName,ParameterValue={key_name}',
        '--region', region,
        '--no-cli-pager'
    ], check=True)
    # Wait for the creation to complete
    print(f"Waiting for stack {stack_name} to be created...")
    subprocess.run([
        'aws', 'cloudformation', 'wait', 'stack-create-complete',
        '--stack-name', stack_name,
        '--region', region,
        '--no-cli-pager'
    ], check=True)
    print(f"CloudFormation stack {stack_name} created")

def get_instance_public_ip(stack_name, region):
    ec2 = boto3.client('ec2', region_name=region)
    stack = boto3.client('cloudformation', region_name=region).describe_stack_resources(StackName=stack_name)
    instance_id = next(
        r['PhysicalResourceId'] for r in stack['StackResources'] if r['ResourceType'] == 'AWS::EC2::Instance'
    )
    reservations = ec2.describe_instances(InstanceIds=[instance_id])
    public_ip = reservations['Reservations'][0]['Instances'][0]['PublicIpAddress']
    print(f"EC2 instance with ID {instance_id} has public IP: {public_ip}")
    return public_ip

def get_wordpress_salts():
    # Step 1: Call the WordPress Salts API
    url = "https://api.wordpress.org/secret-key/1.1/salt/"
    response = requests.get(url)
    
    # Step 2: Ensure the request was successful
    if response.status_code != 200:
        raise Exception(f"Failed to retrieve salts. Status code: {response.status_code}")
    
    # Step 3: Parse the response and extract salts into a list
    salts = []
    for line in response.text.splitlines():
        if "define" in line:
            # Extract the salt value within single quotes
            salt_value = line.split("'")[3]
            salts.append(salt_value)
    
    return salts

def write_selected_args_to_yaml(args, key_file_path, public_ip, output_file):
    # Get the WordPress salts and put them in a list
    salts = get_wordpress_salts()
    
    # Dictionary to map command-line argument names and WordPress salts to YAML keys
    yaml_data = {
        'HOST_IP': public_ip,
        'MY_DOMAIN': args.domain,
        'MY_EMAIL': args.email,
        'WPDB_HOST': args.db_host,
        'WPDB_NAME': args.db_name,
        'WPDB_ROOT_NAME': args.db_root_name,
        'WPDB_ROOT_PASSWORD': args.db_root_password,
        'WPDB_USER_NAME': args.db_user_name,
        'WPDB_USER_PASSWORD': args.db_user_password,
        'AUTH_KEY': salts[0],
        'SECURE_AUTH_KEY': salts[1],
        'LOGGED_IN_KEY': salts[2],
        'NONCE_KEY': salts[3],
        'AUTH_SALT': salts[4],
        'SECURE_AUTH_SALT': salts[5],
        'LOGGED_IN_SALT': salts[6],
        'NONCE_SALT': salts[7],
        'KEY_FILE_PATH': key_file_path,
        'REGION': args.region,
        'KEY_NAME': args.key_name,
        'STACK_NAME': args.stack_name
    }
    
    # Open the YAML file and write each key-value pair
    with open(output_file, 'w') as yaml_file:
        yaml.dump(yaml_data, yaml_file, default_flow_style=False)
    
    print(f"External variables for Ansible playbook have been written to {output_file}")

def generate_secure_password(length=16):
    # Special characters that are less likely to cause issues
    safe_special_chars = "!@#%^*()-_+=[]{}"

    # Combine character sets
    characters = string.ascii_letters + string.digits + safe_special_chars
    
    # Randomly select characters from the pool
    password = ''.join(random.choice(characters) for i in range(length))
    
    # Ensure the password contains at least one of each character type
    if (not any(c in string.ascii_lowercase for c in password) or
        not any(c in string.ascii_uppercase for c in password) or
        not any(c in string.digits for c in password) or
        not any(c in safe_special_chars for c in password)):
        return generate_secure_password(length)
    
    return password

def main():
    # If external_vars.yaml exists, then do nothing.
    if os.path.isfile('external_vars.yaml'):
        print('You have already run this script')
        print('Run \"reset.py\" to undo everything this script did')
        print('Then you can run this script again')
        print('CAUTION: running \"reset.py\" will erase everything!')
        exit()

    root_password = generate_secure_password(20)
    user_password = generate_secure_password(20)
    parser = argparse.ArgumentParser(description='Deploy resources and configure them using AWS and Ansible')

    # Required arguments
    parser.add_argument('--region', required=True, help='AWS region in which you wish to create resources')
    parser.add_argument('--email', required=True, help='Your email, which will be used with certbot to create an SSL cert')
    parser.add_argument('--domain', required=True, help='The domain of the site you would like to create')

    # Optional arguments
    parser.add_argument('--stack-name', default='WJCstack', help='Name of the CloudFormation stack')
    parser.add_argument('--template-file', default='wjc_cfn_stack.yaml', help='Path to the CloudFormation template file')
    parser.add_argument('--key-name', default='WJCkey', help='Name of the EC2 key pair (as it will appear in the AWS console, so no need to add .pem at the end)')
    # parser.add_argument('--playbook-file', default='wjc_playbook.yaml', help='Path to the Ansible playbook')
    parser.add_argument('--key-file-path', default='~/.ssh/', help='The directory where you would like to store the key')
    parser.add_argument('--db-host', default='localhost', help='The host address of the WordPress database')
    parser.add_argument('--db-name', default='wordpress', help='The name of the WordPress database')
    parser.add_argument('--db-root-name', default='root', help='The name of the root user of the WordPress database')
    parser.add_argument('--db-root-password', default=root_password, help='The password of the root user of the WordPress database. Random if unused.')
    parser.add_argument('--db-user-name', default='user', help='The name of the user of the WordPress database')
    parser.add_argument('--db-user-password', default=user_password, help='The password of the user of the WordPress database. Random if unused.')

    args = parser.parse_args()
    key_file_path = os.path.expanduser(f'{args.key_file_path}{args.key_name}.pem')

    create_key_pair(args.key_name, key_file_path, args.region)
    run_cloudformation(args.stack_name, args.template_file, args.key_name, args.region)
    public_ip = get_instance_public_ip(args.stack_name, args.region)
    write_selected_args_to_yaml(args, key_file_path, public_ip, 'external_vars.yaml')
    print("Now run \"ansible-playbook wjc_playbook.yaml\"")
    print("Then point your domain's DNS records to your EC2 Instance's IP address")
    print("Then run \"ansible-playbook wjc_ssl_playbook.yaml\"")
    print("After that, you should have a fresh WordPress site up and running!")

if __name__ == '__main__':
    main()
