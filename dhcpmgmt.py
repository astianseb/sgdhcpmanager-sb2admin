#!/bin/python

import os
from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash
import socket

conn = None

app = Flask(__name__)

app.config.update(dict(
    DATABASE='',
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


# This route will return a list in JSON format

@app.route('/')
def index():
    return render_template('index.html')



@app.route('/dhcp')
def dhcp():
    import routerconfig
    db = routerconfig.ConfigDB()
    myconfig = routerconfig.DhcpConfig('config.txt')  #reading config to show current data
    config_file = routerconfig.ConfigFile()           #
    entries = []
    pool_list = myconfig.get_dhcppoolname_list()
    for name in pool_list:
        config = [name, myconfig.get_ipaddr(name), myconfig.get_ipaddrmask(name), myconfig.get_macaddr(name)]
        db.insert(tuple(config))
        entries.append(config)

    config_date = config_file.get_config_date()

    return render_template('dhcp.html', entries=entries, config_file='config.txt', config_date=config_date)

@app.route('/configuration')
def configuration():
    import routerconfig
    config_file = routerconfig.ConfigFile()           #
    config_date = config_file.get_config_date()

    return render_template('configuration.html', config_file='config.txt', config_date=config_date)


@app.route('/getconfig', methods=['GET', 'POST'])
def getconfig():
    routerconfig.ConfigFile().get_config()
    return render_template('getconfig.html', result='Success!')

@app.route('/show_command', methods=['POST'])
def show_commandlist():
    import routerconfig
    global conn
    if request.form.has_key('arp_mac_end'):
        mac_end=request.form['arp_mac_end']
        try:
            print "test"
            output = conn.show_arp(mac_end)
        except socket.error:
            print "socket error"
            conn = routerconfig.Router()
            output = conn.show_arp(mac_end)
        return render_template('showcommand.html', result=output)

    elif request.form.has_key('dhcp_mac_end'):
        mac_end=request.form['dhcp_mac_end']
        try:
            print "test"
            output = conn.show_arp(mac_end)
        except socket.error:
            print "socket error"
            conn = routerconfig.Router()
            output = conn.show_arp(mac_end)
        return render_template('showcommand.html', result=output)

    elif request.form.has_key('ping_ip'):
        ip = request.form['ping_ip']
        try:
            print "test"
            output = conn.ping_ipaddr(ip)
        except socket.error:
            print "socket error"
            conn = routerconfig.Router()
            output = conn.ping_ipaddr(ip)
        return render_template('showcommand.html', result=output)

    else:
        print "cos innego"
        output = "Rubbish!"

@app.route('/add_dhcp_client', methods=['POST'])
def add_dhcp():
    import routerconfig
    global conn
    pool_name = request.form['pool_name']
    ip_address = request.form['ip_address']
    mac_address = request.form['mac_address']
    config_list = routerconfig.create_config(pool_name, ip_address, mac_address)
    try:
        print "test"
        output = conn.add_dhcp_client(config_list)
    except socket.error:
        print "socket error"
        conn = routerconfig.Router()
        output = conn.add_dhcp_client(config_list)
    return render_template('showcommand.html', result=output)

@app.route('/delete_dhcp_client', methods=['POST'])
def delete_dhcp():
    import routerconfig
    global conn
    pool_name = request.form['pool_name']
    command = 'no ip dhcp pool' + ' ' + pool_name
    config_list = [command]
    try:
        print "test"
        output = conn.delete_dhcp_client(config_list)
    except socket.error:
        print "socket error"
        conn = routerconfig.Router()
        output = conn.delete_dhcp_client(config_list)
    return render_template('showcommand.html', result=output)


if __name__ == '__main__':
    import routerconfig
    conn = routerconfig.Router()  #opening SSH connection at start to speed up command responses
    db = routerconfig.ConfigDB()
    db.create_db()
    app.run(
        host="0.0.0.0",
        port=int("5000")
    )