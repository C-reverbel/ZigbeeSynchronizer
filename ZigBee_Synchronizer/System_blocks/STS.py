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
    test = np.correlate(receivedSignal.real, matchedKernel, mode='full')
    # Gardner
    test2 = np.zeros(test.__len__())
    for i in range(test2.__len__() -2):
        test2[i+1] = (test[i+2] - test[i]) * test[i+1]

    pltMax = 20

    plt.plot(receivedSignal.real[:pltMax], 'b')
    plt.plot(test[:pltMax], 'g-x')
    plt.plot(test2[:pltMax], '-rx')
    plt.plot(myPacket.I[:pltMax], linewidth = 0.5)

    index = [i for i, j in enumerate(abs(myPacket.I[:pltMax])) if j <= 0.1 or j >= 0.99]

    print index
    for i in range(index.__len__()):
        plt.axvline(x = index[i], linewidth = 0.5)
    plt.axhline(y=0, linewidth = 0.5)
    plt.show()
