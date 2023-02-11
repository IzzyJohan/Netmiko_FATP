import time
from netmiko import ConnectHandler, SSHDetect, redispatch
import json
# import logging

with open('config.json', 'r') as read_file:
    config_data = json.load(read_file)

jumpserver = config_data['jumpserver']
node = config_data['node']

guesser = SSHDetect(**jumpserver)
best_match = guesser.autodetect()

# Uncomment to show jump server detected device type
# print(f'Device type: {best_match}') 
# Netmiko dictionary of the device type matching result
# print(guesser.potential_matches) 

jumpserver['device_type'] = best_match
net_connect = ConnectHandler(**jumpserver)
print(f'Jump Server Prompt: {net_connect.find_prompt()}\n')

file_name = input('Masukan nama file: ')
log_file = open(f'{file_name}.log', 'w')

# Netmiko debugging
# logging.basicConfig(filename = 'debug.log', level = logging.DEBUG)
# logger = logging.getLogger('netmiko')

def get_ip_list():
    with open('ip_list.txt', 'r') as read_file:
        ip_list = read_file.read().splitlines()
    stripped_ip_list = [ip.strip() for ip in ip_list]
    while('' in stripped_ip_list):
        stripped_ip_list.remove('')
    return(stripped_ip_list)

def get_commands_list():
    with open('commands.txt', 'r') as read_file:
        command_list = read_file.read().splitlines()
    stripped_command_list = [command.strip() for command in command_list]
    while('' in stripped_command_list):
        stripped_command_list.remove('')
    return(stripped_command_list)

def active_node_handler():
    net_connect.write_channel(f"{node['password']}\n")
    time.sleep(2)
    net_connect.write_channel(f"{node['another_password']}\n")
    time.sleep(2)

    redispatch(net_connect, device_type = node['device_type'])
    send_show_command(get_commands_list())

    net_connect.write_channel('exit\n')
    time.sleep(2)


def send_show_command(commands):
    for command in commands:
        output = f'{net_connect.send_command(command)}\n\n'
        node_prompt = f'{net_connect.find_prompt()}{command}'
        time.sleep(1)
        print(f'{node_prompt}\n{output}')
        log_file.write(f'{node_prompt}\n{output}')

def node_connection(ip_list):
    for ip in ip_list:

        write_ssh = f"{net_connect.find_prompt()}ssh {node['ssh_user']}@{ip}\n"
        print(write_ssh)
        log_file.write(write_ssh)

        ssh_command = f"ssh {node['ssh_user']}@{ip}\n"
        net_connect.write_channel(ssh_command)
        time.sleep(3)

        node_respond = net_connect.read_channel()

        if 'yes/no' in node_respond.lower():
            net_connect.write_channel('yes\n')
            time.sleep(2)
            active_node_handler()

        elif 'password' in node_respond.lower():
            active_node_handler()
        
        elif node_respond == ssh_command:
            no_respond = f'{ip} is not responding\n\n'
            print(no_respond)
            log_file.write(no_respond)
            net_connect.write_channel('\3')
            time.sleep(2)

        else:
            print(node_respond + '\n\n')
            log_file.write(node_respond + '\n\n')
            net_connect.write_channel('\3')
            time.sleep(2)
        
node_connection(get_ip_list())

# Ending jump server SSH session
net_connect.write_channel('exit\n')
log_file.close
