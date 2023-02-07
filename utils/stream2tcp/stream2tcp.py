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
from queue import Queue, Full, Empty


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


class Context:
    def __init__(self) -> None:
        self.is_write_to_queue_enabled = False
        self.queue = Queue(32)
        self.socket = None
        self.flag_stop = False


def process(connection, ctx: Context):
    try:
        while not ctx.flag_stop:
            try:
                bb = ctx.queue.get(timeout=0.5)
            except Empty:
                pass
            except:
                raise
            else:
                rc = connection.send(bb)
                if rc != len(bb):
                    eprint("Stream2tcp. Incomplete send. len={}".format(rc))
                    connection.close()
                    return
    except Exception as ex:
        eprint("Stream2tcp. Error: {}".format(ex))


def tcp_thread(addr_pair, ctx: Context):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(addr_pair)
    sock.listen(1)

    flag_msg_once = True
    while not ctx.flag_stop:
        if flag_msg_once:
            eprint("stream2tcp. Before accept ...")
            flag_msg_once = False
        try:
            connection, address = sock.accept()
        except socket.timeout:
            pass
        except:
            raise
        else:
            flag_msg_once = True
            eprint("stream2tcp. Connection accepted from: {}".format(address))
            #
            ctx.is_write_to_queue_enabled = True
            ctx.socket = connection
            process(connection, ctx)
            ctx.socket = None
            ctx.is_write_to_queue_enabled = False

            # clear queue
            while not ctx.queue.empty():
                try:
                    ctx.queue.get(block=False)
                except Empty:
                    break
            time.sleep(1) # for some reason

def main(addr_pair):
    ctx = Context()

    thread = Thread(target=tcp_thread, args=(addr_pair, ctx))
    thread.start()

    try:
        while True:
            bb = sys.stdin.buffer.read(512)
            if len(bb) != 512:
                raise Exception(
                    "Stream2tcp. Incomplete read from stdin. len={}".format(len(bb)))
            if ctx.is_write_to_queue_enabled:
                try:
                    ctx.queue.put(bb, block=False)
                except Full:
                    if ctx.socket:
                        eprint("Stream2tcp. buffer full. close socket.")
                        ctx.socket.close()
                        ctx.socket = None
                        ctx.is_write_to_queue_enabled = False
                    else:
                        eprint("f")
    except:
        ctx.flag_stop = True
        raise


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
