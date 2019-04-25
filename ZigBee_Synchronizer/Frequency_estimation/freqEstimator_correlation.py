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
    zigbeePayloadNbOfBytes = 50
    freqOffset = 100000.0
    phaseOffset = 0.0
    SNR = 4.
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

    for i in range(5):
        SNR = SNR + 2.0
        ## CHANNEL
        # sample-rate (MHz), frequency offset (Hz), phase offset (degrees), SNR (db)
        myChannel = WirelessChannel(sampleRate, freqOffset, phaseOffset, SNR)
        # receive signal and filter it (change filter order to ZERO to disable filtering)
        receivedSignal = utils.butter_lowpass_filter(
                            myChannel.receive(myPacket.IQ,
                                              leadingNoiseSamples,
                                              trailingNoiseSamples),
                            cutoff, fs, order)

        idealPhaseKernel = np.unwrap(np.angle(myPacket.IQ[4:132]))

        matchedKernel = [0.0, 0.382683432, 0.707106781, 0.923879533, 1.0, 0.923879533, 0.707106781, 0.382683432, 0.0]

        recMatched = np.correlate(receivedSignal.real, matchedKernel, mode='full') + 1j * np.correlate(receivedSignal.imag, matchedKernel, mode='full')

        recPhase = np.unwrap(np.angle(receivedSignal))

        correlation = np.correlate(recPhase, idealPhaseKernel, mode='full')

        m = max(correlation[:180])
        index = [i for i, j in enumerate(correlation[:400]) if j == m]
        plt.plot(correlation[:512])
        plt.axvline(x=index[0])
        print SNR, index[0]
    plt.show()

    plt.plot(idealPhaseKernel)
    plt.plot(recPhase[:512])
    plt.show()

    # matched Filter
    test = np.correlate(receivedSignal.real, matchedKernel, mode='full')
    # Gardner
    test2 = np.zeros(test.__len__())
    for i in range(test2.__len__() -2):
        test2[i+1] = (test[i+2] - test[i]) * test[i+1]

    pltMax = 60

    plt.plot(receivedSignal.real[:pltMax], 'b')
    plt.plot(test[:pltMax], 'g')
    plt.plot(test2[:pltMax], 'r')

    index = [i for i, j in enumerate(abs(test2[:pltMax])) if j <= 0.5]

    print index
    for i in range(index.__len__()):
        plt.axvline(x = index[i], linewidth = 0.5)
    plt.axhline(y=0)
    plt.show()
