#
# @file   init_db.py
# @author Alexander Sholokhov <ra9yer(at)yahoo.com>
# @date   Mon Feb 06 2023
#

import socket
import sys
import time
import argparse


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def process(addr_pair):
    try:
        eprint("stream2tcp. Connecting to {}:{} ...".format(addr_pair[0], addr_pair[1]))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(addr_pair)
        eprint("stream2tcp. Connected")
        while True:
            bb = sock.recv(512)
            if len(bb) == 0:
                eprint("stream2tcp. Empty read. Exit loop.")
                sock.close()
                return
            sys.stdout.buffer.write(bb)
    except Exception as ex:
        eprint("stream2tcp. Error: {}".format(ex))


def main(addr_pair):
    while True:
        process(addr_pair)
        time.sleep(15)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='stream2tcp',
        description='This utility establishes tcp connection with remote host, reads data and forwards stream to stdout (something like "nc addr port"). On disconnect it waits 15 seconds and tries to connect again.')
    parser.add_argument('--address', default="127.0.0.1",
                        help="IP address to connect to. Default %(default)s.")
    parser.add_argument('--port', type=int, default=5050,
                        help="Destination port  (default: %(default)s)")

    args = parser.parse_args()
    addr_pair = (args.address, args.port)
    main(addr_pair)
