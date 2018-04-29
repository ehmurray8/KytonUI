import os
import constants
import sqlite3


def reset_config():
    if not os.path.isdir(constants.CONFIG_PATH):
        os.mkdir(constants.CONFIG_PATH)
    if not os.path.isdir(constants.DB_DIR):
        os.mkdir(constants.DB_DIR)

    conn = sqlite3.connect("db\\program_data.db")
    cur = conn.cursor()

    try:
        cur.execute('SELECT * FROM map;')
        cur.fetchall()
    except:
        cur.execute("CREATE TABLE 'map' ( 'ID' INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,"
                        "'ProgName' TEXT NOT NULL, 'ProgType' INTEGER NOT NULL, 'FilePath' TEXT, 'Snums' TEXT )")


    if not os.path.isfile(constants.DEV_CONFIG_PATH):
            print("""
[Devices]
controller_location =
oven_location = 
op_switch_address = 
op_switch_port = 
sm125_address = 
sm125_port = 
""", file=open(constants.DEV_CONFIG_PATH, "w"))

    if not os.path.isfile(constants.PROG_CONFIG_PATH):
            print("""
[Baking]
running = false
num_scans = 5
set_temp = 150
drift_rate = 5.0
prim_interval = 1.0
file = 
last_folder = 
chan1_fbgs = 
chan1_positions = 
chan2_fbgs = 
chan2_positions = 
chan3_fbgs = 
chan3_positions = 
chan4_fbgs = 
chan4_positions = 

[Cal]
running = false
use_cool = 0
num_scans = 5
num_temp_readings = 2
temp_interval = 60.0
drift_rate = 5.0
num_cycles = 5
target_temps = 40.0,60.0,80.0,100.0,120.0
file =
last_folder = 
chan1_fbgs = 
chan1_positions = 
chan2_fbgs = 
chan2_positions = 
chan3_fbgs = 
chan3_positions = 
chan4_fbgs = 
chan4_positions = 
        """, file=open(constants.PROG_CONFIG_PATH, "w"))
