from ZigBeePacket import ZigBeePacket
from WirelessChannel import WirelessChannel
from CFS2 import CFS2
import utils
import numpy as np
import matplotlib.pyplot as plt

class CPS:
    def __init__(self, sampleRate):
        self.sampleRate = sampleRate

    def costasLoop(self, freq, vector):
        temp = vector.copy()
        C1, C2 = self._computeFilterParameters(freq, self.sampleRate)
        N = vector.__len__()

        phaseVect = np.zeros(N)
        phaseErrVector = np.zeros(N)

        phase = 0
        # loop filter variables
        last, last_old, deltaPhi_old = 0, 0, 0
        # in-phase filter variables
        y_i, y_i_old, x_i_old = 0, 0, 0
        # quadrature filter variables
        y_q, y_q_old, x_q_old = 0, 0, 0
        for i in range(N):
            # rotate point
            temp[i] = self.compensatePhase(phase, temp[i])
            # compute phase error
            signI = np.sign(temp.real[i])
            signQ = np.sign(temp.imag[i])
            deltaPhi = -temp.imag[i] * signI + temp.real[i] * signQ
            # loop filter
            last, last_old, deltaPhi_old = self._iterativeLowPassFilter(freq, last, last_old, deltaPhi, deltaPhi_old)

            phase = last
            phaseVect[i] = phase
            phaseErrVector[i] = deltaPhi
        return temp, phaseVect, phaseErrVector

    def _iterativeLowPassFilter(self, cutoffFrequency, y, y_old, x, x_old):
        C1, C2 = self._computeFilterParameters(cutoffFrequency, self.sampleRate)
        y = (C1 * y_old + C2 * (x + x_old))
        x_old = x
        y_old = y
        return y, y_old, x_old


    def _computeFilterParameters(self, freq, sampleRate):
        Wc = 2 * np.pi * freq
        Ts = 1e-6 / sampleRate

        C1 = (2 - Wc * Ts) / (2 + Wc * Ts)
        C2 = (Wc * Ts) / (2 + Wc * Ts)

        return C1, C2

    def compensatePhase(self, phase, signal):
        return np.exp(-1j * phase) * signal

if __name__ == "__main__":
    # Zigbee packet
    nbOfSamples = 1024
    sampleRate = 8
    zigbeePayloadNbOfBytes = 127
    freqOffset = 0
    phaseOffset = 5
    SNR = 1000
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

    # sample-rate (MHz), frequency offset (Hz), phase offset (degrees), SNR (db)
    myChannel = WirelessChannel(sampleRate, freqOffset, phaseOffset, SNR)
    # receive signal and filter it (change filter order to ZERO to disable filtering)
    receivedSignal = np.roll(utils.butter_lowpass_filter(myChannel.receive(myPacket.IQ), cutoff, fs, order), 0)
    # convert to QPSK


    receivedSignal.imag = np.roll(receivedSignal.imag,0)
    # sample rate (MHz)
    synchronizer = CPS(8)
    correctedSignal, phaseVector, phaseErrVector = synchronizer.costasLoop(800, receivedSignal)

    plt.plot(phaseVector * 180 / np.pi)
    plt.grid(b=None, which='major', axis='both')
    plt.show()

    #plt.plot(phaseErrVector * 180 / np.pi)
    #plt.grid(b=None, which='major', axis='both')
    #plt.show()



    plt.plot(receivedSignal.real[25000:25100], 'g')
    plt.plot(correctedSignal.real[25000:25100], 'r')
    plt.plot(myPacket.I[25000:25100], 'b--')
    plt.show()