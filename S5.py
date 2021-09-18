import os
import shlex
import s3commands
import readline

#commands
shell_specific_commands = {}
client = s3commands.config()


if client is not None:
    print("Welcome to the AWS S3 Storage Shell (S5)")
    print("You are now connected to your S3 storage")
else:
    print("Welcome to the AWS S3 Storage Shell (S5)")
    print("You could not be connected to your S3 storage")
    print("Please review procedures for authenticating your account on AWS S3")

while True:
    print("S5> ", end='')
    inputText = input()
    args = shlex.split(inputText)

    print(args)

    if len(args) == 0:
        continue
    elif args[0] == "exit" or args[0] == "quit":
        exit()
    elif args[0] in s3commands.commands.keys():
        print(s3commands.commands[args[0]](args, client))
    elif args[0] in shell_specific_commands.keys():
        shell_specific_commands[args[0]](args)
    else:
        os.system(inputText)