from ZigBeePacket import ZigBeePacket
from WirelessChannel import WirelessChannel
import numpy as np
import matplotlib.pyplot as plt

class CFS2:
    def __init__(self, sampleRate, nbOfSamples):
        self.sampleRate = sampleRate
        self.nbOfSamples = nbOfSamples
        self.estimatorBufferSize = 1
        self.samplesOffset = 4

    def estimateFrequencyAndPhaseIterative(self, phaseDifference):
        N = phaseDifference.__len__()
        maxTime = (1e-6 / self.sampleRate) * N
        timeStep = 1e-6 / self.sampleRate
        time = np.arange(0, maxTime, timeStep)
        # estimate parameters recursively
        sumX = 0
        sumY = 0
        sumXY = 0
        sumXX = 0
        freq = np.zeros(N)
        phase = np.zeros(N)
        for i in range(self.samplesOffset, self.nbOfSamples + self.samplesOffset):
            n = i - self.samplesOffset + 1
            sumX += time[i]
            sumY += phaseDifference[i]
            sumXY += time[i] * phaseDifference[i]
            sumXX += time[i] * time[i]
            if i >= self.estimatorBufferSize:
                freq[i] = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX)
                phase[i] = (sumY - freq[i] * sumX) / (n)
        # correct received signal
        for i in range(self.estimatorBufferSize):
            freq[i] = freq[self.estimatorBufferSize]
            phase[i] = phase[self.estimatorBufferSize]
        for i in range(self.nbOfSamples, N):
            freq[i] = freq[self.nbOfSamples - 1]
            phase[i] = phase[self.nbOfSamples - 1]
        # format frequency and phase
        for i in range(N):
            freq[i] = freq[i] / (2 * np.pi)
            phase[i] = phase[i] * 180 / np.pi
        # freuency in Hz, phase in degrees
        return freq, phase
    # generate vector to be applied on compensatePhase()
    def generatePhaseVector(self, freqVect, phaseVect):
        N = freqVect.__len__()
        freq = np.zeros(N)
        phase = np.zeros(N)
        for i in range(N):
            freq[i] = freqVect[i] * (2 * np.pi)
            phase[i] = phaseVect[i] / (180 / np.pi)
        maxTime = (1e-6 / self.sampleRate) * N
        timeStep = 1e-6 / self.sampleRate
        time = np.arange(0, maxTime, timeStep)
        return time * freq + phase
    # applies a rotation to each point of 'signal' by corresponding point in 'phase' vector
    def compensatePhase(self, phase, signal):
        cos = np.cos(phase)
        sin = np.sin(phase)
        resultReal = signal.real * cos + signal.imag * sin
        resultImag = - signal.real * sin + signal.imag * cos
        result = resultReal + 1j * resultImag
        return result

