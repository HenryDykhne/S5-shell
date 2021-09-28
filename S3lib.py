import copy
import boto3
from botocore.exceptions import ClientError
import configparser
import re
import logging

class S3:
    initial_response = {"code": 1, "text":"unspecified error"}
    path = ""
    def __init__(self):
        self.client = None
        self.config()
        self.commands = {}
        self.commands['lc_copy'] = self.lc_copy
        self.commands['cl_copy'] = self.cl_copy
        self.commands['create_bucket'] = self.create_bucket
        self.commands['create_folder'] = self.create_folder
        self.commands['ch_folder'] = self.ch_folder
        self.s3path = ""

    def config(self):
        config = configparser.ConfigParser()
        config.read('S5-S3conf')
        ACCESS_KEY = config.get('edykhne', 'aws_access_key_id')
        SECRET_KEY = config.get('edykhne', 'aws_secret_access_key')
        REGION = config.get('edykhne', 'default_region_name')
        client = boto3.client(
            's3',
            aws_access_key_id = ACCESS_KEY,
            aws_secret_access_key = SECRET_KEY,
            region_name = REGION
        )
        self.client = client

    def lc_copy(self, args):
        response = copy.deepcopy(self.initial_response)

        if len(args) != 3:
            response["text"] = "invalid number of arguments"
            return response

        destinationSplit = args[2].split(':')
        if len(destinationSplit) != 2:
            destinationSplit = (self.path + args[2]).split(':') 
            #make sure to manually add : after buckets in path during ch_folder
        
        if len(destinationSplit) != 2:
            response["text"] = "invalid destination format"
            return response

        bucketName = destinationSplit[0]
        objName = destinationSplit[1]

        if objName == "../" or objName == "./" or objName == "/":
            response["text"] = "this shell does not support files named '.' or '..' or ''"
            return response

        try:
            self.client.upload_file(args[1], bucketName, objName)
            response["code"] = 0
            response["text"] = ""
        except (ClientError, FileNotFoundError) as e:
            response["text"] = str(e)

        return response

    def cl_copy(self, args):
        response = copy.deepcopy(self.initial_response)

        if len(args) != 3:
            response["text"] = "invalid number of arguments"
            return response

        sourceSplit = args[1].split(':')
        if len(sourceSplit) != 2:
            sourceSplit = (self.path + args[1]).split(':') 
            #make sure to manually add : after buckets in path during ch_folder
        
        if len(sourceSplit) != 2:
            response["text"] = "invalid source format"
            return response

        bucketName = sourceSplit[0]
        objName = sourceSplit[1]

        if objName == "../" or objName == "./" or objName == "/":
            response["text"] = "this shell does not support files named '.' or '..' or ''"
            return response
        
        try:
            self.client.download_file(bucketName, objName, args[2])
            response["code"] = 0
            response["text"] = ""
        except (ClientError, FileNotFoundError) as e:
            response["text"] = str(e)

        return response

    def create_bucket(self, args):
        response = copy.deepcopy(self.initial_response)

        if len(args) != 2:
            response["text"] = "wrong number of arguments"
            return response
        
        if not (3 < len(args[1]) <= 63):
            response["text"] = "invalid bucket name\nbucket names must be between 3 and 63 characters long"
            return response

        if not re.match("^[a-z0-9\.-]*$", args[1]):
            response["text"] = "invalid bucket name\nbucket names can consist only of lowercase letters, numbers, dots (.), and hyphens (-)"
            return response

        if not args[1][0].isalnum() or not args[1][-1].isalnum():
            response["text"] = "invalid bucket name\nbbucket names must begin and end with a letter or number"
            return response

        if re.match("^([0-9]+\.)+[0-9]+$", args[1]):
            response["text"] = "invalid bucket name\nbucket names must not be formatted as an IP address (for example, 192.168.5.4)"
            return response

        if args[1].startswith("xn--"):
            response["text"] = "invalid bucket name\nbucket names must not start with the prefix xn--"
            return response

        if args[1].endswith("-s3alias"):
            response["text"] = "invalid bucket name\nbucket names must not end with the suffix"
            return response

        if args[1] == "../" or args[1] == "./" or args[1] == "/":
            response["text"] = "this shell does not support buckets named '.' or '..' or ''"
            return response

        try:
            location = {'LocationConstraint': self.client.meta.region_name}
            self.client.create_bucket(Bucket=args[1], CreateBucketConfiguration=location)
            response["code"] = 0
            response["text"] = ""
        except ClientError as e:
            response["text"] = str(e)

        return response
    
    def create_folder(self, args):
        response = copy.deepcopy(self.initial_response)

        if len(args) != 2:
            response["text"] = "invalid number of arguments"
            return response

        destinationSplit = args[1].split(':')
        if len(destinationSplit) != 2:
            destinationSplit = (self.path + args[1]).split(':') 
            #make sure to manually add : after buckets in path during ch_folder
        
        if len(destinationSplit) != 2:
            response["text"] = "invalid destination format"
            return response

        bucketName = destinationSplit[0]
        folderName = destinationSplit[1] + "/"

        if folderName == "../" or folderName == "./" or folderName == "/":
            response["text"] = "this shell does not support folders named '.' or '..' or ''"
            return response

        try:
            self.client.put_object(Bucket = bucketName, Key = folderName)
            response["code"] = 0
            response["text"] = ""
        except (ClientError, FileNotFoundError) as e:
            response["text"] = str(e)
        
        return response
    
    def path_dots_canceler(self, destinationSplit):
        bucket = destinationSplit[0]
        folderPath = destinationSplit[1]

        splitPath = folderPath.split('/')

        i = 0
        while i < len(splitPath):
            if splitPath[i] == '..':
                if i != 0:
                    splitPath.pop(i)
                    splitPath.pop(i - 1)
                    i = i - 1
                else:
                    bucket = ''
                    folderPath = ''
                    return bucket, folderPath
            i = i + 1
        
        folderPath = '/'.join(splitPath)
        return bucket, folderPath

    def validate_path(self, bucket, objPath):
        response = copy.deepcopy(self.initial_response)
        if bucket == "":
            if objPath != "":
                response["text"] = "no bucket"
            else:
                response["code"] = 0
                response["text"] = ""
            return response

        if objPath == "":
            try:
                self.client.head_bucket(Bucket = bucket)
                response["code"] = 0
                response["text"] = ""
                return response
            except Exception as e:
                response["text"] = "invalid bucket: " + str(e)
                return response
        else:
            try:
                self.client.head_object(Bucket = bucket, Key = objPath)
                response["code"] = 0
                response["text"] = ""
                return response
            except Exception as e:
                response["text"] = "object does not exist: " + str(e)
                return response
            

    def ch_folder(self, args):
        response = copy.deepcopy(self.initial_response)

        if len(args) != 2:
            response["text"] = "invalid number of arguments"
            return response

        if args[1] == "/":
            self.path = ""
            response["code"] = 0
            response["text"] = ""
            return response

        if self.path == "" and ":" not in args[1]:
            #we are at root
            tempBucket = args[1]
            tempFolderPath = ""
        else:
            destinationSplit = args[1].split(':')
            if len(destinationSplit) != 2:
                destinationSplit = (self.path + args[1]).split(':') 
                #make sure to manually add : after buckets in path during ch_folder
            
            if len(destinationSplit) != 2:
                response["text"] = "invalid destination format"
                return response
            
            tempBucket, tempFolderPath = self.path_dots_canceler(destinationSplit)
        
        if tempBucket == "":
            self.path = ""
            response["code"] = 0
            response["text"] = ""
            return response

        val = self.validate_path(tempBucket, tempFolderPath + ('/' if tempFolderPath != '' else ''))
        if val['code'] == 0:
            self.path = tempBucket + (':' if tempBucket != '' else '') + tempFolderPath + ('/' if tempFolderPath != '' else '')
        return val
        #if at root and no :. then consider to be bucket name
        # if not at root and no : consider to be relative path
        # if : then full path name
        # need check for '/'
        #check if real bucket + folder

