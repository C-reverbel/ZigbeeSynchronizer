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
    zigbeePayloadNbOfBytes = 20
    freqOffset = 200000.0
    phaseOffset = 0.0
    SNR = 10.
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
    matchedI = np.correlate(receivedSignal.real, matchedKernel, mode='full')
    matchedQ = np.correlate(receivedSignal.imag, matchedKernel, mode='full')

    matched = matchedI + 1j * matchedQ
    matched_ideal = np.correlate(myPacket.I, matchedKernel, mode='full') + 1j * np.correlate(myPacket.Q, matchedKernel, mode='full')

    matchedI_bin = np.zeros(matchedI.__len__())
    matchedQ_bin = np.zeros(matchedQ.__len__())

    thres = 1.0
    for i in range(matchedI.__len__()):
        matchedI_bin[i] = 1.0 if matchedI[i] > thres else (-1.0 if matchedI[i] < -thres else 0)
        matchedQ_bin[i] = 1.0 if matchedQ[i] > thres else (-1.0 if matchedQ[i] < -thres else 0)

    matched_bin = matchedI_bin + 1j * matchedQ_bin

    phaseKernel = np.unwrap(np.angle(matched_ideal[4:132]))


    maxPlot = 100
    plt.subplot(2,1,1)
    plt.plot(myPacket.I[:maxPlot])
    plt.plot(matchedI[:maxPlot])
    plt.plot(matched_bin.real[:maxPlot])
    plt.axhline(y=0,linewidth=0.5)
    plt.subplot(2, 1, 2)
    plt.plot(myPacket.Q[:maxPlot])
    plt.plot(matchedQ[:maxPlot])
    plt.plot(matched_bin.imag[:maxPlot])
    plt.axhline(y=0, linewidth=0.5)
    plt.show()

    phaseCorr = np.correlate(np.unwrap(np.angle(matched)), phaseKernel, mode='full')

    plt.plot(phaseCorr[:1000])
    plt.show()