if __name__ == "__main__":
    # preamble lasts 1024 samples
    nbOfSamples = 1024
    sampleRate = 8
    freqOffset = 500e3
    phaseOffset = 15
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
    synchronizer = CFS2(sampleRate, nbOfSamples)
    freqOffsetVector, phaseOffsetVector = synchronizer.estimateFrequencyAndPhaseIterative(phaseDifference)
    corrVector = synchronizer.generatePhaseVector(freqOffsetVector, phaseOffsetVector)
    # PHASE AND FREQUENCY CORRECTION
    correctedMessage = synchronizer.compensatePhase(corrVector, receivedMessage)
    correctedUnwrappedPhase = np.unwrap(np.angle(correctedMessage))
    phaseDifferenceCorrected = correctedUnwrappedPhase - idealUnwrappedPhase


    print "Zigbee packet number of samples = " + str(myPacket.IQ.__len__())
    print "Sample rate = " + str(sampleRate) + " MHz"
    print "Frequency offset = " + str(freqOffset / 1000) + " kHz"
    print "Phase offset = " + str(phaseOffset) + " Degrees"
    print "SNR = " + str(SNR) + " dB"

    print "Estimated frequency offset = " + str(freqOffsetVector[-1] / 1000) + " kHz"
    print "Estimated phase offset = " + str(phaseOffsetVector[-1]) + " Degrees"
    print "Frequency estimation error = " + str((freqOffset - freqOffsetVector[-1])) + " Hz"
    print "Phase estimation error = " + str((phaseOffset - phaseOffsetVector[-1])) + " Degrees"


    ## PLOT
    N = myPacket.I.__len__()
    nbOfSamplesToPlot = nbOfSamples

    maxTime = (1e-6 / sampleRate) * N
    timeStep = 1e-6 / sampleRate
    timeUs = np.arange(0, maxTime, timeStep) * 1e6

    # wrapped and unwrapped ideal phase
    wrapped, = plt.plot(timeUs[:nbOfSamplesToPlot], np.angle(myPacket.IQ[:nbOfSamplesToPlot]), '-b')
    unwrapped, = plt.plot(timeUs[:nbOfSamplesToPlot], idealUnwrappedPhase[:nbOfSamplesToPlot], '-r')
    plt.legend([wrapped, unwrapped], ['WRAPPED PHASE', 'UNWRAPPED PHASE'], loc=2)
    plt.grid(b=None, which='major', axis='both')
    plt.title("TRANSMITTED PHASE")
    plt.ylabel("phase (rad)")
    plt.xlabel("time (us)")
    plt.xticks(np.arange(0,nbOfSamplesToPlot / sampleRate + 0.5,0.5))
    plt.yticks(np.arange(-2 * np.pi, max(idealUnwrappedPhase[:nbOfSamplesToPlot]) + np.pi / 2, np.pi / 2))
    plt.xlim(0,nbOfSamplesToPlot / sampleRate)
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
    plt.plot(timeUs[:nbOfSamplesToPlot], phaseDifference[:nbOfSamplesToPlot], '-ko')
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

    nbOfSamplesToPlot = N

    # phase difference
    plt.plot(timeUs[:nbOfSamplesToPlot], 180 * phaseDifferenceCorrected[:nbOfSamplesToPlot] / np.pi, '-k')
    plt.grid(b=None, which='major', axis='y')
    plt.title("TRANSMITTED AND CORRECTED PHASE DIFFERENCE")
    plt.ylabel("phase difference (degree)")
    plt.xlabel("time (us)")
    plt.show()

    # constellation plot: QPSK
    receivedConstellation, = plt.plot(correctedMessage.real[4::8], np.roll(correctedMessage.imag,-4)[4::8], 'rx')
    idealConstellation, = plt.plot(myPacket.I[4::8], np.roll(myPacket.Q,-4)[4::8], 'bo')
    plt.axvline(x=0)
    plt.axhline(y=0)
    plt.legend([idealConstellation, receivedConstellation], ['IDEAL CONSTELLATION', 'CORRECTED CONSTELLATION'], loc=3)
    receivedConstellation.set_linewidth(0.1)
    plt.ylim(-2, 2)
    plt.xlim(-2, 2)
    plt.title("QPSK CONSTELLATION - IDEAL VS CORRECTED")
    plt.show()

    # constellation plot: O-QPSK
    receivedConstellation, = plt.plot(correctedMessage.real[6:N-2:4], correctedMessage.imag[6:N-2:4], 'rx')
    idealConstellation, = plt.plot(myPacket.I[6:N-2:4], myPacket.Q[6:N-2:4], 'bo')
    plt.axvline(x=0)
    plt.axhline(y=0)
    plt.legend([idealConstellation, receivedConstellation], ['IDEAL CONSTELLATION', 'CORRECTED CONSTELLATION'], loc=3)
    receivedConstellation.set_linewidth(0.1)
    plt.ylim(-2, 2)
    plt.xlim(-2, 2)
    plt.title("O-QPSK CONSTELLATION - IDEAL VS CORRECTED")
    plt.show()


