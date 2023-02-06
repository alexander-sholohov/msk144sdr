#
# @file   init_db.py
# @author Alexander Sholokhov <ra9yer(at)yahoo.com>
# @date   Mon Feb 06 2023
#
import sys
import datetime
import os
import math

import numpy as np
import PIL.Image
import PIL.ImageDraw
import requests

import wf_config as config

MSK144_API_KEY = os.environ.get("MSK144_API_KEY", "111")

g_color_map = []


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def build_color_map():
    palette = []

    palette.append((0,  0,  255))
    palette.append((0,  62, 194))
    palette.append((0, 126, 130))
    palette.append((0, 190,  66))
    palette.append((0, 254, 2))
    palette.append((62, 194, 0))
    palette.append((126, 130, 0))
    palette.append((190, 66,  0))
    palette.append((254, 2,  0))

    assert (len(palette) == 9)

    def getcolor(pos, a, b): return a + (b - a) * pos / 32.0
    for idx in range(256):
        low = idx // 32
        high = low + 1
        x = idx - low * 32
        r = getcolor(x, palette[low][0], palette[high][0])
        g = getcolor(x, palette[low][1], palette[high][1])
        b = getcolor(x, palette[low][2], palette[high][2])
        g_color_map.append((round(r), round(g), round(b)))


def process_minute(cur_date, buf, num_chunks):
    img_height = 110
    power_line_base = img_height - 1
    spectrum_line_base = img_height - 30
    timeline_base = spectrum_line_base - 66
    datetime_base = img_height - 30

    im = PIL.Image.new('RGBA', (num_chunks, img_height), (0, 0, 0, 255))
    draw = PIL.ImageDraw.Draw(im)

    def f(x): return complex(x, 0)
    vfunc = np.vectorize(f)

    fft_gain = math.pow(10.0, 0.1 * config.FFT_IN_GAIN)
    rms_gain = math.pow(10.0, 0.1 * config.RMS_IN_GAIN)

    fac = math.pow(1 / 512, 2)

    arr_graph_pow = np.zeros((num_chunks,), dtype=int)
    arr_graph_spectrum = np.zeros((num_chunks, 64), dtype=int)

    for blk_idx in range(num_chunks):
        data = buf[blk_idx*512:(blk_idx+1)*512]

        sq = np.dot(data, data)
        rms = math.sqrt(rms_gain * sq / 512.0)
        graph_pow = 20.0 * math.log10(rms) if rms > 0 else 0.0
        arr_graph_pow[blk_idx] = graph_pow

        signal6 = vfunc(data)
        spectrum = np.fft.fft(signal6)
        q = np.abs(spectrum)

        # 0..128 - means 0..3kHz; map 3kHz to 64 points
        for idx in range(64):
            arr_graph_spectrum[blk_idx][idx] = (q[idx*2]
                                                + q[idx*2+1]) * fac * fft_gain

    # draw spectrum
    for blk_idx in range(num_chunks):
        for p_idx in range(64):
            v = int(arr_graph_spectrum[blk_idx, p_idx]
                    * config.FFT_IMAGE_SCALE)
            if v < 0:
                v = 0
            if v > 255:
                v = 255
            s_color = g_color_map[v]
            draw.point((blk_idx, spectrum_line_base - p_idx), fill=s_color)

    # make green power line at bottom
    rms_line_shift = np.min(arr_graph_pow) - 2
    # draw green power line
    fill_color = (0, 255, 0)
    def gety(y): return power_line_base - \
        int(config.RMS_IMAGE_SCALE * (y - rms_line_shift))
    for blk_idx in range(num_chunks):
        if blk_idx == 0:
            v = arr_graph_pow[blk_idx]
            draw.point((blk_idx, gety(v)), fill=fill_color)
        else:
            v1 = arr_graph_pow[blk_idx - 1]
            v2 = arr_graph_pow[blk_idx]
            draw.line((blk_idx-1, gety(v1), blk_idx,
                       gety(v2)), fill=fill_color)

    # draw timeline 1sec
    for idx in range(60):
        x = idx * num_chunks / 60
        draw.line((x, timeline_base, x, timeline_base-4), fill=(255, 255, 255))

    # draw timeline 5sec
    draw.line((0, timeline_base, num_chunks, timeline_base),
              fill=(255, 255, 255))
    for idx in range(12):
        x = idx * num_chunks / 12
        draw.line((x, timeline_base, x, timeline_base-8), fill=(255, 255, 255))
        s = "{:02d}".format(idx*5)
        draw.text((x+3, timeline_base-10), s, align="left")

    #
    s = cur_date.strftime("%Y-%m-%d %H:%M:00")
    draw.text((0, datetime_base), s, align="left")

    filename_only = "w{}.png".format(cur_date.strftime("%Y%m%d%H%M00"))
    filename = os.path.join(config.TMP_DIR, filename_only)
    im.save(filename)

    if config.UPLOAD_FILE_URL:
        with open(filename, 'rb') as fv:
            files = {'file': fv}
            values = {
                'date': cur_date.strftime("%Y%m%d%H%M00"),
                'msk144_api_key': MSK144_API_KEY}
            try:
                res = requests.post(config.UPLOAD_FILE_URL,
                                    files=files, data=values, timeout=5)
                if res.status_code != 200:
                    eprint("Send result: {}".format(res.text))
            except Exception as ex:
                eprint("Upload file error: {}".format(ex))

    os.unlink(filename)


