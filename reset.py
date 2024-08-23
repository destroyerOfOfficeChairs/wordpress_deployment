import boto3
import os
import subprocess
import yaml

def main():
    my_dict = {}
    if not os.path.isfile('external_vars.yaml'):
        print("You have nothing to delete")
        print("Run \"deploy.py\" first")
        exit()
    with open('external_vars.yaml') as f:
        my_dict = yaml.load(f, Loader=yaml.FullLoader)
    ec2 = boto3.client('ec2', my_dict['REGION'])
    ec2.delete_key_pair(KeyName=my_dict['KEY_NAME'])
    cf = boto3.client('cloudformation', my_dict['REGION'])
    cf.delete_stack(StackName=my_dict['STACK_NAME'])
    os.remove(my_dict['KEY_FILE_PATH'])
    os.remove('./external_vars.yaml')

if __name__ == '__main__':
    main()
