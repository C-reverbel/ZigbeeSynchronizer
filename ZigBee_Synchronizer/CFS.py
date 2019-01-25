from ZigBeePacket import ZigBeePacket
from WirelessChannel import WirelessChannel
import numpy as np
import matplotlib.pyplot as plt

class CFS:
    def __init__(self, sampleRate, nbOfSamples):
        self.sampleRate = sampleRate
        self.nbOfSamples = nbOfSamples
        self.samplesOffset = 5

    def estimateFrequency(self, phaseDifference):
        maxTime    = (1e-6 / self.sampleRate) * self.nbOfSamples
        timeStep   = 1e-6 / self.sampleRate
        time = np.arange(0, maxTime, timeStep)

        fit = np.polyfit(time[self.samplesOffset:self.nbOfSamples], phaseDifference[self.samplesOffset:self.nbOfSamples], 1)
        # return estimated frequency in Hz
        return fit[0] / (2 * np.pi)

    def estimatePhase(self, phaseDifference):
        maxTime    = (1e-6 / self.sampleRate) * self.nbOfSamples
        timeStep   = 1e-6 / self.sampleRate
        time = np.arange(0, maxTime, timeStep)

        fit = np.polyfit(time[self.samplesOffset:self.nbOfSamples], phaseDifference[self.samplesOffset:self.nbOfSamples], 1)
        # return estimated phase in degrees
        return fit[1] * 180 / np.pi

    # freq in Hz, phase in degree, signal in complex form (I + jQ)
    def compensateFrequencyAndPhase(self, freq, phase, signal):
        n = np.arange(signal.__len__())
        cos = np.cos(2 * np.pi * 1e-6 * freq * n / self.sampleRate + np.pi * phase / 180)
        sin = np.sin(2 * np.pi * 1e-6 * freq * n / self.sampleRate + np.pi * phase / 180)
        resultReal = signal.real * cos + signal.imag * sin
        resultImag = - signal.real * sin + signal.imag * cos
        result = resultReal + 1j * resultImag
        return result


