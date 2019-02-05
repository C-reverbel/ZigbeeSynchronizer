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
    phaseOffset = 50
    SNR = 30
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

    ## CHANNEL
    # sample-rate (MHz), frequency offset (Hz), phase offset (degrees), SNR (db)
    myChannel = WirelessChannel(sampleRate, freqOffset, phaseOffset, SNR)
    # receive signal and filter it (change filter order to ZERO to disable filtering)
    receivedSignal = utils.butter_lowpass_filter(myChannel.receive(myPacket.IQ), cutoff, fs, order)

    ## CFS
    # sample rate (MHz), number of samples - 2 to compute linear regression
    synchronizer = CFS2(sampleRate, nbOfSamples, 4)
    # estimate frequency and phase offset
    idealUnwrappedPhase = np.unwrap(np.angle(myPacket.IQ))
    receivedUnwrappedPhase = np.unwrap(np.angle(receivedSignal))
    phaseDifference = receivedUnwrappedPhase - idealUnwrappedPhase
    freqOffsetEstimated, phaseOffsetEstimated = synchronizer.estimateFrequencyAndPhaseIterative(phaseDifference)
    correctionVector = synchronizer.generatePhaseVector(freqOffsetEstimated, phaseOffsetEstimated)
    # correct received signal
    preCorrectedSignal = synchronizer.compensatePhase(correctionVector, receivedSignal)

    plt.plot(phaseDifference[:1000])
    plt.show()

    errF = freqOffsetEstimated[-1] - freqOffset
    errP = phaseOffsetEstimated[-1] - phaseOffset

    print "CFS estimated frequency and phase offset"
    print "Frequency = " + str(freqOffsetEstimated[-1])
    print "Phase = " + str(phaseOffsetEstimated[-1])
    print "Frequency Error = " + str(freqOffsetEstimated[-1] - freqOffset)
    print "Phase Error = " + str(phaseOffsetEstimated[-1] - phaseOffset) + "\n"

    # estimate frequency and phase offset
    synchronizer2 = CFS2(sampleRate, nbOfSamples, 260)
    idealUnwrappedPhase = np.unwrap(np.angle(myPacket.IQ))
    receivedUnwrappedPhase = np.unwrap(np.angle(preCorrectedSignal))
    phaseDifference = receivedUnwrappedPhase - idealUnwrappedPhase
    freqOffsetEstimated, phaseOffsetEstimated = synchronizer2.estimateFrequencyAndPhaseIterative(phaseDifference)
    correctionVector = synchronizer2.generatePhaseVector(freqOffsetEstimated, phaseOffsetEstimated)
    # correct received signal
    correctedSignal = synchronizer2.compensatePhase(correctionVector, preCorrectedSignal)


    plt.plot(phaseDifference[:1000])
    plt.show()

    ## PLOT
    print "CFS estimated frequency and phase offset"
    print "Frequency = " + str(freqOffsetEstimated[-1])
    print "Phase = " + str(phaseOffsetEstimated[-1])
    print "Frequency Error = " + str(freqOffsetEstimated[-1] - errF)
    print "Phase Error = " + str(phaseOffsetEstimated[-1] - errP) + "\n"
    # time vector
    maxTime = (1e-6 / sampleRate) * N
    timeStep = 1e-6 / sampleRate
    time = np.arange(0, maxTime, timeStep)

    # # phase estimation
    # totalPhase = (time * freqOffsetEstimated * 2 * np.pi + phaseOffsetEstimated * np.pi / 180) + phaseCPS
    # plt.plot(time[:100], totalPhase[:100])
    # plt.show()

    ###plt.plot(phaseCPS * 180 / np.pi)
    ###plt.show()

    # ideal received signal, no freq or phase offset
    myNoisyChannel = WirelessChannel(sampleRate, 0, 0, SNR)
    idealReceivedSignal = utils.butter_lowpass_filter(myNoisyChannel.receive(myPacket.IQ), cutoff, fs, order)
    idealReceivedSignal.imag = np.roll(idealReceivedSignal.imag, -4)

    correctedSignal.imag = np.roll(correctedSignal.imag, -4)

    # constellation plot: QPSK
    receivedConstellation, = plt.plot(correctedSignal.real[4::8], correctedSignal.imag[4::8], 'rx')
    idealConstellation, = plt.plot(idealReceivedSignal.real[4::8], idealReceivedSignal.imag[4::8], 'bo')
    plt.axvline(x=0)
    plt.axhline(y=0)
    plt.legend([idealConstellation, receivedConstellation], ['IDEAL CONSTELLATION', 'CORRECTED CONSTELLATION'], loc=3)
    receivedConstellation.set_linewidth(0.1)
    plt.ylim(-2, 2)
    plt.xlim(-2, 2)
    plt.title("O-QPSK CONSTELLATION - IDEAL VS CORRECTED")
    plt.show()
