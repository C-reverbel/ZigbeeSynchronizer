from ZigBeePacket import ZigBeePacket
from WirelessChannel import WirelessChannel
from CFS2 import CFS2
import utils
import numpy as np
import matplotlib.pyplot as plt

class CPS2:
    def __init__(self, sampleRate):
        self.sampleRate = sampleRate

    def rootMeanSquare(self, vector):
        temp = vector.copy()
        N = vector.__len__()
        f_acc = 0
        for k in range(N):
            Wk = self._computeWk(N / 8, k)
            f_acc += Wk * np.angle(temp[k])
        return (1e6 / (2 * np.pi)) * f_acc

    def _computeWk(self, L0, k):
        return 6 * (2 * k - 8 * L0 + 1) / (8 * L0 * (64 * L0 * L0 - 1))

class CPS:
    def __init__(self, sampleRate):
        self.sampleRate = sampleRate
        self.myPacket = ZigBeePacket(1, sampleRate)
        self.myPacket.Q = np.roll(self.myPacket.Q,0)

    def costasLoop(self, freq, vector):
        temp = vector.copy()
        C1, C2 = self._computeFilterParameters(freq, self.sampleRate)
        N = vector.__len__()

        phaseVect = np.zeros(N)
        phaseErrVector = np.zeros(N)

        phase = 0
        # loop filter variables
        last, last_old, deltaPhi_old = 0, 0, 0
        for i in range(N):
            # rotate point
            temp[i] = self.compensatePhase(phase, temp[i])
            # compute phase error
            signI = np.sign(temp.real[i])#myPacket.I[i]#np.sign(temp.real[i])
            signQ = np.sign(temp.imag[i])#myPacket.Q[i]#
            deltaPhi = temp.real[i] * signQ - temp.imag[i] * signI
            # loop filter
            last, last_old, deltaPhi_old = self._iterativeLowPassFilter(freq, last, last_old, deltaPhi, deltaPhi_old)

            phase += 0.01*last
            phaseVect[i] = phase
            phaseErrVector[i] = deltaPhi
        #temp = self.compensatePhase(phase * np.ones(N), temp)
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
    freqOffset = 300
    phaseOffset = 5
    SNR = 10
    # Butterworth low-pass filter
    cutoff = 1.5e6
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
    # receive signal and filter it (change filter order to ZERO to disable filtering)
    receivedSignal = np.roll(utils.butter_lowpass_filter(myChannel.receive(myPacket.IQ), cutoff, fs, order), 0)
    # Instantiate CPS
    # sample rate (MHz)
    synchronizer = CPS(sampleRate)
    correctedSignal, phaseVector, phaseErrVector = synchronizer.costasLoop(100000, receivedSignal)

    # define ideal noisy signal (no freq or phase offset)
    channel2 = WirelessChannel(sampleRate, 0, 0, SNR)
    idealRecSignal = np.roll(utils.butter_lowpass_filter(channel2.receive(myPacket.IQ), cutoff, fs, order), 0)

    ## PLOT
    plt.plot(phaseVector * 180 / np.pi)
    plt.grid(b=None, which='major', axis='both')
    plt.show()

    err_corrected = utils.calcAverageError(idealRecSignal, correctedSignal)
    err_received = utils.calcAverageError(idealRecSignal, receivedSignal)

    print err_received / err_received, err_corrected / err_received

    offset = 25000

    rec, = plt.plot(receivedSignal.real[offset:offset+100], 'g')
    rec.set_linewidth(0.5)
    plt.plot(correctedSignal.real[offset:offset+100], 'r')
    plt.plot(idealRecSignal.real[offset:offset+100], 'b--')
    plt.show()