import sys, os
sys.path.append('/usr/lib/python3.5')

#check for netmiko, install if not present
if 'netmiko' in sys.modules:
    print "Dependencies already present"
else:
    confirmation = raw_input("Netmiko library required but not present. OK to install? Y/N: ")
    valid_input = False

    while not valid_input:
        if confirmation == "y":
            valid_input = True
            os.system("gnome-terminal -e 'sudo apt-get install netmiko'")
            raw_input("A terminal will open to request sudo permission to install netmiko library. Press enter to continue after dependencies installed.")
        elif confirmation == "n":
            valid_input = True
            raw_input("Press enter to quit....")
            sys.exit()
        else:
            confirmation = raw_input("Please provide valid input. OK to install netmiko? Y/N: ")[0]

import netmiko

devices = []
interface_list = []
disable_unused = False
port_security = "switch port-security mac sticky"

my_device = {
    'device_type': 'cisco_ios',
        'ip': '',
        'username': '',
        'password': '',
        'secret': '',
}

#gets current interface configurations, populates a list of dictionaries
def grab_ints():
    int_name = ""
    is_active = False
    is_trunk = False

    #start connection, determine number of interfaces
    net_connect = netmiko.ConnectHandler(**my_device)
    net_connect.enable()
    output = net_connect.send_command("sho ip int br")
    lines = output.split('\n')

    #disinclude vlan interfaces and column headers
    for line in lines:
        for char in line:
            if char != " " and char != "I" and char != "V":
                int_name += char
            else:
                break

        #determine layer 1 status
        if line[50] == "u":
            is_active = True
        elif line[50] == "d" or line[50] == "a":
            is_active = False

        #determine if interface is trunk
        if int_name != "":
            trunk_line = net_connect.send_command("show interface " + int_name + " trunk")
            trunk_line = trunk_line.split('\n')
            trunk_line = trunk_line[2]
            if trunk_line[12:14] == "on":
                is_trunk = True

            #generate dict and add to list
            new_interface = {
                'int_name': int_name,
                'is_active': is_active,
                'is_trunk': is_trunk,
            }

            interface_list.append(new_interface)
            int_name = ""
        
    #call configuration
    config_int()

#actually configure interfaces
def config_int():
    net_connect = netmiko.ConnectHandler(**my_device)
    net_connect.enable()
    net_connect.config_mode()

    for iface in interface_list:
        int_name = iface["int_name"]
        command_set = ['interface ' + int_name]
        if iface['is_trunk']:
            command_set.append("no cdp enable")
        else:
            command_set.append('switch port-sec mac sticky')
        
        if not iface['is_active'] and disable_unused:
            command_set.append('shutdown')
        output = net_connect.send_config_set(command_set)
        
    #net_connect.exit_config_mode()
    output = net_connect.send_command("show run")
    print(output)
    net_connect.disconnect()

        


def main():
    ip = raw_input("IP of device? ")
    username = raw_input("Username? ")
    passwd = raw_input("User Pass? ")
    secret = raw_input("Enable Secret? ")

    my_device["ip"] = ip
    my_device["username"] = username
    my_device["password"] = passwd
    my_device["secret"] = secret

    disable = raw_input("Disable unused interfaces? y/n: ")[0]
    valid_input = False

    while not valid_input:
        if disable == "y" or disable == "Y":
            disable_unused = True
            valid_input = True
        elif disable == "n" or disable == "N":
            disable_unused = False
            valid_input = True
        else:
            disable = raw_input("Please provide valid input. Disable unused interfaces? y/n: ")[0]


    print("\nConfiguring, please stand by...")
    grab_ints()

if __name__ =="__main__":
    main()
