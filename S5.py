import os
import shlex
import readline
from S3lib import S3
import copy

path = os.getcwd()
initial_response = {"code": 1, "text":"unspecified error"}

def os_command(inputText):
    response = copy.deepcopy(initial_response)
    try:
        os.system(inputText)
        response["code"] = 0
        response["text"] = ""
    except Exception as e:
        response["text"] = str(e)
    return response

def cd(args):
    response = copy.deepcopy(initial_response)
    if len(args) == 1 or args[1] == "" or args[1] == " ":
        args[1] = ""
        
    try:
        os.chdir(args[1])
        response["code"] = 0
        response["text"] = ""
    except FileNotFoundError as e:
        response["text"] = str(e)

    path = os.getcwd()
    return response

#commands
shell_commands = {}
shell_commands['cd'] = cd
s3 = S3()



if s3.client is not None: #FIXME: this does not work. fix it
    #DONT FORGET!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    print("Welcome to the AWS S3 Storage Shell (S5)")
    print("You are now connected to your S3 storage")
else:
    print("Welcome to the AWS S3 Storage Shell (S5)")
    print("You could not be connected to your S3 storage")
    print("Please review procedures for authenticating your account on AWS S3")

while True:
    inputText = input(path + ":S5> ")
    args = shlex.split(inputText)

    if len(args) == 0:
        continue
    elif args[0] == "exit" or args[0] == "quit":
        exit()
    elif args[0] in s3.commands.keys():
        response = s3.commands[args[0]](args)
    elif args[0] in shell_commands.keys():
        response = shell_commands[args[0]](args)
    else:
        response = os_command(inputText)

    if response["code"] != 0:
        print(response["text"])

#if at root, and no : then consider it to be a bucket name
#if : then consider it to be a full path name