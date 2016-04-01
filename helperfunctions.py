from netmiko import ConnectHandler
from ciscoconfparse import CiscoConfParse
import sqlite3
import os, time


homeRTR = {
    'device_type':'cisco_ios',
    'ip':'192.168.0.1',
    'username':'admin',
    'password':'xxxx',
    'port':'22',
}


def build_config_list(config_file):
    config = DhcpConfig(config_file)
    config_list=[]
    for pool_name in config.get_dhcppoolname_list():
        mac_address = config.get_macaddr(pool_name)
        ip_address = config.get_ipaddr(pool_name)
        config_list.append([pool_name, mac_address, ip_address])
    return config_list


def create_dhcp_client_config(kom_type, os_type, pool_name, mac_address):
    db = DatabaseHandler('rtrconfig.db')

    if os_type == "windows":
        line3 = 'client-identifier' + ' ' + '01' + mac_address
    else:
        line3 = 'hardware-address' + ' ' + mac_address

    if kom_type == 'KOM-A':
        ip_address = db.get_free_ip(kom_type)
        line1 = 'ip dhcp pool' + ' ' + 'STATIC-KOMA-' + pool_name
        line2 = 'host' + ' ' + str(ip_address) + ' ' + '255.255.255.0'
        line4 = 'default-router 192.168.4.1'
    if kom_type == 'KOM-B':
        ip_address = db.get_free_ip(kom_type)
        line1 = 'ip dhcp pool' + ' ' + 'STATIC-KOMB-' + pool_name
        line2 = 'host' + ' ' + str(ip_address) + ' ' + '255.255.255.0'
        line4 = 'default-router 192.168.5.1'

    line5 = 'dns-server 194.204.159.1'
    line6 = 'update arp'
    return [line1, line2, line3, line4, line5, line6]

def delete_dhcp_client_config(pool_name):
    line1 = 'no ip dhcp pool' + ' ' + pool_name
    return [line1, ]


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
        return time.strftime('%d/%m/%Y %H:%M', time.gmtime(t))

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


class DatabaseHandler:
    def __init__(self, db):
        self.conn = sqlite3.connect(db)

    def create_baseline_table(self):
        c = self.conn.cursor()
        c.execute('''DROP TABLE IF EXISTS ip_to_mac;''')
        c.execute('''CREATE TABLE ip_to_mac(
            kom_type TEXT,
            pool_name TEXT,
            ip_address TEXT,
            mac_address TEXT,
            istaken TEXT);''')
        self.conn.commit()
        for j in range(0, 3):
            if j == 0:
                kom_type = "KOM-A"
                octet = "4"
            if j == 1:
                kom_type = "KOM-B"
                octet = "5"
            for i in range(2, 240):
                ip_address = "192.168." + str(octet) + "." + str(i)
                c.execute('''
                INSERT INTO ip_to_mac (kom_type, ip_address, istaken) VALUES (?, ?, ?)
                ''', (kom_type, ip_address, "N"))
        self.conn.commit()

    def sync_table_with_list(self, list):
        self.list = list
        c = self.conn.cursor()
        c.execute(''' UPDATE ip_to_mac
                    SET pool_name = ?, mac_address = ?, istaken = ?
                    WHERE ip_address = ?
        ''', (self.list[0], self.list[1], "Y", self.list[2]))
        self.conn.commit()

    def get_free_ip(self, kom_type):
        c = self.conn.cursor()
        c.execute(''' SELECT ip_address FROM ip_to_mac
                    WHERE kom_type = ? AND istaken = "N"
                    LIMIT 1''', (kom_type,))
        free_ip = c.fetchone()
        return free_ip[0]

    def get_entries(self, kom_type):
        c = self.conn.cursor()
        c.execute(''' SELECT pool_name, ip_address, mac_address FROM ip_to_mac
                    WHERE kom_type = ? AND istaken = "Y" ''', (kom_type,))
        entries = c.fetchall()
        return entries


