#                   _________                         _____                             _____
#                  |         |                       |     |                           |     |
#  myPacket.IQ --> | CHANNEL | -- receivedSignal --> | CFS | -- preCorrectedSignal --> | CPS | --> correctedSignal
#                  |_________|                       |_____|                           |_____|
#
from ZigBeePacket import ZigBeePacket
from WirelessChannel import WirelessChannel
from CFS2 import CFS2
from CPS import CPS
import utils
import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":
    # Zigbee packet
    nbOfSamples = 256
    sampleRate = 8
    zigbeePayloadNbOfBytes = 127
    freqOffset = 200e3
    phaseOffset = 10
    SNR = 10.
    # Butterworth low-pass filter
    cutoff = 2e6
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
    receivedSignal = utils.butter_lowpass_filter(myChannel.receive(myPacket.IQ), cutoff, fs, order)

    ## CFS
    # sample rate (MHz), number of samples - 2 to compute linear regression
    synchronizer = CFS2(sampleRate, nbOfSamples, 4)
    # estimate frequency and phase offset
    phaseDifference = np.unwrap(np.angle(receivedSignal)) - np.unwrap(np.angle(myPacket.IQ))
    freqOffsetEstimated, phaseOffsetEstimated = synchronizer.estimateFrequencyAndPhaseIterative(phaseDifference)
    correctionVector = synchronizer.generatePhaseVector(freqOffsetEstimated, phaseOffsetEstimated)
    # correct received signal with correctionVector
    preCorrectedSignal = synchronizer.compensatePhase(correctionVector, receivedSignal)



    errF = freqOffsetEstimated[-1] - freqOffset
    errP = phaseOffsetEstimated[-1] - phaseOffset

    print "CFS estimated frequency and phase offset"
    print "Frequency = " + str(freqOffsetEstimated[-1])
    print "Phase = " + str(phaseOffsetEstimated[-1])
    print "Frequency Error = " + str(freqOffsetEstimated[-1] - freqOffset)
    print "Phase Error = " + str(phaseOffsetEstimated[-1] - phaseOffset) + "\n"

    ## CPS
    synchronizer2 = CPS(sampleRate)
    correctedSignal, phaseVector = synchronizer2.costasLoop(100000, preCorrectedSignal)




    ## PLOT
    # time vector
    maxTime = (1e-6 / sampleRate) * N
    timeStep = 1e-6 / sampleRate
    time = np.arange(0, maxTime, timeStep)

    plt.subplot(211)
    plt.plot(1e6*time, phaseDifference)
    plt.subplot(212)
    phaseDifference = np.unwrap(np.angle(preCorrectedSignal)) - np.unwrap(np.angle(myPacket.IQ))
    plt.plot(1e6*time, phaseDifference, 'r')

    phaseDifference = np.unwrap(np.angle(correctedSignal)) - np.unwrap(np.angle(myPacket.IQ))
    plt.plot(1e6*time, phaseDifference, 'b')
    plt.show()


    # ideal received signal, no freq or phase offset
    myNoisyChannel = WirelessChannel(sampleRate, 0, 0, SNR)
    idealReceivedSignal = utils.butter_lowpass_filter(myNoisyChannel.receive(myPacket.IQ), cutoff, fs, order)

    idealReceivedSignal.imag = np.roll(idealReceivedSignal.imag, -4)
    correctedSignal.imag = np.roll(correctedSignal.imag, -4)
    preCorrectedSignal.imag = np.roll(preCorrectedSignal.imag, -4)

    # constellation plot: QPSK
    receivedConstellation, = plt.plot(preCorrectedSignal.real[4::8], preCorrectedSignal.imag[4::8], 'gx')
    idealConstellation, = plt.plot(idealReceivedSignal.real[4::8], idealReceivedSignal.imag[4::8], 'bo')
    plt.axvline(x=0)
    plt.axhline(y=0)
    plt.legend([idealConstellation, receivedConstellation], ['IDEAL CONSTELLATION', 'PRE-CORRECTED CONSTELLATION'], loc=3)
    idealConstellation.set_linewidth(0.1)
    plt.ylim(-2, 2)
    plt.xlim(-2, 2)
    plt.title("QPSK CONSTELLATION - IDEAL VS PRE-CORRECTED")
    plt.show()
    # constellation plot: QPSK
    receivedConstellation, = plt.plot(correctedSignal.real[4::8], correctedSignal.imag[4::8], 'rx')
    idealConstellation, = plt.plot(idealReceivedSignal.real[4::8], idealReceivedSignal.imag[4::8], 'bo')
    plt.axvline(x=0)
    plt.axhline(y=0)
    plt.legend([idealConstellation, receivedConstellation], ['IDEAL CONSTELLATION', 'CORRECTED CONSTELLATION'], loc=3)
    idealConstellation.set_linewidth(0.1)
    plt.ylim(-2, 2)
    plt.xlim(-2, 2)
    plt.title("QPSK CONSTELLATION - IDEAL VS CORRECTED")
    plt.show()

    offset = 30000
    #rec, = plt.plot(receivedSignal.real[offset:offset + 100], 'g')
    #rec.set_linewidth(0.5)
    plt.plot(correctedSignal.real[offset:offset + 100], 'r')
    plt.plot(preCorrectedSignal.real[offset:offset + 100], 'k')
    plt.plot(idealReceivedSignal.real[offset:offset + 100], 'b--')
    plt.show()
