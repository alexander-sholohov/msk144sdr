import sqlite3

schema = """ 
DROP TABLE IF EXISTS all_spots;

CREATE TABLE all_spots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TIMESTAMP NOT NULL,
    message TEXT NOT NULL,
    snr REAL NOT NULL,
    f0  REAL NOT NULL,
    num_avg INTEGER NOT NULL,
    num_hard_errors INTEGER NOT NULL
);

-- insert into all_spots (created, message, snr, f0, num_avg, num_hard_errors) values ('2023-01-29 12:13:14', 'HELLO1', -5.0, 1500.0, 3, 2);

DROP TABLE IF EXISTS params;

CREATE TABLE params (
    k TEXT NOT NULL,
    v TEXT NOT NULL
);

INSERT INTO params(k,v) VALUES('launch_id', '1');

DROP TABLE IF EXISTS waterfall_files;

CREATE TABLE waterfall_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TIMESTAMP NOT NULL,
    filename TEXT NOT NULL
);


"""

arr = schema.split(";")

connection = sqlite3.connect('database.db')
cur = connection.cursor()
for sql in arr:
    cur.execute(sql)

connection.commit()
connection.close()

print("Done")