if __name__ == "__main__":
    nbOfSamples = 128
    sampleRate = 8
    freqOffset = 200e3
    phaseOffset = 10
    SNR = 10

    # 2 bytes payload, 8 MHz sample-rate
    myPacket = ZigBeePacket(127, sampleRate)
    # sample rate (MHz), frequency offset (Hz), phase offset (degrees), SNR (db)
    myChannel = WirelessChannel(sampleRate, freqOffset, phaseOffset, SNR)
    receivedMessage = myChannel.receive(myPacket.IQ)

    # ideal and received phases
    idealUnwrappedPhase = np.unwrap(np.angle(myPacket.IQ))
    receivedUnwrappedPhase = np.unwrap(np.angle(receivedMessage))
    phaseDifference = receivedUnwrappedPhase - idealUnwrappedPhase

    # sample rate (MHz), number of samples - 2 to compute linear regression
    freqEstimator = CFS(sampleRate, nbOfSamples)
    freqOffsetEstimated = freqEstimator.estimateFrequency(phaseDifference)
    phaseOffsetEstimated = freqEstimator.estimatePhase(phaseDifference)

    # correct received signal with estimated frequency and phase offset
    correctedMessage = freqEstimator.compensateFrequencyAndPhase(freqOffsetEstimated, phaseOffsetEstimated, receivedMessage)

    idealUnwrappedPhase = np.unwrap(np.angle(myPacket.IQ))
    correctedUnwrappedPhase = np.unwrap(np.angle(correctedMessage))
    phaseDifferenceCorrected = correctedUnwrappedPhase - idealUnwrappedPhase

    print "Zigbee packet number of samples = " + str(myPacket.IQ.__len__())
    print "Sample rate = " + str(sampleRate) + " MHz"
    print "Frequency offset = " + str(freqOffset / 1000) + " kHz"
    print "Phase offset = " + str(phaseOffset) + " Degrees"
    print "SNR = " + str(SNR) + " dB"

    print "Estimated frequency offset = " + str(freqOffsetEstimated / 1000) + " kHz"
    print "Estimated phase offset = " + str(phaseOffsetEstimated) + " Degrees"


    ## PLOT
    correctedUnwrappedPhase = np.unwrap(np.angle(correctedMessage))
    nbOfSamplesToPlot = 20000
    maxTime = (1e-6 / sampleRate) * (nbOfSamplesToPlot)
    timeStep = 1e-6 / sampleRate
    timeUs = np.arange(0, maxTime, timeStep) * 1e6

    print timeUs.__len__()
    print myPacket.IQ[:nbOfSamplesToPlot].__len__()
    # wrapped and unwrapped ideal phase
    wrapped, = plt.plot(timeUs[:nbOfSamplesToPlot], np.angle(myPacket.IQ[:nbOfSamplesToPlot]), '-b')
    unwrapped, = plt.plot(timeUs[:nbOfSamplesToPlot], idealUnwrappedPhase[:nbOfSamplesToPlot], '-r')
    plt.legend([wrapped, unwrapped], ['WRAPPED PHASE', 'UNWRAPPED PHASE'], loc=2)
    plt.title("TRANSMITTED PHASE")
    plt.ylabel("phase (rad)")
    plt.xlabel("time (us)")
    plt.show()
    # transmitted vs received unwrapped phase
    unwrappedTransmitted, = plt.plot(timeUs[:nbOfSamplesToPlot], idealUnwrappedPhase[:nbOfSamplesToPlot], '-b')
    unwrappedReceived, = plt.plot(timeUs[:nbOfSamplesToPlot], receivedUnwrappedPhase[:nbOfSamplesToPlot], '-r')
    plt.legend([unwrappedTransmitted, unwrappedReceived], ['IDEAL PHASE', 'RECEIVED PHASE'], loc=2)
    plt.title("IQ PHASE - TRANSMITTED VS RECEIVED")
    plt.ylabel("phase (rad)")
    plt.xlabel("time (us)")
    plt.show()
    # phase difference
    plt.plot(timeUs[:nbOfSamplesToPlot], phaseDifference[:nbOfSamplesToPlot], '-k')
    plt.title("TRANSMITTED AND RECEIVED PHASE DIFFERENCE")
    plt.ylabel("phase difference (rad)")
    plt.xlabel("time (us)")
    plt.show()
    # transmitted vs corrected unwrapped phase
    unwrappedTransmitted, = plt.plot(timeUs[:nbOfSamplesToPlot], idealUnwrappedPhase[:nbOfSamplesToPlot], '-b')
    unwrappedReceived, = plt.plot(timeUs[:nbOfSamplesToPlot], receivedUnwrappedPhase[:nbOfSamplesToPlot], '-r')
    unwrappedCorrected, = plt.plot(timeUs[:nbOfSamplesToPlot], correctedUnwrappedPhase[:nbOfSamplesToPlot], 'kx')
    unwrappedCorrected.set_linewidth(0.5)
    plt.legend([unwrappedTransmitted, unwrappedReceived, unwrappedCorrected], ['IDEAL PHASE', 'RECEIVED PHASE', 'CORRECTED PHASE'], loc=2)
    plt.title("IQ PHASE - TRANSMITTED VS RECEIVED VS CORRECTED")
    plt.ylabel("phase (rad)")
    plt.xlabel("time (us)")
    plt.show()
    # phase difference
    plt.plot(timeUs[:nbOfSamplesToPlot], phaseDifferenceCorrected[:nbOfSamplesToPlot], '-k')
    plt.title("TRANSMITTED AND CORRECTED PHASE DIFFERENCE")
    plt.ylabel("phase difference (rad)")
    plt.xlabel("time (us)")
    plt.show()
    # Constellation
    transmitted, = plt.plot(myPacket.IQ.real, myPacket.IQ.imag, '-bo')
    transmitted.set_linewidth(4)
    received, = plt.plot(correctedMessage.real, correctedMessage.imag, '-rx')
    received.set_linewidth(0.5)
    plt.title("O-QPSK CONSTELLATION DIAGRAM")
    plt.legend([transmitted, received], ['IDEAL', 'DISTORTED'], loc=3)
    plt.show()