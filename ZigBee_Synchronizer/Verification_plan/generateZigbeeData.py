#                   _________                         _____                             _____
#                  |         |                       |     |                           |     |
#  myPacket.IQ --> | CHANNEL | -- receivedSignal --> | CFS | -- preCorrectedSignal --> | CPS | --> correctedSignal
#                  |_________|                       |_____|                           |_____|
#
import sys
sys.path.append('../')

import os
from System_blocks.ZigBeePacket import ZigBeePacket
from System_blocks.WirelessChannel import WirelessChannel
from System_blocks.CPS import CPS
import utils
import numpy as np
import matplotlib.pyplot as plt

def lowRes(val, nbBits):
    N = val.__len__()
    res = range(N)
    maxVal = (2 ** (nbOfBits - 1) - 1)
    for i in range(N):
        temp = int(val[i] * maxVal)
        res[i] = int(maxVal if temp > maxVal else (-maxVal if temp < -maxVal else temp))
    return res
def int_to_twoCompl(val, nbBits):
    N = val.__len__()
    res = range(N)
    mask = 2 ** nbBits - 1
    for i in range(N):
        temp = int(val[i])
        if temp < 0:
            temp = abs(temp)
            temp = (temp ^ mask) + 1
        res[i] = "{0:016b}".format(temp)
    return res
def twoCompl_to_hex(val):
    N = val.__len__()
    res = range(N)
    for i in range(N):
        res[i] = "{0:04x}".format(int(val[i], 2))
    return res
def float_to_int_bin_hex(val, nbOfBits):
    intLowRes = lowRes(val, nbOfBits)
    bits = int_to_twoCompl(intLowRes, nbOfBits)
    hexa = twoCompl_to_hex(bits)
    return intLowRes, bits, hexa
def getFileName(folderName, name_initial, zigbeePayloadNbOfBytes, freqOffset, phaseOffset, SNR, nbOfBits):
    try:
        if not os.path.exists(folderName):
            os.makedirs(folderName)
    except OSError:
        print ('Error: Creating directory. ' + folderName)

    result = "./" + str(folderName) + "/" + str(name_initial)
    result += str(zigbeePayloadNbOfBytes) + "bytes_" + \
              str(freqOffset) + "Hz_" + \
              str(phaseOffset) + "Deg_" + \
              str(SNR) + "dB_" + \
              str(nbOfBits) + "b.txt"
    return result

