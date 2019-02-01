#                   _________                         _____                             _____
#                  |         |                       |     |                           |     |
#  myPacket.IQ --> | CHANNEL | -- receivedSignal --> | CFS | -- preCorrectedSignal --> | CPS | --> correctedSignal
#                  |_________|                       |_____|                           |_____|
#
from ZigBeePacket import ZigBeePacket
from WirelessChannel import WirelessChannel
from CFS2 import CFS2
import utils
import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":
    # Zigbee packet
    nbOfSamples = 128
    sampleRate = 8
    zigbeePayloadNbOfBytes = 127
    freqOffset = 500e3
    phaseOffset = 30
    SNR = 10
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
    # sample-rate (MHz), frequency offset (Hz), phase offset (degrees), SNR (db)
    myChannel = WirelessChannel(sampleRate, freqOffset, phaseOffset, SNR)
    # receive signal and filter it (change filter order to ZERO to disable filtering)
    receivedSignal = np.roll(utils.butter_lowpass_filter(myChannel.receive(myPacket.IQ), cutoff, fs, order),0)

    accErrorVector = np.zeros(8)
    nbOfSimulations = 30
    for i in range(1,9):
        for j in range(nbOfSimulations):
            nbOfSamples = i * 128
            # sample rate (MHz), number of samples - 2 to compute linear regression
            synchronizer = CFS2(sampleRate, nbOfSamples)
            # estimate frequency and phase offset
            idealUnwrappedPhase = np.unwrap(np.angle(myPacket.IQ))
            receivedUnwrappedPhase = np.unwrap(np.angle(receivedSignal))
            phaseDifference = receivedUnwrappedPhase - idealUnwrappedPhase
            freqOffsetEstimated, phaseOffsetEstimated = synchronizer.estimateFrequencyAndPhaseIterative(phaseDifference)
            correctionVector = synchronizer.generatePhaseVector(freqOffsetEstimated, phaseOffsetEstimated)
            # correct received signal
            preCorrectedSignal = synchronizer.compensatePhase(correctionVector, receivedSignal)


            accErrorVector[i-1] += utils.calcAverageError(myPacket.IQ[6:N - 2:4], preCorrectedSignal[6:N - 2:4]) / nbOfSimulations

    # normalize result
    accErrorVector = accErrorVector / accErrorVector[0]
    plt.plot(128 * np.arange(1,9),accErrorVector, '--bo')
    plt.show()