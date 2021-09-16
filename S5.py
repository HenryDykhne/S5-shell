import boto3
import os
import configparser
import shlex

config = configparser.ConfigParser()
config.read('S5-S3conf')
ACCESS_KEY = config.get('edykhne', 'aws_access_key_id')
SECRET_KEY = config.get('edykhne', 'aws_secret_access_key')
REGION = config.get('edykhne', 'default_region_name')
#double check this is the right way to do this and if config file should have edykhne in it
#check if session token is needed
client = boto3.client(
    's3',
    aws_access_key_id = ACCESS_KEY,
    aws_secret_access_key = SECRET_KEY,
    region_name = REGION

    #aws_session_token=SESSION_TOKEN
)

if client is not None:
    print("Welcome to the AWS S3 Storage Shell (S5)")
    print("You are now connected to your S3 storage")
else:
    print("Welcome to the AWS S3 Storage Shell (S5)")
    print("You could not be connected to your S3 storage")
    print("Please review procedures for authenticating your account on AWS S3")

while True:
    print("S5>", end='')

    inputText = input()
    args = shlex.split(inputText)
    print(args)
    if args[0] == "quit" or args[0] == "exit":
        break
    else:
        os.system(inputText)