if __name__ == "__main__":
    # Zigbee packet
    sampleRate = 8
    zigbeePayloadNbOfBytes = 127
    freqOffset = 500.
    phaseOffset = 35.
    SNR = 10.
    nbOfBits = 16
    leadingNoiseSamples = 0
    trailingNoiseSamples = 0
    # get values from command prompt
    try:
        if sys.argv > 1 : zigbeePayloadNbOfBytes = int(sys.argv[1])
        if sys.argv > 2 : freqOffset = float(sys.argv[2])
        if sys.argv > 3 : phaseOffset = float(sys.argv[3])
        if sys.argv > 4 : SNR = float(sys.argv[4])
        if sys.argv > 5 : nbOfBits = int(sys.argv[5])
    except:
        print "No arguments passed. Default parameters used."
        print "python generateZigbeeData.py payloadNbOfBytes frequency_offset phase_offset SNR nbOfBits"
        print "----------------------------------------------------------------------------------------"
        print " - payloadNbOfBytes = number of bytes of packet payload, default = " + str(zigbeePayloadNbOfBytes)
        print " - frequency_offset in Hz,                               default = " + str(freqOffset) + " Hz"
        print " - phase_offset in degrees,                              default = " + str(phaseOffset) + " degrees"
        print " - SNR (Signal to Noise Ratio) in dB,                    default = " + str(SNR) + " dB"
        print " - nbOfBits = data resolution in bits,                   default = " + str(nbOfBits) + " bits"
        print ""

    # Butterworth low-pass filter (NOT USED)
    cutoff = 2.5e6
    fs = sampleRate * 1e6
    order = 0   # oder = 0 means no filter
    # payload in bytes, sample-rate in MHz
    myPacket = ZigBeePacket(zigbeePayloadNbOfBytes, sampleRate)
    N = myPacket.I.__len__()
    # time vector
    maxTime = (1e-6 / sampleRate) * N
    timeStep = 1e-6 / sampleRate
    time = np.arange(0, maxTime, timeStep)
    # channel
    myChannel = WirelessChannel(sampleRate, freqOffset, phaseOffset, SNR)
    receivedSignal = utils.butter_lowpass_filter(myChannel.receive(myPacket.IQ, leadingNoiseSamples, trailingNoiseSamples), cutoff, fs, order)
    # low resolution signal
    maxVal = (2 ** (nbOfBits - 1) - 1)
    # get ideal signals
    i_ideal_int, i_ideal_bin, i_ideal_hex = float_to_int_bin_hex(myPacket.IQ.real, nbOfBits)
    q_ideal_int, q_ideal_bin, q_ideal_hex = float_to_int_bin_hex(myPacket.IQ.imag, nbOfBits)
    # get raw signals
    i_raw_int, i_raw_bin, i_raw_hex = float_to_int_bin_hex(receivedSignal.real, nbOfBits)
    q_raw_int, q_raw_bin, q_raw_hex = float_to_int_bin_hex(receivedSignal.imag, nbOfBits)
    # format new low-res raw data from -1 to +1
    rec_int = np.zeros(N) + 1j * np.zeros(N)
    for i in range(N):
        rec_int[i] = float(i_raw_int[i])/maxVal + 1j * float(q_raw_int[i])/maxVal
    # receiver
    synchronizer = CPS(sampleRate)
    correctedSignal, phaseVector, correctedBits = synchronizer.costasLoop(850000, rec_int)
    # get corrected signals
    i_corr_int, i_corr_bin, i_corr_hex = float_to_int_bin_hex(correctedSignal.real, nbOfBits)
    q_corr_int, q_corr_bin, q_corr_hex = float_to_int_bin_hex(correctedSignal.imag, nbOfBits)
    # get delta_phi signal
    scaled_delta_phi = phaseVector / np.pi
    delta_phi_int, delta_phi_bin, delta_phi_hex = float_to_int_bin_hex(scaled_delta_phi, nbOfBits)
    print "DELTA_PHI"
    print [delta_phi_hex[x] for x in range(10)]

    folderName = "sim_values"
    name_i_ideal = getFileName(folderName, "i_ideal_", zigbeePayloadNbOfBytes, freqOffset, phaseOffset, SNR, nbOfBits)
    name_q_ideal = getFileName(folderName, "q_ideal_", zigbeePayloadNbOfBytes, freqOffset, phaseOffset, SNR, nbOfBits)
    name_i_raw   = getFileName(folderName, "i_raw_"  , zigbeePayloadNbOfBytes, freqOffset, phaseOffset, SNR, nbOfBits)
    name_q_raw   = getFileName(folderName, "q_raw_"  , zigbeePayloadNbOfBytes, freqOffset, phaseOffset, SNR, nbOfBits)
    name_i_corr  = getFileName(folderName, "i_corr_" , zigbeePayloadNbOfBytes, freqOffset, phaseOffset, SNR, nbOfBits)
    name_q_corr  = getFileName(folderName, "q_corr_" , zigbeePayloadNbOfBytes, freqOffset, phaseOffset, SNR, nbOfBits)
    name_delta_phi = getFileName(folderName, "delta_phi_", zigbeePayloadNbOfBytes, freqOffset, phaseOffset, SNR, nbOfBits)

    f_i_ideal = open(name_i_ideal, 'w')
    f_q_ideal = open(name_q_ideal, 'w')
    f_i_raw   = open(name_i_raw,   'w')
    f_q_raw   = open(name_q_raw,   'w')
    f_i_corr  = open(name_i_corr,  'w')
    f_q_corr  = open(name_q_corr,  'w')
    f_delta_phi = open(name_delta_phi, 'w')

    for i in range(N):
        f_i_ideal.write(i_ideal_hex[i] + "\n")
        f_q_ideal.write(q_ideal_hex[i] + "\n")
        f_i_raw.write(i_raw_hex[i] + "\n")
        f_q_raw.write(q_raw_hex[i] + "\n")
        f_i_corr.write(i_corr_hex[i] + "\n")
        f_q_corr.write(q_corr_hex[i] + "\n")
        f_delta_phi.write(delta_phi_hex[i] + "\n")

    f_i_ideal.close()
    f_q_ideal.close()
    f_i_raw.close()
    f_q_raw.close()
    f_i_corr.close()
    f_q_corr.close()
    f_delta_phi.close()

    print "Successfully generated random Zigbee packet with:"
    print "- " + str(zigbeePayloadNbOfBytes) + " bytes payload;"
    print "- " + str(freqOffset) + " Hz frequency offset;"
    print "- " + str(phaseOffset) + " Degrees phase offset;"
    print "- " + str(SNR) + " dB SNR;"
    print "-------------------------------------------------"
    print "Output files inside folder ./" + str(folderName) + "/ with " + str(nbOfBits) + " bits resolution."

    plt.subplot(2,1,1)
    plt.plot(scaled_delta_phi)
    plt.subplot(2, 1, 2)
    plt.plot(phaseVector)
    plt.show()
    ### PRINT ###
    print "HEX  BIN              INT"
    print "-------------------------"
    for i in range(16):
        print q_ideal_int[i], q_ideal_bin[i], q_ideal_hex[i]

    printOffset = 20000
    printRange = 100

    idealI, = plt.plot(i_ideal_int[printOffset:printOffset + printRange],'b-')
    rawI, = plt.plot(i_raw_int[printOffset:printOffset + printRange], 'g-')
    corrI, = plt.plot(i_corr_int[printOffset:printOffset + printRange], 'r-')
    rawI.set_linewidth(0.5)
    plt.axhline(linewidth=2, color='g', y=maxVal)
    plt.axhline(linewidth=2, color='g', y=-maxVal)
    plt.show()

    idealQ, = plt.plot(q_ideal_int[printOffset:printOffset + printRange], 'b-')
    rawQ, = plt.plot(q_raw_int[printOffset:printOffset + printRange], 'g-')
    corrQ, = plt.plot(q_corr_int[printOffset:printOffset + printRange], 'r-')
    rawQ.set_linewidth(0.5)
    plt.axhline(linewidth=2, color='g', y=maxVal)
    plt.axhline(linewidth=2, color='g', y=-maxVal)
    plt.show()
