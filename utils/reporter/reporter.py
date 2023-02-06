#
# @file   reporter.py
# @author Alexander Sholokhov <ra9yer(at)yahoo.com>
# @date   Mon Feb 06 2023
#

import sys
import re
import os
import argparse

import requests

MSK144_API_KEY = os.environ.get("MSK144_API_KEY", "111")

DEFAULT_URL = 'http://127.0.0.1:5000/msk144/put_spot'
DEFAULT_DUP_FILE = "result.txt"


def send(url, obj_to_send):
    try:
        obj_to_send["msk144_api_key"] = MSK144_API_KEY
        msg = obj_to_send["msg"]
        res = requests.post(url, data=obj_to_send, timeout=10)
        print("Send result: {}. msg={}".format(res.text, msg))
    except Exception as ex:
        print("Send exception: {}".format(ex))


def main(url, dup_file):
    splt = re.compile(r"(\w+)=([^;]+)")
    with open(dup_file, "a") as fo:
        for line in sys.stdin:
            # Duplicate to stdout
            print(line)

            if line.startswith("*** "):
                # Duplicate to file
                fo.write(line)
                fo.flush()
                try:
                    m = splt.findall(line)
                    res = {k: v for (k, v) in m}
                    integer_types = ["num_avg", "nbadsync", "pattern_idx"]
                    float_types = ["snr", "f0"]
                    quoted_types = ["msg"]
                    for k in res:
                        if k in integer_types:
                            res[k] = int(res[k])
                        if k in float_types:
                            res[k] = float(res[k])
                        if k in quoted_types:
                            res[k] = res[k][1:-1]

                    send(url, res)
                except Exception as ex:
                    print("Exception: {}".format(ex))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='MSK144 Sport Reporter',
        description='This utility grabs output from msk144cudecoder and sends success decodes to msk144sdr web server.')

    parser.add_argument('--url', default=DEFAULT_URL,
                        help="URL to send decodes to. (default: %(default)s)")
    parser.add_argument('--dup-file', default=DEFAULT_DUP_FILE,
                        help="A file name to save a copy of decodes. (default: %(default)s)")
    args = parser.parse_args()
    print("Will report to url: {}".format(args.url))
    main(args.url, args.dup_file)
