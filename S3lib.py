import copy
import boto3
from botocore.exceptions import ClientError
import configparser
import re
from tabulate import tabulate

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
        self.commands['cwf'] = self.cwf
        self.commands['list'] = self.list
        self.commands['ccopy'] = self.ccopy
        self.commands['delete_object'] = self.delete_object
        self.commands['delete_bucket'] = self.delete_bucket
        

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
            destinationSplit = (self.path +("/" if re.search(":[\s\S]+", self.path) else "") + args[2]).split(':') 
        
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
            sourceSplit = (self.path +("/" if re.search(":[\s\S]+", self.path) else "") + args[1]).split(':') 
        
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

        if ":" in args[1] or ".." in args[1]:
            response["text"] = "this shell does not support bucket names containing the substrings ':' or '..'"
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
        if len(destinationSplit) != 2:  #if relative path
            if '/' in args[1]:
                response["text"] = "this shell does not support the creation of nested folders in a single create_folder command"
                return response
            destinationSplit = (self.path +("/" if re.search(":[\s\S]+", self.path) else "") + args[1]).split(':') 
        
        if len(destinationSplit) != 2:
            response["text"] = "invalid destination format. you may not be in a bucket " + str(destinationSplit)
            return response

        if ":" in destinationSplit[1] or ".." in destinationSplit[1]:
            response["text"] = "this shell does not support folder names containing the substrings ':', or '..'"
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
            except Exception as e:
                response["text"] = "invalid bucket: " + str(e)
        else:
            try:
                self.client.head_object(Bucket = bucket, Key = objPath)
                response["code"] = 0
                response["text"] = ""
            except Exception as e:
                response["text"] = "object/directory does not exist: " + str(e)
            
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
                destinationSplit = (self.path +("/" if re.search(":[\s\S]+", self.path) else "") + args[1]).split(':') 

            if len(destinationSplit) != 2:
                response["text"] = "invalid destination format"
                return response
            
            tempBucket, tempFolderPath = self.path_dots_canceler(destinationSplit)
        
        if tempBucket == "":
            self.path = ""
            response["code"] = 0
            response["text"] = ""
            return response
        
        val = self.validate_path(tempBucket, tempFolderPath + ("/" if tempFolderPath != "" else ""))
        if val['code'] == 0:
            self.path = tempBucket + (':' if tempBucket != '' else '') + tempFolderPath
        return val

    def cwf(self, args):
        response = copy.deepcopy(self.initial_response)
        if self.path == "":
            response["text"] = "/"
        else:
            response["text"] = self.path

        response["code"] = 0
        return response

    def list(self, args):
        response = copy.deepcopy(self.initial_response)
        if len(args) >= 2 and args[1] == "-l":
            lFlag = True
        else:
            lFlag = False

        if self.path == "":
            try:
                bucketList = []
                bucketListLite = []
                result = self.client.list_buckets()["Buckets"]
                if result == None:
                    response["text"] = "no buckets"
                else:
                    for bucket in result:
                        bucketListLite.append([bucket["Name"]])
                        bucketList.append([bucket["Name"], bucket["CreationDate"]])
                    if lFlag:
                        response["text"] = tabulate(bucketList, headers = ["BucketName", "Creation Date"], tablefmt = "pretty", stralign = "left")

                    else:
                        response["text"] = tabulate(bucketListLite, headers = ["BucketName"], tablefmt = "pretty", stralign = "left")

                response["code"] = 0
            except Exception as e:
                response["text"] = "could not retrive buckets: " + str(e)
                response["code"] = 1
            return response

        splitPath = self.path.split(":")
        try:
            objectList = []
            objectListLite = []
            prefix = splitPath[1] + ("/" if splitPath[1] != "" else "")
            result = self.client.list_objects(Bucket = splitPath[0], Prefix = prefix)
            if result.get('Contents') == None:
                response["text"] = "empty"
                response["code"] = 0
                return response

            for object in result.get('Contents'):
                prefixPurged = object['Key'][len(prefix):]
                if ('/' not in prefixPurged or (prefixPurged.count('/') == 1 and prefixPurged[-1] == '/')) and prefixPurged != "":
                    objectList.append([prefixPurged, str(object['Size'] / 1024) + " KB", object['LastModified']])
                    objectListLite.append([prefixPurged])

            if lFlag:
                returnText = tabulate(objectList, headers = ["Name", "Size", "Last Modified"], tablefmt = "pretty", stralign = "left")
            else:
                returnText = tabulate(objectListLite, headers = ["Name"], tablefmt = "pretty", stralign = "left")
            
            response["text"] = returnText
            response["code"] = 0
        except Exception as e:
            response["text"] = "could not retrive list of items: " + str(e)

        return response

    def ccopy(self, args):
        response = copy.deepcopy(self.initial_response)
        if len(args) != 3:
            response["text"] = "invalid number of arguments"
            return response

        destinationSplit = args[2].split(':')
        if len(destinationSplit) != 2:
            destinationSplit = (self.path +("/" if re.search(":[\s\S]+", self.path) else "") + args[2]).split(':') 
        
        if len(destinationSplit) != 2:
            response["text"] = "invalid destination format"
            return response

        destinationBucketName = destinationSplit[0]
        destinationObjName = destinationSplit[1]

        sourceSplit = args[1].split(':')
        if len(sourceSplit) != 2:
            sourceSplit = (self.path +("/" if re.search(":[\s\S]+", self.path) else "") + args[1]).split(':') 
        
        if len(sourceSplit) != 2:
            response["text"] = "invalid source format"
            return response

        sourceBucketName = sourceSplit[0]
        sourceObjName = sourceSplit[1]

        if destinationObjName == "../" or destinationObjName == "./" or destinationObjName == "/" or sourceObjName == "../" or sourceObjName == "./" or sourceObjName == "/":
            response["text"] = "this shell does not support files named '.' or '..' or ''"
            return response

        copy_source = {
            'Bucket': sourceBucketName,
            'Key': sourceObjName
        }

        try:
            self.client.copy(copy_source, destinationBucketName, destinationObjName)
            response["text"] = ""
            response["clode"] = 0
        except Exception as e:
            response["text"] = "could not retrive buckets: " + str(e)
        
        return response

    def delete_object(self, args):
        response = copy.deepcopy(self.initial_response)
        ###implement this
        ##################33
        ####################33
        #########################
        #########################
        ######################
        return None

    def delete_bucket(self, args):
        response = copy.deepcopy(self.initial_response)
        if(len(args) != 2):
            response["text"] = "invalid number of arguments"
            return response

        #if in bucket
        if self.path != "" and self.path.split(":")[0] == args[1]:
            response["text"] = "cannot delete bucket shell is occupying"
            return response

        #if bucket exists
        try:
            self.client.head_bucket(Bucket=args[1])
        except Exception as e:
            response["text"] = "bucket does not exist: " + str(e)
            return response
        
        #if bucket is empty
        try:
            result = self.client.list_objects(Bucket = args[1])
            if result.get('Contents') != None:
                response["text"] = "deletion cannot be completed. bucket is not empty"
                return response
        except Exception as e:
            response["text"] = "unable to check if bucket is empty before deletion. try again: " + str(e)
            return response
        
        try:
            response = self.client.delete_bucket(Bucket=args[1])
        except Exception as e:
            response["text"] = "failed to delete bucket: " + str(e)
            return response

        response["text"] = ""
        response["code"] = 0
        return response

