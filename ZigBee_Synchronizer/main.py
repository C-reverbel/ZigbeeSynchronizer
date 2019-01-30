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
    nbOfSamples = 1024
    sampleRate = 8
    zigbeePayloadNbOfBytes = 127
    freqOffset = 500e3
    phaseOffset = 50
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
    print freqOffsetEstimated[-1], phaseOffsetEstimated[-1]

    # constellation plot: O-QPSK
    receivedConstellation, = plt.plot(preCorrectedSignal.real[6:N - 2:4], preCorrectedSignal.imag[6:N - 2:4], 'rx')
    idealConstellation, = plt.plot(myPacket.I[6:N - 2:4], myPacket.Q[6:N - 2:4], 'bo')
    plt.axvline(x=0)
    plt.axhline(y=0)
    plt.legend([idealConstellation, receivedConstellation], ['IDEAL CONSTELLATION', 'CORRECTED CONSTELLATION'], loc=3)
    receivedConstellation.set_linewidth(0.1)
    plt.ylim(-2, 2)
    plt.xlim(-2, 2)
    plt.title("O-QPSK CONSTELLATION - IDEAL VS CORRECTED")
    plt.show()

    plt.plot(freqOffsetEstimated[:1100])
    plt.ylim(100000, 800000)
    plt.show()



    nbOfSamplesToPlot = 8 * 128

    maxTime = (1e-6 / sampleRate) * N
    timeStep = 1e-6 / sampleRate
    timeUs = np.arange(0, maxTime, timeStep) * 1e6
    print idealUnwrappedPhase[4:128+4+1]

    preambleStart = idealUnwrappedPhase[4:128 + 4]
    fullPreamble = preambleStart
    for i in range(8):
        fullPreamble = np.append(fullPreamble, (i+1) * 6.283185307179587 * np.ones(128) + preambleStart)

    plt.plot(timeUs[4:nbOfSamplesToPlot+4], idealUnwrappedPhase[4:nbOfSamplesToPlot+4],'bo')
    plt.plot(timeUs[4:nbOfSamplesToPlot + 4], fullPreamble[:nbOfSamplesToPlot], 'rx')
    plt.grid(b=None, which='major', axis='both')
    plt.title("TRANSMITTED PHASE")
    plt.ylabel("phase (rad)")
    plt.xlabel("time (us)")
    plt.xticks(np.arange(0, nbOfSamplesToPlot / sampleRate + 0.5, 0.5))
    plt.yticks(np.arange(-2 * np.pi, max(idealUnwrappedPhase[:nbOfSamplesToPlot]) + np.pi / 2, np.pi / 2))
    #plt.xlim(0, nbOfSamplesToPlot / sampleRate)
    plt.show()

    phaseError = fullPreamble[:nbOfSamplesToPlot] - idealUnwrappedPhase[4:nbOfSamplesToPlot+4]
    plt.plot(phaseError)
    plt.show()
