import os
import shlex
import readline
from S3lib import S3

path = os.getcwd()

def cd(args):
    if len(args) == 1 or args[1] == "" or args[1] == " ":
        args[1] = ""
        
    try:
        os.chdir(args[1])
    except:
        return "invalid path"

    path = os.getcwd()
    return ''

#commands
shell_commands = {}
shell_commands['cd'] = cd
s3 = S3()



if s3.client is not None: #this does not work. fix it
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
        os.system(inputText)

    if response["code"] != 0:
        print(response["text"])