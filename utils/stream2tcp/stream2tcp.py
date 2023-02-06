#
# @file   stream2tcp.py
# @author Alexander Sholokhov <ra9yer(at)yahoo.com>
# @date   Mon Feb 06 2023
#

import socket
import sys
import time
import argparse
from threading import Thread


g_enable_dummy_stream_consumer = True


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def dummy_stream_consumer():
    while True:
        if g_enable_dummy_stream_consumer:
            bb = sys.stdin.buffer.read(512)
        else:
            time.sleep(0.5)


def process(connection):
    try:
        while True:
            bb = sys.stdin.buffer.read(512)
            if len(bb) != 512:
                eprint("Stream2tcp. Incomplete read from stdin. return. len={}".format(len(bb)))
                connection.close()
                return
            connection.send(bb)
    except Exception as ex:
        eprint("Stream2tcp. Error: {}".format(ex))


def main(addr_pair):
    global g_enable_dummy_stream_consumer
    thread = Thread(target=dummy_stream_consumer)
    thread.start()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(addr_pair)
    sock.listen(1)
    while True:
        eprint("stream2tcp. Before accept ...")
        connection, address = sock.accept()
        eprint("stream2tcp. Connection accepted from: {}".format(address))
        #
        g_enable_dummy_stream_consumer = False
        process(connection)
        g_enable_dummy_stream_consumer = True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='stream2tcp',
        description='This utility accepts stdin stream and forwards it through server socket tcp connection. (Something like "nc -l -p"). Only one incoming connection is possible at a time.')
    parser.add_argument('--bind-address', default="127.0.0.1",
                        help="Default %(default)s . Set to 0.0.0.0 if you want to listen on all interfaces.")
    parser.add_argument('--bind-port', type=int, default=5050,
                        help="Port to bind to.  (default: %(default)s)")

    args = parser.parse_args()

    addr_pair = (args.bind_address, args.bind_port)
    eprint("Will listen on {}:{}".format(addr_pair[0], addr_pair[1]))
    main(addr_pair)
