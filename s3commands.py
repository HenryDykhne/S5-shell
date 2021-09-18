import boto3
from botocore.exceptions import ClientError
import configparser
import re
import logging

def config():
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
    return client

def lc_copy(args, client):
    if len(args) != 3:
        return "invalid number of arguments"
    destination = args[2].split(':')
    if len(destination) != 2:
        return "destination improperly formatted"
    bucketName = destination[0]
    objName = destination[1]
    try:
        client.upload_file(args[1], bucketName, objName)
        response = ""
    except (ClientError, FileNotFoundError) as e:
        logging.error(e)
        response = e
    return response

commands = {}
commands['lc_copy'] = lc_copy