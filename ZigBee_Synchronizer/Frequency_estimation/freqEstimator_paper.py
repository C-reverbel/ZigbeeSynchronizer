from System_blocks.ZigBeePacket import ZigBeePacket
from System_blocks.WirelessChannel import WirelessChannel
from System_blocks.CFS_iterative import CFS_iterative
from System_blocks.CFS_direct import CFS_direct
from System_blocks.CPS import CPS
import utils
import numpy as np
import matplotlib.pyplot as plt
from random import randint

def computeMaxIndex(vector, myPacket):
    N = 1
    D = 128
    d = myPacket.IQ[4:4 + N * D]
    print d.__len__()
    maxN = 100
    res = []
    for i in range(maxN):
        temp = abs((np.sum(vector[4+i:4 + N * D + i] * np.conj(d[:])))) ** 2
        temp2 = abs((np.sum(vector[4 + i:4 + N * D + i] * np.conj(vector[4 + i + D:4 + N * D + D + i] )))) ** 2
        res.append(temp)
    index = np.argmax(res)
    print index
    plt.plot(res)
    plt.axvline(x=index)
    plt.show()

if __name__ == "__main__":
    # Zigbee packet
    sampleRate = 8
    zigbeePayloadNbOfBytes = 5
    freqOffset = 5000.0
    phaseOffset = 210.0
    SNR = 4.5
    leadingNoiseSamples = 53
    trailingNoiseSamples = 0

    # Butterworth low-pass filter
    cutoff = 3e6
    fs = sampleRate * 1e6
    order = 0

    print "Zigbee payload size = " + str(zigbeePayloadNbOfBytes) + " bytes"
    print "Sample rate = " + str(sampleRate) + " MHz"
    print "Frequency offset = " + str(freqOffset / 1000) + " kHz"
    print "Phase offset = " + str(phaseOffset) + " Degrees"
    print "SNR = " + str(SNR) + " dB"
    print "\n"

    # ZIGBEE PACKET
    # payload in bytes, sample-rate in MHz
    myPacket = ZigBeePacket(zigbeePayloadNbOfBytes, sampleRate)
    N = myPacket.I.__len__()

    ## CHANNEL
    # sample-rate (MHz), frequency offset (Hz), phase offset (degrees), SNR (db)
    myChannel = WirelessChannel(sampleRate, freqOffset, phaseOffset, SNR)

    ## RECEIVER
    # receive signal and filter it (change filter order to ZERO to disable filtering)
    receivedSignal = utils.butter_lowpass_filter(myChannel.receive(myPacket.IQ,leadingNoiseSamples,trailingNoiseSamples),cutoff, fs, order)

    computeMaxIndex(receivedSignal, myPacket)
