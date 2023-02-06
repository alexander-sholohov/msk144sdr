#!/bin/sh
export LD_LIBRARY_PATH=./
nc 192.168.1.200 2223 | ./csdr convert_u8_f | ./csdr shift_addition_cc 0.3125 | ./csdr fir_decimate_cc 64.0 0.005 HAMMING | ./csdr bandpass_fir_fft_cc 0 0.12 0.06 | ./csdr realpart_cf | ./csdr rational_resampler_ff 3 8 | ./csdr gain_ff 100.0 | ./csdr limit_ff | ./csdr convert_f_i16 | python split_waterfall.py 

