from System_blocks.ZigBeePacket import ZigBeePacket
from System_blocks.WirelessChannel import WirelessChannel
from System_blocks.CFS_iterative import CFS_iterative
from System_blocks.CFS_direct import CFS_direct
from System_blocks.CPS import CPS
import utils
import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":
    # Zigbee packet
    sampleRate = 8
    zigbeePayloadNbOfBytes = 0
    freqOffset = 0.0
    phaseOffset = 0.0
    SNR = 8.
    leadingNoiseSamples = 0
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

    # payload in bytes, sample-rate in MHz
    myPacket = ZigBeePacket(zigbeePayloadNbOfBytes, sampleRate)
    N = myPacket.I.__len__()

    ## CHANNEL
    # sample-rate (MHz), frequency offset (Hz), phase offset (degrees), SNR (db)
    myChannel = WirelessChannel(sampleRate, freqOffset, phaseOffset, SNR)
    # receive signal and filter it (change filter order to ZERO to disable filtering)
    receivedSignal = utils.butter_lowpass_filter(
        myChannel.receive(myPacket.IQ,
                          leadingNoiseSamples,
                          trailingNoiseSamples),
        cutoff, fs, order)


    matchedKernel = [0.0, 0.382683432, 0.707106781, 0.923879533, 1.0, 0.923879533, 0.707106781, 0.382683432, 0.0]

    # matched Filter
    matched = np.correlate(receivedSignal.real, matchedKernel, mode='full')
    # Gardner
    gardner = np.zeros(matched.__len__())
    for i in range(gardner.__len__() -2):
        gardner[i+1] = (matched[i+2] - matched[i]) * matched[i+1]

    pltMax = 260

    rec, = plt.plot(receivedSignal.real[:pltMax], 'b')
    match, = plt.plot(matched[:pltMax], 'g-x')
    gard, = plt.plot(gardner[:pltMax], '-rx')
    ideal, = plt.plot(myPacket.I[:pltMax], linewidth = 0.5)
    plt.legend([rec, match, gard], ['RECEIVED I', 'MATCHED FILTER OUTPUT', 'GARDNER OUTPUT'])

    index = [i for i, j in enumerate(abs(myPacket.I[:pltMax])) if j <= 0.1 or j >= 0.99]
    for i in range(index.__len__()):
        plt.axvline(x = index[i], linewidth = 0.5)
    plt.axhline(y=0, linewidth = 0.5)

    plt.show()

    # new algorithm
    tempPlus = 0
    tempMinus = 0
    bits = []
    for i in range(gardner.__len__()):
        if (matched[i] > 0.05): tempPlus = tempPlus + 1
        if (matched[i] < 0.05): tempMinus = tempMinus + 1
        if (tempPlus > 6):
            bits.append(1)
            tempPlus = 0
            tempMinus = 0
        if (tempMinus > 6):
            bits.append(0)
            tempMinus = 0
            tempPlus = 0

    # ideal bits
    print [int(myPacket.messageI[i]) for i in range(N/8)]
    # received bits
    print bits[:]

    for i in range(N/8):
        if bits[i] != int(myPacket.messageI[i]):
            print "error on index ", i


