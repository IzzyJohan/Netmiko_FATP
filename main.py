import time
from netmiko import ConnectHandler, SSHDetect, redispatch
import json
import logging

def config_data():
    with open('config.json', 'r') as read_file:
        config_data = json.load(read_file)
        global jumpserver, node
        jumpserver = config_data['jumpserver']
        node = config_data['node']

def jumpserver_connection():
    guesser = SSHDetect(**jumpserver)
    best_match = guesser.autodetect() # Automatic device type detector
    # print(guesser.potential_matches) # Netmiko dictionary of device match 
    jumpserver['device_type'] = best_match

    global net_connect
    net_connect = ConnectHandler(**jumpserver)
    print(f'Jump Server Prompt: {net_connect.find_prompt()}\n')

    log_file()
    node_connection(get_ip_list())

    net_connect.write_channel('exit\n')
    log_file.close

def log_file():
    file_name = input('Masukan nama file: ')
    print()
    global log_file
    log_file = open(f'{file_name}.log', 'w')

def debugging_log():
    logging.basicConfig(filename='debug.log', level=logging.DEBUG)

def separator():
        separator = '=-' * 42
        return separator

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

    redispatch(net_connect, device_type=node['device_type'])
    send_show_command(get_commands_list())

    net_connect.write_channel('exit\n')
    time.sleep(2)


def send_show_command(commands):
    for command in commands:
        output = f'{net_connect.send_command(command)}'
        node_prompt = f'{net_connect.find_prompt()}{command}'
        time.sleep(1)
        print(f'{node_prompt}\n{output}\n')
        log_file.write(f'{node_prompt}\n{output}' + '\n\n')

def node_connection(ip_list):
    for ip in ip_list:

        prompt_view = f"{net_connect.find_prompt()}ssh {node['ssh_user']}@{ip}"
        print(prompt_view)
        log_file.write(prompt_view + '\n')

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
            no_respond = f'{ip} is not responding'
            print(f'{no_respond}\n')
            log_file.write(no_respond + '\n\n')
            net_connect.write_channel('\3')
            time.sleep(2)

        else:
            print(f'{node_respond}\n')
            log_file.write(node_respond + '\n\n')
            net_connect.write_channel('\3')
            time.sleep(2)

        print(separator())
        log_file.write(separator() + '\n')

def main():
    config_data()
    jumpserver_connection()


if __name__ == '__main__':
    main()

