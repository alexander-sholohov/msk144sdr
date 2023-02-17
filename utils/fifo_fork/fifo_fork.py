#
# @file   fifo_fork.py
# @author Alexander Sholokhov <ra9yer(at)yahoo.com>
# @date   Sun Feb 12 2023
#
# License: MIT
#

import sys
import os
import stat
import errno
import argparse
from threading import Thread
import queue


CHUNK_SIZE = 512
QUEUE_SIZE = 256


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


class FifoFullException(Exception):
    pass


class FifoOut:
    def __init__(self, filename, stop_all_if_full):
        self.filename = filename
        self.stop_all_if_full = stop_all_if_full

        if os.path.exists(filename):
            # ensure file is FIFO
            if not stat.S_ISFIFO(os.stat(filename).st_mode):
                raise Exception(
                    "File '{}' exists, but it is not a FIFO file.".format(filename))
        else:
            os.mkfifo(filename)

        self.fo = None
        self.queue = queue.Queue(QUEUE_SIZE)
        self.flag_stop = False
        self.is_alive = True
        self.thread = Thread(target=fifo_thread, args=(self, ))
        self.thread.start()

    def send(self, data):
        # FIFO is not connected yet.
        if not self.fo:
            return

        need_raise = False
        try:
            self.queue.put(data, block=False)
        except queue.Full:
            if self.stop_all_if_full:
                need_raise = True
            else:
                # We ignore full signal here, this chunk of data will be lost.
                pass

        if need_raise:
            raise FifoFullException(
                "FIFO '{}' is full! Stop all.".format(self.filename))


def fifo_thread(fifo_obj: FifoOut):
    while fifo_obj.is_alive and not fifo_obj.flag_stop:
        eprint("FIFO '{}' is openning ...".format(fifo_obj.filename))
        # We block on open util peer connect!
        fifo_obj.fo = open(fifo_obj.filename, "wb")
        eprint("FIFO '{}' opened. ".format(fifo_obj.filename))

        try:
            while not fifo_obj.flag_stop:
                try:
                    bb = fifo_obj.queue.get(timeout=0.5)
                except queue.Empty:
                    pass
                except:
                    raise
                else:
                    writen = fifo_obj.fo.write(bb)
                    if writen != len(bb):
                        eprint("Stream2tcp. Incomplete send. len={}".format(writen))
                        fifo_obj.is_alive = False
                        fifo_obj.fo.close()
                        return
        except IOError as ex:
            if ex.errno == errno.EPIPE:
                eprint("Broken pipe detectected. Reopen FIFO.")
            else:
                fifo_obj.is_alive = False
                eprint("fifo_thread. IOError: {}".format(ex))
        except Exception as ex:
            fifo_obj.is_alive = False
            eprint("fifo_thread. Exception: {}".format(ex))


def main(out_names, ignore_full_fifo_names, in_file):
    arr = []
    for name in out_names:
        stop_all_if_full = name not in ignore_full_fifo_names
        f = FifoOut(name, stop_all_if_full)
        arr.append(f)

    if in_file:
        binary_io = open(in_file, "rb")
    else:
        binary_io = sys.stdin.buffer

    try:
        while True:
            bb = binary_io.read(CHUNK_SIZE)
            if len(bb) != CHUNK_SIZE:
                raise Exception(
                    "Stream2tcp. Incomplete read from stdin. len={}".format(len(bb)))

            num_processed = 0
            for elm in arr:
                if elm.is_alive:
                    elm.send(bb)
                    num_processed += 1
            if num_processed == 0:
                raise Exception("There are no more output FIFOs. Exit.")
    except:
        for elm in arr:
            elm.flag_stop = True
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='fifo_fork',
        description='This utility accepts stream from stdin and forwards it to multiple FIFOs.',
        epilog='By default overflow of any FIFO will cause program stop. But this behaviour can be changed using --ignore-full-fifo parameter.')

    parser.add_argument(
        '--in-file', help='Use this file as data producer. Not specified parameter means "stdin".')
    parser.add_argument('--out-fifo', nargs='+', help='Output fifo names.')
    parser.add_argument('--ignore-full-fifo', default=[], nargs='*',
                        help='Specify FIFOs which should stop all in case at least one of them fails.')

    args = parser.parse_args()

    # validate
    for elm in args.ignore_full_fifo:
        if elm not in args.out_fifo:
            raise Exception(
                "Name specified in --ignore-full-fifo must be present in filenames. Wrong name='{}'".format(elm))

    main(args.out_fifo, args.ignore_full_fifo, args.in_file)
