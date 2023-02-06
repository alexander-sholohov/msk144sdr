from app import app
from flask import request, jsonify, render_template, send_from_directory, abort, url_for
from werkzeug.utils import secure_filename
import sqlite3
import os

MSK144_API_KEY = os.environ.get("MSK144_API_KEY", "111")


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def spots():
    return render_template('spots.html')


def process_spot(conn, spot_record_id):
    row = conn.execute("SELECT max(id) from all_spots").fetchone()
    spot_last_record_id = row[0] if row[0] else 0
    # created, message, snr, f0, num_avg, num_hard_errors
    rows = conn.execute(
        f"SELECT * from all_spots where id>{spot_record_id}").fetchall()

    arr = []
    for row in rows:
        s = row['created'] + "  "
        s += "snr={:2d}; ".format(int(row['snr']))
        s += "f0={:7.1f}; ".format(row['f0'])
        s += "message={}".format(row['message'])
        arr.append(s)

    return (spot_last_record_id, arr)


def process_wf(conn, wf_record_id):
    row = conn.execute("SELECT max(id) from waterfall_files").fetchone()
    spot_last_record_id = row[0] if row[0] else 0
    # created, message, snr, f0, num_avg, num_hard_errors
    rows = conn.execute(
        f"SELECT * from waterfall_files where id>{wf_record_id} order by id desc limit 30").fetchall()

    arr = [url_for("waterfall_files", path=row['filename'])
           for row in reversed(rows)]

    return (spot_last_record_id, arr)


@app.route('/get_update')
def get_update():
    args = request.args
    spot_record_id = int(args.get('spot_record_id', 0))
    wf_record_id = int(args.get('wf_record_id', 0))

    conn = get_db_connection()
    row = conn.execute("SELECT v from params where k='launch_id'").fetchone()
    launch_id = int(row[0])

    spot_last_record_id, arr_spot = process_spot(conn, spot_record_id)
    wf_last_record_id, arr_wf = process_wf(conn, wf_record_id)

    conn.close()

    res = {"spot_lines": arr_spot, "spot_last_record_id": spot_last_record_id,
           "wf_lines": arr_wf, "wf_last_record_id": wf_last_record_id,
           "launch_id": launch_id}
    return jsonify(res)


def conv_date(s):
    y = s[0:4]
    mo = s[4:6]
    d = s[6:8]
    h = s[8:10]
    m = s[10:12]
    se = s[12:14]
    return f"{y}-{mo}-{d} {h}:{m}:{se}"


def ensure_msk144_api_key_valid():
    api_key = request.form['msk144_api_key']
    if api_key != MSK144_API_KEY:
        abort(400, 'Incorrect msk144 api key')


@app.route('/put_spot', methods=('POST',))
def put_spot():
    ensure_msk144_api_key_valid()
    snr = request.form['snr']
    f0 = request.form['f0']
    num_avg = request.form['num_avg']
    nbadsync = request.form['nbadsync']
    pattern_idx = request.form['pattern_idx']
    created_date = conv_date(request.form['date'])
    msg = request.form['msg']
    num_hard_errors = 0  # request.form['num_hard_errors']

    conn = get_db_connection()
    conn.execute('insert into all_spots (created, message, snr, f0, num_avg, num_hard_errors) values (?, ?, ?, ?, ?, ?);',
                 (created_date, msg, snr, f0, num_avg, num_hard_errors))
    conn.commit()
    conn.close()

    return "OK"


@app.route('/put_waterfall_file', methods=('POST',))
def put_waterfall_file():
    ensure_msk144_api_key_valid()
    # validate date
    for ch in request.form['date']:
        if ch < '0' or ch > '9':
            abort(400, 'Bad date format')
    created_date = conv_date(request.form['date'])
    dir_name = request.form['date'][:8]
    dst_dir = os.path.join(app.config['UPLOAD_FOLDER'], dir_name)
    if not os.path.isdir(dst_dir):
        os.makedirs(dst_dir)

    f = request.files['file']
    filename = secure_filename(f.filename)
    f.save(os.path.join(dst_dir, filename))

    db_file_name = dir_name + "/" + filename

    conn = get_db_connection()
    conn.execute('insert into waterfall_files (created, filename) values (?, ?);',
                 (created_date, db_file_name))
    conn.commit()
    conn.close()

    return "OK"


@app.route('/waterfall_files/<path:path>')
def waterfall_files(path):
    return send_from_directory(directory=app.config['UPLOAD_FOLDER'], path=path)
