import queue
import sqlite3
from typing import List

import pandas as pd

from fbgui import helpers
from fbgui.constants import DB_PATH, CAL
from fbgui.datatable import DataTable
from fbgui.exceptions import ProgramStopped
from fbgui.messages import *


class DatabaseController:
    def __init__(self, file_path: str, fbg_names: List[str], main_queue: queue.Queue,
                 function_type: str, table: DataTable = None):
        self.main_queue = main_queue
        self.table = table
        self.function_type = function_type
        self.file_path = None  # type: str
        self.file_name = None  # type: str
        self.fbg_names = None  # type: List[str]
        self.column_names = None  # type: List[str]
        self.reset_controller(file_path, fbg_names)

    def reset_controller(self, file_path: str, fbg_names: List[str]):
        self.file_path = file_path
        self.file_name = helpers.get_file_name(self.file_path)
        self.fbg_names = fbg_names
        self.column_names = create_column_names(fbg_names)
        if self.function_type == CAL:
            add_calibration_column_names(self.column_names)
        table_column_names = [s.replace("'", "") for s in self.column_names]
        if self.table is not None:
            self.table.setup_headers(table_column_names, reset=True)

    def record_baking_point(self, timestamp: float, temperature: float, wavelengths: List[float], powers: List[float]):
        column_command_string = ",".join(self.create_database_column_commands())
        readable_time = datetime.datetime.fromtimestamp(int(timestamp)).strftime("%d/%m/%y %H:%M")
        wavelength_power = create_wavelength_power_list(wavelengths, powers)
        values = [readable_time, *wavelength_power, temperature]
        self.record_point(column_command_string, values, timestamp)

    def record_calibration_point(self, timestamp: float, temperature: float, wavelengths: List[float],
                                 powers: List[float], drift_rate: float,
                                 is_real_calibration_point: bool, cycle_num: int):
        column_commands = self.create_database_column_commands()
        add_calibration_commands(column_commands)
        column_command_string = ",".join(column_commands)
        readable_time = datetime.datetime.fromtimestamp(int(timestamp)).strftime("%d/%m/%y %H:%M")
        wavelength_power = create_wavelength_power_list(wavelengths, powers)
        values = [readable_time, *wavelength_power, temperature, drift_rate,
                  "'{}'".format(is_real_calibration_point), cycle_num]
        self.record_point(column_command_string, values, timestamp)

    def record_point(self, column_command_string: str, values: List, timestamp: float):
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        if not self.program_exists(cursor):
            self.create_program_table(cursor, column_command_string)

        if self.table is not None:
            self.table.add_data(values)
        table_id = self.get_table_id(cursor)
        values[0] = timestamp
        values = ",".join([str(value) for value in values])
        add_baking_command = "INSERT INTO {}({}) VALUES ({})".format(self.function_type.lower() + str(table_id),
                                                                     ",".join(self.column_names), values)
        try:
            cursor.execute(add_baking_command)
            connection.commit()
        except sqlite3.OperationalError as sql_error:
            self.handle_sql_error(sql_error)
        connection.close()

    def create_database_column_commands(self) -> List[str]:
        """
        Returns a list of strings used for creating the database attribute values, includes names and SQL types.

        :return: list of comma separated strings, names and types of table attributes
        """
        fbg_columns = []
        for fbg_name in self.fbg_names:
            fbg_columns.append("'{} Wavelength (nm.)' REAl NOT NULL".format(fbg_name))
            fbg_columns.append("'{} Power (dBm.)' REAL NOT NULL".format(fbg_name))
        col_list = ["ID INTEGER NOT NULL PRIMARY KEY", "'Date Time' REAL NOT NULL",
                    *fbg_columns, "'Mean Temperature (K)' REAL NOT NULL"]
        return col_list

    def create_program_table(self, cursor: sqlite3.Cursor, columns: str):
        try:
            self.add_entry_to_map(cursor)
        except sqlite3.OperationalError:
            cursor.execute("CREATE TABLE 'map' ( 'ID' INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,"
                           "'ProgName' TEXT NOT NULL, 'ProgType' INTEGER NOT NULL, 'FilePath' TEXT, 'Snums' TEXT )")
            self.add_entry_to_map(cursor)
        table_id = self.get_table_id(cursor)
        cursor.execute("CREATE TABLE `{}` ({});".format(self.function_type.lower() + str(table_id), columns))

    def get_table_id(self, cursor):
        cursor.execute("SELECT ID FROM map WHERE ProgName = '{}';".format(self.file_name))
        return cursor.fetchall()[0][0]

    def add_entry_to_map(self, cursor: sqlite3.Cursor):
        cursor.execute("INSERT INTO map('ProgName','ProgType','FilePath','Snums') VALUES ('{}','{}','{}','{}')"
                       .format(self.file_name, self.function_type.lower(), self.file_path, ",".join(self.fbg_names)))

    def handle_sql_error(self, sql_error: sqlite3.OperationalError):
        try:
            if "column" in sql_error:
                msg = Message(MessageType.ERROR, "Configuration Error",
                              "Serial numbers have changed from the first time this program was run. Please "
                              "use a new file name.")
                self.main_queue.put(msg)
                raise ProgramStopped
        except TypeError as type_error:
            self.main_queue.put(Message(MessageType.DEVELOPER, "Write DB sqlite3 Error Dump", str(sql_error)))
            self.main_queue.put(Message(MessageType.DEVELOPER, "Write DB Type Error Dump", str(type_error)))

    def get_last_cycle_num(self) -> int:
        """
        Get the number of the last calibration cycle that data is recorded for.

        :return: last calibration cycle number, or 0 if there is no data calibration recorded
        """
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        try:
            table_id = self.get_table_id(cursor)
        except (sqlite3.OperationalError, IndexError):
            connection.close()
            return 0
        table_name = self.function_type.lower() + str(table_id)
        cursor.execute("SELECT {}.'Cycle Num' FROM {};".format(table_name, table_name))
        last_cycle_num = cursor.fetchall()
        last_cycle_num = last_cycle_num[-1][0]
        connection.close()
        return int(last_cycle_num)

    def to_data_frame(self) -> pd.DataFrame:
        """
        Creates a pandas dataframe object from the database table corresponding to the program run of type
        func, and named name.

        :return: dataframe for the specified table, or an empty dataframe if one cannot be created for the table
        :raises IndexError: If program is not in the map, thus data has not been recorded for this program yet
        :raises RuntimeError: If program database has been corrupted, or the table is empty
        """
        connection = None
        try:
            connection = sqlite3.connect(DB_PATH)
            cursor = connection.cursor()
            table_id = self.get_table_id(cursor)
            df = pd.read_sql_query("SELECT * from {}".format(self.function_type.lower() + str(table_id)), connection)
            del df["ID"]
            connection.close()
            return df
        except (pd.io.sql.DatabaseError, sqlite3.OperationalError):
            if connection is not None:
                connection.close()
            return pd.DataFrame()
        except (RuntimeError, IndexError) as e:
            if connection is not None:
                connection.close()
            raise e

    def program_exists(self, cursor: sqlite3.Cursor = None) -> bool:
        """
        Checks whether or not there is data in the database for the program of type func, named name.

        :param cursor: the database cursor
        :return: True if the program exists, otherwise False
        """
        connection = None
        if cursor is None:
            connection = sqlite3.connect(DB_PATH)
            cursor = connection.cursor()
        try:
            cursor.execute("SELECT ID, ProgName, ProgType from map")
            rows = cursor.fetchall()
        except sqlite3.OperationalError:
            if connection is not None:
                connection.close()
            return False

        if connection is not None:
            connection.close()

        names = [row[1] for row in rows]
        types = [row[2] for row in rows]
        try:
            index = names.index(self.file_name)
            if types[index] == self.function_type.lower():
                return True
        except ValueError:
            return False


def create_wavelength_power_list(wavelengths: List[float], powers: List[float]):
    wavelength_power = []
    for wave, power in zip(wavelengths, powers):
        wavelength_power.append(wave)
        wavelength_power.append(power)
    return wavelength_power


def add_calibration_commands(columns: List[str]):
    columns.append("'Drift Rate' REAL NOT NULL")
    columns.append("'Real Point' INTEGER NOT NULL")
    columns.append("'Cycle Num' INTEGER NOT NULL")


def create_column_names(fbg_names: List[str]) -> List[str]:
    """
    Create the data column headers.

    :param fbg_names: serial numbers for the current program run
    :return: list of header strings
    """
    fbg_columns = []
    for fbg_name in fbg_names:
        fbg_columns.append("'{} Wavelength (nm.)'".format(fbg_name))
        fbg_columns.append("'{} Power (dBm.)'".format(fbg_name))
    columns = ["'Date Time'", *fbg_columns, "'Mean Temperature (K)'"]
    return columns


def add_calibration_column_names(columns: List[str]):
    columns.append("'Drift Rate'")
    columns.append("'Real Point'")
    columns.append("'Cycle Num'")
