import pyodbc

conn_str = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=C:\Users\Emmet\AppData\Local\Databases\kyton.accdb;'
conn = pyodbc.connect(conn_str)
cur = conn.cursor()
cur.execute("CREATE TABLE test_test8 (ID INT PRIMARY KEY, 'Delta Time' DOUBLE NOT NULL, Timestamp1 DOUBLE, 'FBG1 Wavelength' DOUBLE);")
conn.commit()
cur.execute("INSERT INTO test_test8 VALUES (1, 12.1, 111111111111.1, 1500.1);")
conn.commit()
cur.execute("SELECT * FROM test_test8;")
print(cur.fetchall())