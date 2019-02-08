from ZigBeePacket import ZigBeePacket
from WirelessChannel import WirelessChannel
from CFS2 import CFS2
import utils
import numpy as np
import matplotlib.pyplot as plt

class CPS:
    def __init__(self, sampleRate):
        self.sampleRate = sampleRate
        self.myPacket = ZigBeePacket(1, sampleRate)

    def costasLoop(self, freq, vector):
        temp = vector.copy()
        C1, C2 = self._computeFilterParameters(freq, self.sampleRate)
        N = vector.__len__()
        phaseVect = np.zeros(N)
        phase = 0

        # loop filter variables
        last, last_old, deltaPhi_old = 0, 0, 0
        # I and Q filter variables
        y_i, y_i_old, x_i_old = 0, 0, 0
        y_q, y_q_old, x_q_old = 0, 0, 0
        for i in range(4,N):
            # rotate signal
            temp[i] = self.compensatePhase(phase, temp[i])
            y_i = temp.real[i]
            y_q = temp.imag[i-4]
            # compute phase error
            signI = np.sign(temp.real[i])
            signQ = np.sign(temp.imag[i-4])
            deltaPhi = y_q * signI - y_i * signQ
            # loop filter
            last, last_old, deltaPhi_old = self._iterativeLowPassFilter(freq, last, last_old, deltaPhi, deltaPhi_old)
            # constant value empirically tested :p
            phase += 0.005 * last
            phaseVect[i] = phase # return phase for test only
        return temp, phaseVect

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
    sampleRate = 8
    zigbeePayloadNbOfBytes = 127
    freqOffset = 450. # max 450 @ SNR = 10
    phaseOffset = 25  # max 25  @ SNR = 10
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

    # sample-rate (MHz), frequency offset (Hz), phase offset (degrees), SNR (db)
    myChannel = WirelessChannel(sampleRate, freqOffset, phaseOffset, SNR)
    # receive signal and filter it (change filter order to ZERO to disable filtering)
    receivedSignal = np.roll(utils.butter_lowpass_filter(myChannel.receive(myPacket.IQ), cutoff, fs, order), 0)

    # Instantiate CPS
    # sample rate (MHz)
    synchronizer = CPS(sampleRate)
    correctedSignal, phaseVector = synchronizer.costasLoop(100000, receivedSignal)

    # define ideal noisy signal (no freq or phase offset)
    channel2 = WirelessChannel(sampleRate, 0, 0, SNR)
    idealRecSignal = np.roll(utils.butter_lowpass_filter(channel2.receive(myPacket.IQ), cutoff, fs, order), 0)

    ## PLOT
    correctedSignal.imag = np.roll(correctedSignal.imag, -4)
    idealRecSignal.imag = np.roll(idealRecSignal.imag, -4)

    plt.plot(phaseVector * 180 / np.pi)
    plt.grid(b=None, which='major', axis='both')
    plt.show()

    err_corrected = utils.calcAverageError(idealRecSignal, correctedSignal)
    err_received = utils.calcAverageError(idealRecSignal, receivedSignal)

    print "received signal | corrected signal: ", err_received / err_received, " | ", err_corrected / err_received

    offset = 30000

    rec, = plt.plot(receivedSignal.real[offset:offset+100], 'g')
    rec.set_linewidth(0.5)
    plt.plot(correctedSignal.real[offset:offset+100], 'r')
    plt.plot(idealRecSignal.real[offset:offset+100], 'b--')
    plt.show()

    # constellation plot: QPSK
    receivedConstellation, = plt.plot(correctedSignal.real[4::8], correctedSignal.imag[4::8], 'rx')
    idealConstellation, = plt.plot(idealRecSignal.real[4::8], idealRecSignal.imag[4::8], 'bo')
    plt.axvline(x=0)
    plt.axhline(y=0)
    plt.legend([idealConstellation, receivedConstellation], ['IDEAL CONSTELLATION', 'CORRECTED CONSTELLATION'], loc=3)
    receivedConstellation.set_linewidth(0.1)
    plt.ylim(-2, 2)
    plt.xlim(-2, 2)
    plt.title("O-QPSK CONSTELLATION - IDEAL VS CORRECTED")
    plt.show()
