CSDR_CMD = './csdr'

rfSampRate = 2048000
shift = str(float(145000000-144360000)/rfSampRate)
stage1SampRate = 32000
AUDIO_SAMPLE_RATE = 12000
decimation = str(2048000.0 / stage1SampRate)

CMD_CHAIN = []
CMD_CHAIN.append( ['nc', '192.168.1.200', '2223'] )
#CMD_CHAIN.append( ['cat', '/dev/urandom'] )
CMD_CHAIN.append( [CSDR_CMD, 'convert_u8_f']  )
CMD_CHAIN.append( [CSDR_CMD, 'shift_addition_cc', shift] )
CMD_CHAIN.append( [CSDR_CMD, 'fir_decimate_cc', decimation, '0.005', 'HAMMING'] )
CMD_CHAIN.append( [CSDR_CMD, 'bandpass_fir_fft_cc', '0', '0.12', '0.06'] )
CMD_CHAIN.append( [CSDR_CMD, 'realpart_cf'] )
CMD_CHAIN.append( [CSDR_CMD, 'rational_resampler_ff', '3', '8' ] ) 
CMD_CHAIN.append( [CSDR_CMD, 'gain_ff', '100.0'] ) 
#CMD_CHAIN.append( [CSDR_CMD, 'agc_ff' ] ) # ??? fastagc_ff ?? agc_ff
CMD_CHAIN.append( [CSDR_CMD, 'limit_ff'] )
CMD_CHAIN.append( [CSDR_CMD, 'convert_f_i16'] )

cmds = []
for elm in CMD_CHAIN:
    cmds.append(" ".join(elm))

print(" | ".join(cmds))