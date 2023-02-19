import os
import sqlite3

import config


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


def main():
    conn = get_db_connection()

    sql = "select * from waterfall_files where created<date('now', '-6 day')"
    rows = conn.execute(sql).fetchall()
    ids_to_del = []
    folders = set()
    for row in rows:
        dir_name, file_name = os.path.split(row['filename'])
        full_name = os.path.join(config.UPLOAD_FOLDER, dir_name, file_name)
        if os.path.isfile(full_name):
            print(f"Remove file '{full_name}' ...")
            try:
                os.remove(full_name)
                ids_to_del.append(row['id'])
            except Exception as ex:
                print("Unable to remove file: {}".format(ex))
        else:
            print(f"File '{full_name}' does not exist.")
            ids_to_del.append(row['id'])

        folders.add(dir_name)

    for folder in folders:
        folder_name = os.path.join(config.UPLOAD_FOLDER, folder)
        print(f"Remove folder '{folder_name}' ...")
        try:
            os.rmdir(folder_name)
        except Exception as ex:
            print("Unable to remove folder: {}".format(ex))

    if ids_to_del:
        s = ",".join([str(x) for x in ids_to_del])
        sql = "delete from waterfall_files where id in ({})".format(s)
        conn.execute(sql)
        conn.commit()

    conn.close()


if __name__ == "__main__":
    main()
