#!/usr/bin/python

from flask import Flask, request, render_template, Response
from ina219 import INA219
from subprocess import check_output
from re import findall
from datetime import timedelta

import datetime
import time
import sqlite3
import threading



app = Flask(__name__)
db_name = "/home/pi/flask229/electricity"
    
def voltageGetThread():
    ina = INA219(shunt_ohms = 0.1, address = 0x40)
    ina.configure()
    while True:
        database = sqlite3.connect(db_name)
        cursor = database.cursor()
        systemTime = datetime.datetime.now()  
        print("Voltage: %.3f, Time: %s" % (ina.voltage(), systemTime))
        insert = cursor.execute('INSERT INTO electrostats (voltage, time) VALUES (?, ?)', (ina.voltage(), systemTime))
        database.commit()
        database.close()
        time.sleep(600)

@app.route('/')
def index():
    #request_uptime = check_output(['uptime', 'p']).decode().split(' ')[4].replace(',', '').split(':')
    #uptime = request_uptime[0] + " hours, " + request_uptime[1] + " minutes."
    temp = check_output(['vcgencmd', 'measure_temp']).decode()
    temp = float(findall("\d+\.\d", temp)[0])
    current_time = str(findall("\d{2}:\d{2}:\d{2}", time.ctime())[0])
    uptime = 0
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
        uptime = str(timedelta(0, uptime_seconds))
    content = []
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    sel = cursor.execute('select time, voltage from electrostats')
    for line in sel:
        content.append(line)
    conn.close()
    
    return render_template("index.html", contentArray=content, currenttime=current_time, uptime=uptime, temp=str(temp))
@app.route('/get_file')
def get_file():
    csv = "Date;Voltage\n"
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    sel = cursor.execute('select time, voltage from electrostats')
    for line in sel:
        csv += line[0] + ";" + str(line[1]) + "\n"
    conn.close()
    return Response(csv, mimetype="text/csv", headers={"Content-disposition":"attachment; filename=1.csv"})
@app.route('/clear_table')
def clear_table():
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    delete = cursor.execute('DELETE FROM electrostats')
    conn.commit()
    conn.close()
    return index()

@app.route('/refresh')
def refresh():
    return index()    

if __name__ == "__main__":
    t = threading.Thread(target=voltageGetThread)
    t.daemon = True
    t.start()
    app.run(debug=False, host='0.0.0.0')
    
