#                   _________                         _____                             _____
#                  |         |                       |     |                           |     |
#  myPacket.IQ --> | CHANNEL | -- receivedSignal --> | CFS | -- preCorrectedSignal --> | CPS | --> correctedSignal
#                  |_________|                       |_____|                           |_____|
#
from System_blocks.ZigBeePacket import ZigBeePacket
from System_blocks.WirelessChannel import WirelessChannel
from System_blocks.CFS_iterative import CFS_iterative
import utils
import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":
    # Zigbee packet
    nbOfSamples = 128
    sampleRate = 8
    zigbeePayloadNbOfBytes = 127
    freqOffset = 200e3
    phaseOffset = 30
    SNR = 10.
    # Butterworth low-pass filter
    cutoff = 2.5e6
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

    accFreqErrorVector = np.zeros(8)
    accPhaseErrorVector = np.zeros(8)
    nbOfSimulations = 100
    for i in range(1,9):
        for j in range(nbOfSimulations):
            # sample-rate (MHz), frequency offset (Hz), phase offset (degrees), SNR (db)
            myChannel = WirelessChannel(sampleRate, freqOffset, phaseOffset, SNR)
            # receive signal and filter it (change filter order to ZERO to disable filtering)
            receivedSignal = np.roll(utils.butter_lowpass_filter(myChannel.receive(myPacket.IQ), cutoff, fs, order), 0)
            ##receivedSignal = np.roll(receivedSignal, -2)
            # number of samples used to estimate frequency and phase
            nbOfSamples = i * 128
            # sample rate (MHz), number of samples - 2 to compute linear regression
            synchronizer = CFS_iterative(sampleRate, nbOfSamples)
            # estimate frequency and phase offset
            phaseDifference = np.unwrap(np.angle(receivedSignal)) - np.unwrap(np.angle(myPacket.IQ))
            freqOffsetEstimated, phaseOffsetEstimated = synchronizer.estimateFrequencyAndPhaseIterative(phaseDifference)
            #print freqOffsetEstimated[-1] - freqOffset, phaseOffsetEstimated[-1] - phaseOffset
            # compute phase and frequency error
            accFreqErrorVector[i-1]  += abs(freqOffsetEstimated[-1] - freqOffset)   / nbOfSimulations
            accPhaseErrorVector[i-1] += abs(phaseOffsetEstimated[-1] - phaseOffset) / nbOfSimulations

    # plot frequency and phase error
    print "freq error = ", accFreqErrorVector
    print "phase error = ", accPhaseErrorVector
    plt.subplot(211)
    plt.plot(128 * np.arange(1,9), accFreqErrorVector, '--ro')
    plt.xticks(range(128,1025,128))
    plt.title("Frequency estimation error vs number of samples - SNR = " + str(SNR) + " dB")
    plt.ylabel("Frequency error (Hz)")
    plt.ylim(0, 750)
    plt.yticks(np.arange(0,1000,100))
    plt.grid(b=None, which='major', axis='both')
    plt.axhline(y=0)

    plt.subplot(212)
    plt.plot(128 * np.arange(1, 9), accPhaseErrorVector, '--bo')
    plt.xticks(range(128, 1025, 128))
    plt.title("Phase estimation error vs number of samples - SNR = " + str(SNR) + " dB")
    plt.ylabel("Phase error (degrees)")
    plt.xlabel("number of samples")
    plt.ylim(0, 4)
    plt.grid(b=None, which='major', axis='both')
    plt.axhline(y=0)

    plt.show()
