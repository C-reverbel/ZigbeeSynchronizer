#                   _________                         _____                             _____
#                  |         |                       |     |                           |     |
#  myPacket.IQ --> | CHANNEL | -- receivedSignal --> | CFS | -- preCorrectedSignal --> | CPS | --> correctedSignal
#                  |_________|                       |_____|                           |_____|
#
from ZigBeePacket import ZigBeePacket
from WirelessChannel import WirelessChannel
from CFS2 import CFS2
from CFS import CFS
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
    phaseOffset = 200
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
    correctedSignal, phaseVector = synchronizer2.costasLoop(5000, preCorrectedSignal)




    ################################################### PLOT
    # time vector
    maxTime = (1e-6 / sampleRate) * N
    timeStep = 1e-6 / sampleRate
    time = np.arange(0, maxTime, timeStep)

    # ideal received signal, no freq or phase offset
    sync = CFS(sampleRate, nbOfSamples)
    idealReceivedSignal = sync.compensateFrequencyAndPhase(freqOffset, phaseOffset, myChannel.receive(myPacket.IQ))

    # plot phase differences
    phaseDifference = np.unwrap(np.angle(preCorrectedSignal)) - np.unwrap(np.angle(myPacket.IQ))
    phaseNoiseCFS, = plt.plot(1e3*time, phaseDifference, 'orange')
    phaseDifference = utils.butter_lowpass_filter(phaseDifference, 5000, sampleRate*1e6, 2)
    phaseCFS, = plt.plot(1e3 * time, phaseDifference, 'r--')
    plt.yticks(np.arange(min(phaseDifference)-2 * np.pi, max(phaseDifference) + np.pi / 2, np.pi / 2))
    phaseDifference = np.unwrap(np.angle(correctedSignal)) - np.unwrap(np.angle(myPacket.IQ))
    phaseNoiseCPS, = plt.plot(1e3 * time, phaseDifference, 'b')
    phaseDifference = utils.butter_lowpass_filter(phaseDifference, 5000, sampleRate*1e6, 2)
    phaseCPS, = plt.plot(1e3 * time, phaseDifference, 'c--')
    phaseNoiseCFS.set_linewidth(0.1)
    phaseNoiseCPS.set_linewidth(0.1)
    phaseCFS.set_linewidth(4)
    phaseCPS.set_linewidth(4)
    plt.legend([phaseCFS, phaseCPS], ['POST-CFS', 'POST-CPS'],loc=3)
    plt.title("PHASE ERROR VS TIME - SNR: " + str(SNR) + ", CFS SAMPLES: " + str(nbOfSamples))
    plt.ylabel("PHASE (rad)")
    plt.xlabel("TIME (ms)")
    plt.grid(b=None, which='major', axis='both')
    plt.show()

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
    # time domain plot
    offset = 30000
    numberPoints = 50
    samples = range(offset, offset + numberPoints)
    recTime, = plt.plot(samples, receivedSignal.real[offset:offset + numberPoints], 'g')
    preCorrTime, = plt.plot(samples, preCorrectedSignal.real[offset:offset + numberPoints], 'k')
    corrTime, = plt.plot(samples, correctedSignal.real[offset:offset + numberPoints], 'r')
    idealTime, = plt.plot(samples, idealReceivedSignal.real[offset:offset + numberPoints], 'b--')
    idealTimeNoNoise, = plt.plot(samples, myPacket.IQ.real[offset:offset + numberPoints], 'c--')
    recTime.set_linewidth(0.5)
    preCorrTime.set_linewidth(0.5)
    plt.legend([recTime, preCorrTime, corrTime, idealTime, idealTimeNoNoise], \
               ['PRE-CFS', 'POST-CFS', 'POST-CPS', 'IDEAL', 'IDEAL - NO NOISE'], loc=3)
    plt.title("TIME DOMAIN IN-PHASE SIGNAL - SNR: " + str(SNR) + ", CFS SAMPLES: " + str(nbOfSamples))
    plt.ylabel("Amplitude (Volts)")
    plt.xlabel("samples")
    plt.axhline(y=0, color='k')
    plt.show()
