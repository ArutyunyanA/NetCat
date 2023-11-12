import argparse
import socket
import shlex
import subprocess
import sys
import textwrap
import threading

class NetCat:
    # We initialize the NetCat object with the arguments from the command line and the buffer
    def __init__(self, args, buffer=None):
        self.args = args
        self.buffer = buffer
        # create the socket object
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        if self.args.listen:
        # call the listen method
            self.listen()
        else:
        # call the send method 
            self.send()

    def send(self):
        # We connect to the target and port
        self.socket.connect((self.args.target, self.args.port))
        # if we have a buffer, we send that to the target first
        if self.buffer:
            self.socket.send(self.buffer)
        # Then we set up a try/catch block
        try:
            # Next, we start a loop to receive data from the target
            while True:
                recv_len = 1
                response = ''
                while recv_len:
                    data = self.socket.recv(4096)
                    recv_len = len(data)
                    response += data.decode()
                    if recv_len < 4096:
                        # If there is no more data, we break out of the loop
                        break
                    # Otherwise, we print the response data and pause to get 
                    # interactive input, send that input, and continue the loop.
                    if response:
                        print(response)
                        duffer = input('> ')
                        duffer += '\n'
                        self.socket.send(buffer.encode())
        # The loop will continue until the KeyboardInterrupt 
        # occurs (CTRL-C), which will close the socket.
        except KeyboardInterrupt:
            print('User terminated.')
            self.socket.close()
            sys.exit()

    def listen(self):
        # The listen method binds to the target and port 
        # and starts listening in a loop 
        self.socket.bind((self.args.target, self.args.port))
        self.socket.listen(5)
        # passing the connected socket to the handle method
        while True:
            client_socket, _ = self.socket.accept()
            # Now let’s implement the logic to perform file uploads, 
            # execute com- mands, and create an interactive shell.
            client_thread = threading.Thread(
                target=self.handle, args=(client_socket,)
            )
            client_thread.start()
    
    """
    The handle method executes the task corresponding to the command line 
    argument it receives: execute a command, upload a file, or start a shell.
    """

    def handle(self, client_socket):
        # If a command should be executed, the handle method passes 
        # that command to the execute function and sends the output back on the socket.
        if self.args.execute:
            output = execute(self.args.execute)
            client_socket.send(output.encode())
        # If a file should be uploaded 2, we set up a loop to listen for content on 
        # the listening socket and receive data until there’s no more data coming in.
        elif self.args.upload:
            file_buffer = b''
            while True:
                data = client_socket.recv(4096)
                if data:
                    file_buffer += data
                else:
                    break
            # Then we write that accumulated content to the specified file.
            with open(self.args.upload, 'wb') as file:
                file.wrire(file_buffer)
                message = f'Saved file {self.args.upload}'
                client_socket.send(message.encode())
        # Finally, if a shell is to be created 3, we set up a loop, 
        # send a prompt to the sender, and wait for a command string to come back.
        elif self.args.command:
            cmd_buffer = b''
            while True:
                try:
                    client_socket.send(b'BHP: #> ')
                    while '\n' not in cmd_buffer.decode():
                        cmd_buffer += client_socket.recv(64)
                    response = execute(cmd_buffer.decode())
                    if response:
                        client_socket.send(response.encode())
                    cmd_buffer = b''
                except Exception as e:
                    print(f'Server killed {e}')
                    self.socket.close()
                    sys.exit()
        # We then execute the command by using the execute 
        # function and return the output of the command to the sender.

"""
This function receives a command, runs it, and returns the output as
a string.
"""
def execute(cmd):
    cmd = cmd.strip()
    if not cmd:
        return
    # we’re using its check_output method, which runs a command on the local 
    # operating system and then returns the output from that command.
    output = subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT)
    return output.decode()

if __name__ == '__main__':
    # We use the argparse module from the standard 
    # library to create a command line interface
    parser = argparse.ArgumentParser(
        description='BHP Net Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        # We provide example usage that the program will display when the user 
        # invokes it with --help and add six arguments that specify how we 
        # want the program to behave
        epilog=textwrap.dedent('''Example:
                               netcat.py -t 192.168.1.108 -p 5555 -l -c # command shell
                               netcat.py -t 192.168.1.108 -p 5555 -l -u=mytest.txt # upload the file
                               netcat.py -t 192.168.1.108 -p 5555 -l -e=\"cat /etc/passwd\" # execute command
                               echo 'ABC' | ./netcat.py -t 192.168.1.108 -p 135 # echo text to server port 135
                               netcat.py -t 192.168.1.108 -p 5555 # connect to server
'''))
    parser.add_argument('-c', '--command', action='store_true', help='command shell')
    parser.add_argument('-e', '--execute', help='execute specified command')
    parser.add_argument('-l', '--listen', action='store_true', help='listen')
    parser.add_argument('-p', '--port', type=int, default=5555, help='specified port')
    parser.add_argument('-t', '--target', default='192.168.1.203', help='specified IP')
    parser.add_argument('-u', '--upload', help='upload file')
    args = parser.parse_args()
    # If we’re setting it up as a listener 4, we invoke the NetCat object 
    # with an empty buffer string. Otherwise, we send the buffer content 
    # from stdin. Finally, we call the run method to start it up.
    if args.listen:
        buffer = ''
    else:
        buffer = sys.stdin.read()

    nc = NetCat(args, buffer.encode())
    nc.run()

