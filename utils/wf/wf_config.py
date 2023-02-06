import sys

DUP_TO_STDOUT_ENABLED = False
DUP_TO_FILE_FILENAME = None

if sys.platform == "win32":
    TMP_DIR = "./_outimg"
else: 
    TMP_DIR = "/run/msk144"

UPLOAD_FILE_URL = "http://127.0.0.1:5000/msk144/put_waterfall_file"

FFT_IN_GAIN = 12.0
RMS_IN_GAIN = 0.0
FFT_IMAGE_SCALE = 20.0
RMS_IMAGE_SCALE = 1.0
