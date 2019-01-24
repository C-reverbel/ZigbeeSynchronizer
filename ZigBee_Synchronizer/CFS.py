from ZigBeePacket import ZigBeePacket
from WirelessChannel import WirelessChannel
import numpy as np
import matplotlib.pyplot as plt

class CFS:
    def __init__(self, sampleRate, nbOfSamples):
        self.sampleRate = sampleRate
        self.nbOfSamples = nbOfSamples

    def estimateFrequency(self, phaseDifference):
        maxTime    = (1e-6 / self.sampleRate) * self.nbOfSamples
        timeStep   = 1e-6 / self.sampleRate
        time = np.arange(0, maxTime, timeStep)

        fit = np.polyfit(time[2:], phaseDifference[2:self.nbOfSamples], 1)
        # return estimated frequency in Hz
        return fit[0] / (2 * np.pi)

    def estimatePhase(self, phaseDifference):
        maxTime    = (1e-6 / self.sampleRate) * self.nbOfSamples
        timeStep   = 1e-6 / self.sampleRate
        time = np.arange(0, maxTime, timeStep)

        fit = np.polyfit(time[2:], phaseDifference[2:self.nbOfSamples], 1)
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
    # 2 bytes payload, 8 MHz sample-rate
    myPacket = ZigBeePacket(2, sampleRate)
    # sample rate (MHz), frequency offset (Hz), phase offset (degrees), SNR (db)
    myChannel = WirelessChannel(8, 130e3, 100, 0)
    receivedMessage = myChannel.receive(myPacket.IQ)
    # ideal and received phases
    idealUnwrappedPhase = np.unwrap(np.angle(myPacket.IQ))
    receivedUnwrappedPhase = np.unwrap(np.angle(receivedMessage))
    phaseDifference = receivedUnwrappedPhase - idealUnwrappedPhase
    # sample rate (MHz), number of samples - 2 to compute linear regression
    freqEstimator = CFS(sampleRate, nbOfSamples)
    freqOffset = freqEstimator.estimateFrequency(phaseDifference)
    phaseOffset = freqEstimator.estimatePhase(phaseDifference)
    print "Estimated frequency offset = " + str(freqOffset) + " Hz"
    print "Estimated phase offset = " + str(phaseOffset) + " Degrees"
    correctedMessage = freqEstimator.compensateFrequencyAndPhase(freqOffset, phaseOffset, receivedMessage)

    correctedUnwrappedPhase = np.unwrap(np.angle(correctedMessage))

    ## PLOT
    nbOfSamplesToPlot = 128
    maxTime = (1e-6 / sampleRate) * nbOfSamplesToPlot
    timeStep = 1e-6 / sampleRate
    timeUs = np.arange(0, maxTime, timeStep) * 1e6
    # wrapped and unwrapped ideal phase
    wrapped, = plt.plot(timeUs, np.angle(myPacket.IQ[:nbOfSamplesToPlot]), '-b')
    unwrapped, = plt.plot(timeUs, idealUnwrappedPhase[:nbOfSamplesToPlot], '-r')
    plt.legend([wrapped, unwrapped], ['WRAPPED PHASE', 'UNWRAPPED PHASE'], loc=2)
    plt.title("TRANSMITTED PHASE")
    plt.ylabel("phase (rad)")
    plt.xlabel("time (us)")
    plt.show()
    # transmitted vs received unwrapped phase
    unwrappedTransmitted, = plt.plot(timeUs, idealUnwrappedPhase[:nbOfSamplesToPlot], '-b')
    unwrappedReceived, = plt.plot(timeUs, receivedUnwrappedPhase[:nbOfSamplesToPlot], '-r')
    plt.legend([unwrappedTransmitted, unwrappedReceived], ['IDEAL PHASE', 'RECEIVED PHASE'], loc=2)
    plt.title("IQ PHASE - TRANSMITTED VS RECEIVED")
    plt.ylabel("phase (rad)")
    plt.xlabel("time (us)")
    plt.show()
    # phase difference
    plt.plot(timeUs, phaseDifference[:nbOfSamplesToPlot], '-k')
    plt.title("TRANSMITTED AND RECEIVED PHASE DIFFERENCE")
    plt.ylabel("phase difference (rad)")
    plt.xlabel("time (us)")
    plt.show()
    # transmitted vs corrected unwrapped phase
    unwrappedTransmitted, = plt.plot(timeUs, idealUnwrappedPhase[:nbOfSamplesToPlot], '-b')
    unwrappedReceived, = plt.plot(timeUs, receivedUnwrappedPhase[:nbOfSamplesToPlot], '-r')
    unwrappedCorrected, = plt.plot(timeUs, correctedUnwrappedPhase[:nbOfSamplesToPlot], 'kx')
    unwrappedCorrected.set_linewidth(0.5)
    plt.legend([unwrappedTransmitted, unwrappedReceived, unwrappedCorrected], ['IDEAL PHASE', 'RECEIVED PHASE', 'CORRECTED PHASE'], loc=2)
    plt.title("IQ PHASE - TRANSMITTED VS RECEIVED VS CORRECTED")
    plt.ylabel("phase (rad)")
    plt.xlabel("time (us)")
    plt.show()

    inphaseTx, = plt.plot(timeUs, myPacket.I[:nbOfSamplesToPlot], '-b')
    inphaseRx, = plt.plot(timeUs, receivedMessage.real[:nbOfSamplesToPlot], '-r')
    inphaseCorrected, = plt.plot(timeUs, correctedMessage.real[:nbOfSamplesToPlot], 'kx')
    inphaseTx.set_linewidth(3)
    inphaseRx.set_linewidth(1)
    inphaseCorrected.set_linewidth(0.5)
    plt.legend([inphaseTx, inphaseRx, inphaseCorrected], ['TRANSMITTED', 'RECEIVED', 'CORRECTED'], loc=4)
    plt.title("TRANSMITTED, RECEIVED AND CORRECTED IN-PHASE")
    plt.ylabel("voltage")
    plt.xlabel("time (us)")
    plt.show()
