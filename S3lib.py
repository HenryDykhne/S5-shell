import boto3
from botocore.exceptions import ClientError
import configparser
import re
import logging

class S3:
    def __init__(self):
        self.client = None
        self.config()
        self.commands = {}
        self.commands['lc_copy'] = self.lc_copy
        self.commands['cl_copy'] = self.cl_copy
        self.s3path = ""

    def config(self):
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
        self.client = client

    def lc_copy(self, args):
        if len(args) != 3:
            return "invalid number of arguments"

        destinationSplit = args[2].split(':')
        if len(destinationSplit) != 2:
            destinationSplit = (self.path + args[2]).split(':') 
            #make sure to manually add : after buckets in path during ch_folder
        
        if len(destinationSplit) != 2:
            return "invalid destination format"

        bucketName = destinationSplit[0]
        objName = destinationSplit[1]
        try:
            self.client.upload_file(args[1], bucketName, objName)
            response = ""
        except (ClientError, FileNotFoundError) as e:
            logging.error(e)
            response = e
        return response

    def cl_copy(self, args):
        if len(args) != 3:
            return "invalid number of arguments"

        sourceSplit = args[1].split(':')
        if len(sourceSplit) != 2:
            sourceSplit = (self.path + args[1]).split(':') 
            #make sure to manually add : after buckets in path during ch_folder
        
        if len(sourceSplit) != 2:
            return "invalid source format"

        bucketName = sourceSplit[0]
        objName = sourceSplit[1]
        try:
            self.client.download_file(bucketName, objName, args[2])
            response = ""
        except (ClientError, FileNotFoundError) as e:
            logging.error(e)
            response = e
        return response