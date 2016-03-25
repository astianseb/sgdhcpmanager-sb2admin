from netmiko import ConnectHandler
from ciscoconfparse import CiscoConfParse
import sqlite3
import os, datetime


homeRTR = {
    'device_type':'cisco_ios',
    'ip':'192.168.0.1',
    'username':'admin',
    'password':'xxxxxx',
    'port':'22',
}


def create_config(poolname, ip_address, mac_address):
    line1 = 'ip dhcp pool' + ' ' + poolname
    line2 = 'host' + ' ' + ip_address + ' ' + '255.255.255.0'
    line3 = 'client-identifier' + ' ' + mac_address
    line4 = 'default-router 192.168.0.1'
    line5 = 'dns-server 192.34.178.1'
    return [line1, line2, line3, line4, line5]

class Router:
    def __init__(self):
        self.net_connect = ConnectHandler(**homeRTR)

    def show_dhcp_binding(self, mac_end):
        command = 'show ip dhcp binding | incl ' + mac_end
        output = self.net_connect.send_command(command)
#        self.net_connect.disconnect()
        return output.split('\n')

    def ping_ipaddr(self, ipaddr):
        command = 'ping ' + ipaddr
        output = self.net_connect.send_command(command)
#        self.net_connect.disconnect()
        return output.split('\n')

    def show_arp(self, mac_end):
        command = 'show arp | incl ' + mac_end
        output = self.net_connect.send_command(command)
#        self.net_connect.disconnect()
        return output.split('\n')

    def add_dhcp_client(self, config_list):
        output = self.net_connect.send_config_set(config_list)
        return output.split('\n')

    def delete_dhcp_client(self, config_list):
        output = self.net_connect.send_config_set(config_list)
        return output.split('\n')

class ConfigFile:
    def __init__(self):
        self.config_file = "config.txt"

    def get_config(self):
        net_connect = ConnectHandler(**homeRTR)
        output = net_connect.send_command('sh run')
        text_file = open(self.config_file, "w")
        text_file.write(output)
        text_file.close()

    def get_config_date(self):
        t = os.path.getmtime(self.config_file)
        return datetime.datetime.fromtimestamp(t)

class DhcpConfig:
    def __init__(self, config_file):
        self.config_file = config_file
        self.parse = CiscoConfParse(self.config_file)

    def get_dhcppool_config(self, pool_name):
        find_result = self.parse.find_children(pool_name)
        return find_result

    def get_dhcppoolname_list(self):
        dhcppoolname_list = []
        find_result = self.parse.find_parents_w_child('^ip dhcp pool', 'host')
        for parent in find_result:
            dhcppoolname_list.append(parent.split()[3])
        return dhcppoolname_list

    def get_ipaddr(self, pool_name):
        find_result = self.parse.find_children(pool_name)
        return find_result[1].split()[1]

    def get_ipaddrmask(self, pool_name):
        find_result = self.parse.find_children(pool_name)
        return find_result[1].split()[2]

    def get_macaddr(self, pool_name):
        find_result = self.parse.find_children(pool_name)
        return find_result[2].split()[1]

    def get_defaultrouter(self, pool_name):
        find_result = self.parse.find_children(pool_name)
        return find_result[3].split()[1]

    def get_dns(self, pool_name):
        find_result = self.parse.find_children(pool_name)
        return [find_result[4].split()[1], find_result[4].split()[2]]


class ConfigDB():
    def __init__(self):
        self.conn = sqlite3.connect('configdb.db')

    def create_db(self):
        c = self.conn.cursor()
        c.execute('''DROP TABLE dhcp_router_config''')
        c.execute('''CREATE TABLE dhcp_router_config
            (pool_name text, ipaddr text, ipaddr_mask text, mac text)''')
        c.execute('''DROP TABLE dhcp_config''')
        c.execute('''CREATE TABLE dhcp_config
            (ipaddr text, ipmask text, mac text, defaultgw text, dns text)''')
        self.conn.commit()
#        self.conn.close()
    def insert(self, list):
        c = self.conn.cursor()
        c.execute("INSERT INTO dhcp_router_config (pool_name, ipaddr, ipaddr_mask, mac) VALUES (?,?,?,?)", list)
        self.conn.commit()

