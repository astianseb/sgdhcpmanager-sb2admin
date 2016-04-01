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



@app.route('/sandbox', methods=['GET', 'POST'])
def sandbox():
    import helperfunctions
    global conn
    print request.form
    kom_type = request.form['kom_type']
    os_type = request.form['os_type']
    pool_name = request.form['pool_name']
    mac_address = request.form['mac_address']
    if not pool_name or not mac_address:
        return render_template('error.html', result=["Pool name or mac address missing!"])
    config_list = helperfunctions.create_dhcp_client_config(kom_type, os_type, pool_name, mac_address)
    output = config_list
    return render_template('showcommand.html', result=output)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dhcptable')
def dhcptable():
    import helperfunctions
    myconfig = helperfunctions.DhcpConfig('config.txt')  #reading config to show current data
    config_file = helperfunctions.ConfigFile()           #
    entries = []
    pool_list = myconfig.get_dhcppoolname_list()
    for name in pool_list:
        config = [name, myconfig.get_ipaddr(name), myconfig.get_macaddr(name)]
        entries.append(config)

    config_date = config_file.get_config_date()

    return render_template('dhcptable.html', entries=entries, config_file='config.txt', config_date=config_date)

@app.route('/dbtable')
def dbtable():
    config_file = helperfunctions.ConfigFile()           #
    config_date = config_file.get_config_date()
    db = helperfunctions.DatabaseHandler("rtrconfig.db")
    entries_kom_a = db.get_entries("KOM-A")
    entries_kom_b = db.get_entries("KOM-B")
    return render_template('dbtable.html', entries_kom_a=entries_kom_a, entries_kom_b=entries_kom_b, config_date=config_date)

@app.route('/addremove')
def addremove():
    return render_template('addremove.html')

@app.route('/test')
def test():
    return render_template('test.html')


@app.route('/setup')
def configuration():
    import helperfunctions
    config_file = helperfunctions.ConfigFile()           #
    config_date = config_file.get_config_date()

    return render_template('setup.html', config_file='config.txt', config_date=config_date)


@app.route('/syncconfig', methods=['GET', 'POST'])
def syncconfig():
    helperfunctions.ConfigFile().get_config()
    return render_template('getconfig.html', result=['Success!'])

@app.route('/sync_db_with_config', methods=['GET', 'POST'])
def sync_db_with_config():
    config_list = helperfunctions.build_config_list('config.txt')
    db = helperfunctions.DatabaseHandler('rtrconfig.db')
    db.create_baseline_table()
    for item in config_list:
        db.sync_table_with_list(item)
    return render_template('getconfig.html', result=['Success!'])


@app.route('/show_command', methods=['POST'])
def show_commandlist():
    import helperfunctions
    global conn
    if request.form.has_key('arp_mac_end'):
        mac_end=request.form['arp_mac_end']
        try:
            print "test"
            output = conn.show_arp(mac_end)
        except socket.error:
            print "socket error"
            conn = helperfunctions.Router()
            output = conn.show_arp(mac_end)
        return render_template('showcommand.html', result=output)

    elif request.form.has_key('dhcp_mac_end'):
        mac_end=request.form['dhcp_mac_end']
        try:
            print "test"
            output = conn.show_arp(mac_end)
        except socket.error:
            print "socket error"
            conn = helperfunctions.Router()
            output = conn.show_arp(mac_end)
        return render_template('showcommand.html', result=output)

    elif request.form.has_key('ping_ip'):
        ip = request.form['ping_ip']
        try:
            print "test"
            output = conn.ping_ipaddr(ip)
        except socket.error:
            print "socket error"
            conn = helperfunctions.Router()
            output = conn.ping_ipaddr(ip)
        return render_template('showcommand.html', result=output)

    else:
        print "cos innego"
        output = "Rubbish!"

@app.route('/add_dhcp_client', methods=['POST'])
def add_dhcp_client():
    import helperfunctions
    global conn
    kom_type = request.form['kom_type']
    os_type = request.form['os_type']
    pool_name = request.form['pool_name']
    mac_address = request.form['mac_address']
    if not pool_name or not mac_address:
        return render_template('error.html', result=["Pool name or mac address missing!"])
    config_list = helperfunctions.create_dhcp_client_config(kom_type, os_type, pool_name, mac_address)
    try:
        print "test"
        output = conn.add_dhcp_client(config_list)
    except socket.error:
        print "socket error"
        conn = helperfunctions.Router()
        output = conn.add_dhcp_client(config_list)
    return render_template('showcommand.html', result=output)

@app.route('/delete_dhcp_client', methods=['POST'])
def delete_dhcp_client():
    import helperfunctions
    global conn
    pool_name = request.form['pool_name']
    config_list = helperfunctions.delete_dhcp_client_config(pool_name)
    if ('pool_name' in request.form) or ('radioButton' in request.form):
        try:
            print "test"
            output = conn.delete_dhcp_client(config_list)
        except socket.error:
            print "socket error"
            conn = helperfunctions.Router()
            output = conn.delete_dhcp_client(config_list)
    return render_template('showcommand.html', result=output)


if __name__ == '__main__':
    import helperfunctions
    conn = helperfunctions.Router()  #opening SSH connection at start to speed up command responses

# Build rtrconfig.db from config file
    config_list = helperfunctions.build_config_list('config.txt')
    db = helperfunctions.DatabaseHandler('rtrconfig.db')
    db.create_baseline_table()
    for item in config_list:
        db.sync_table_with_list(item)
    app.run(
        host="0.0.0.0",
        port=int("5000")
    )