def main():
    num_samples_per_minute = 12000 * 60
    NUM_SAMPLES_IN_CHUNK = 512  # 512 - FFT
    num_chunks = num_samples_per_minute // NUM_SAMPLES_IN_CHUNK
    if num_samples_per_minute % NUM_SAMPLES_IN_CHUNK != 0:
        num_chunks += 1

    num_samples_aligned = NUM_SAMPLES_IN_CHUNK * num_chunks

    arr = np.zeros((num_samples_aligned,), dtype=int)

    prev_date = datetime.datetime.now()

    # process_minute(prev_date, arr, num_chunks)

    if config.DUP_TO_FILE_FILENAME:
        fo = open(config.DUP_TO_FILE_FILENAME, "wb")
    num_minutes = 0
    pos = 0
    while True:
        # duplicate to stdout
        bb = sys.stdin.buffer.read(NUM_SAMPLES_IN_CHUNK * 2)
        if len(bb) != NUM_SAMPLES_IN_CHUNK * 2:
            raise Exception(
                "Incomplete read from stdin. len={}".format(len(bb)))
        # assert (len(bb) == NUM_SAMPLES_IN_CHUNK * 2)
        if config.DUP_TO_STDOUT_ENABLED:
            sys.stdout.buffer.write(bb)
        if config.DUP_TO_FILE_FILENAME:
            fo.write(bb)

        # fill array
        for idx in range(NUM_SAMPLES_IN_CHUNK):
            arr[pos+idx] = int.from_bytes(bb[idx*2:idx*2+2],
                                          "little", signed=True)
        pos += NUM_SAMPLES_IN_CHUNK

        date = datetime.datetime.now()
        if date.minute != prev_date.minute:
            # Next minute detected.
            num_minutes += 1
            # Skip first incomplete minute.
            if num_minutes > 1:
                buf = np.roll(arr, -(pos - num_samples_aligned))
                process_minute(prev_date, buf, num_chunks)
        prev_date = date

        assert (pos <= num_samples_aligned)

        if pos == num_samples_aligned:
            pos = 0


def create_tmpdir_if_need():
    if config.TMP_DIR and not os.path.isdir(config.TMP_DIR):
        os.mkdir(config.TMP_DIR)


if __name__ == "__main__":
    build_color_map()
    create_tmpdir_if_need()
    main()
