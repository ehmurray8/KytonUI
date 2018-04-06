import sqlite3
import os

if __name__ == "__main__":
    conn = sqlite3.connect("program_data.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM map;")
    tuples = cur.fetchall()

    ids = [tup[0] for tup in tuples]
    names = [tup[1] for tup in tuples]

    for i, name in zip(ids, names):
        cur.execute("UPDATE map SET 'FilePath' = '{}', 'Snums' = '{}' WHERE id = {};"
                    .format(os.path.join(r"C:\Users\phils\Documents\BAKES", name) + ".xlsx",
                            "KY1001PKOPEN,KY1003PKCLOSED,KY1004PKCLOSED", i))

    conn.commit()
    conn.close()
