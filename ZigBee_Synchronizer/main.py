#                   _________                         _____                             _____
#                  |         |                       |     |                           |     |
#  myPacket.IQ --> | CHANNEL | -- receivedSignal --> | CFS | -- preCorrectedSignal --> | CPS | --> correctedSignal
#                  |_________|                       |_____|                           |_____|
#
from ZigBeePacket import ZigBeePacket
from WirelessChannel import WirelessChannel
from CFS import CFS
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
    SNR = 15

    cutoff = 2.5e6
    fs = sampleRate * 1e6
    order = 4

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
    receivedSignal = np.roll(utils.butter_lowpass_filter(myChannel.receive(myPacket.IQ), cutoff, fs, order),0)
    # sample rate (MHz), number of samples - 2 to compute linear regression
    synchronizer = CFS(sampleRate, nbOfSamples)
    # estimate frequency and phase offset
    idealUnwrappedPhase = np.unwrap(np.angle(myPacket.IQ))
    receivedUnwrappedPhase = np.unwrap(np.angle(receivedSignal))
    phaseDifference = receivedUnwrappedPhase - idealUnwrappedPhase
    freqOffsetEstimated, phaseOffsetEstimated = synchronizer.estimateFrequencyAndPhase(phaseDifference)
    preCorrectedSignal = synchronizer.compensateFrequencyAndPhase(freqOffsetEstimated, phaseOffsetEstimated, receivedSignal)
    idealCorrectedSignal = synchronizer.compensateFrequencyAndPhase(freqOffset, phaseOffset, receivedSignal)

    print "DIRECT METHOD ESTIMATION"
    print "Estimated frequency offset = " + str(freqOffsetEstimated / 1000) + " kHz"
    print "Estimated phase offset = " + str(phaseOffsetEstimated) + " Degrees"
    print "Frequency estimation error = " + str((freqOffset - freqOffsetEstimated)) + " Hz"
    print "Phase estimation error = " + str((phaseOffset - phaseOffsetEstimated)) + " Degrees\n"

    freqOffsetVector, phaseOffsetVector, corrVector = synchronizer.estimateFrequencyAndPhaseIterative(phaseDifference)

    correctedSignal = synchronizer.compensatePhase(corrVector, receivedSignal)

    print "ITERATIVE METHOD ESTIMATION"
    print "Estimated frequency offset = " + str(freqOffsetVector[-1] / 1000) + " kHz"
    print "Estimated phase offset = " + str(phaseOffsetVector[-1]) + " Degrees"
    print "Frequency estimation error = " + str((freqOffset - freqOffsetVector[-1])) + " Hz"
    print "Phase estimation error = " + str((phaseOffset - phaseOffsetVector[-1])) + " Degrees\n"

    plot1, = plt.plot(myPacket.I[-50:-1],'--bo')
    plot2, = plt.plot(correctedSignal.real[-50:-1],'--ro')
    plt.show()

    plt.plot(idealCorrectedSignal.real[6:N-10:4], idealCorrectedSignal.imag[6:N-10:4], 'bx')
    plt.plot(correctedSignal.real[6:N - 10:4], correctedSignal.imag[6:N - 10:4], 'rx')
    plt.show()
    ## transmitted vs received unwrapped phase
    #unwrappedTransmitted, = plt.plot(time[:nbOfSamples], idealUnwrappedPhase[:nbOfSamples], '-b')
    #unwrappedReceived, = plt.plot(time[:nbOfSamples], receivedUnwrappedPhase[:nbOfSamples], '-r')
    #plt.legend([unwrappedTransmitted, unwrappedReceived], ['IDEAL PHASE', 'RECEIVED PHASE'], loc=2)
    #plt.title("IQ PHASE - TRANSMITTED VS RECEIVED")
    #plt.ylabel("phase (rad)")
    #plt.xlabel("time (us)")
    #plt.show()
    #
    #plt.plot(a[:200] / (2 * np.pi),'r')
    #plt.show()
    #plt.plot(b[:200] * 180 / np.pi,'r')
    #plt.show()
    #
    #reconstructed = time * a[-1] + b[-1]
    #plot2, = plt.plot(time[:], phaseDifference[:nbOfSamples], 'b')
    #plot1, = plt.plot(time[:], reconstructed[:], 'r')
    #plot1.set_linewidth(1)
    #plot2.set_linewidth(4)
    #plt.show()
    #print a[-1] / (2 * np.pi), b[-1] * 180 / np.pi
    #
    #maxTime2 = (1e-6 / sampleRate) * N
    #time2 = np.arange(0, maxTime2, timeStep)
    #correctedPhase = a * time2 + b
    #
    #correctedSignal = synchronizer.compensatePhase(correctedPhase, receivedSignal)
    #
    #plt.plot(myPacket.Q[500:600],'-bo')
    #plt.plot(correctedSignal.imag[500:600],'-rx')
    #plt.show()
    #
    #print utils.calcAverageError(correctedSignal, idealCorrectedSignal)
    #print utils.calcAverageError(preCorrectedSignal, idealCorrectedSignal)
    #
    ## extract signal phase
    #corrSignalPhase = utils.extractPhase(correctedSignal)
    #plt.plot(corrSignalPhase.real, corrSignalPhase.imag, 'rx')
    #plt.show()