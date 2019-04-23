# Carrier Phase Synchronizer (CPS) performs a fine instantaneous phase compensation using Costas Loop algorithm
#
# INPUTS:
#   - sampleRate : sample rate in MHz of the waveform. Suggested value = 8 MHz (8 samples per half-sine)
#
# METHODS:
#   - costasLoop(freq, vector)
#       - IN : freq, vector --> loop-filter cut-off frequency in Hz, ZigBee IQ complex signal
#       - OUT: temp, phaseVect, sign --> corrected signal, vector with estimated instantaneous phase,
#       IQ signal in binary format (values can assume +1 and -1 values)

from ZigBeePacket import ZigBeePacket
from WirelessChannel import WirelessChannel
from CFS_iterative import CFS_iterative
import utils
import numpy as np
import matplotlib.pyplot as plt

class CPS:
    def __init__(self, sampleRate):
        self.sampleRate = sampleRate
        self.myPacket = ZigBeePacket(1, sampleRate)

    def costasLoop(self, freq, vector):
        temp = vector.copy()
        N = vector.__len__()
        phaseVect = np.zeros(N)
        sign = np.zeros(N) + 1j * np.zeros(N)
        phase = 0

        # loop filter variables
        last, last_old, deltaPhi_old = 0, 0, 0
        for i in range(self.sampleRate/2,N):
            # rotate signal
            temp[i] = self._compensatePhase(phase, temp[i])
            y_i = temp.real[i-self.sampleRate/2]
            y_q = temp.imag[i]
            # compute phase error
            signI = np.sign(temp.real[i-self.sampleRate/2])
            signQ = np.sign(temp.imag[i])
            deltaPhi = y_q * signI - y_i * signQ
            # loop filter
            last, last_old, deltaPhi_old = self._iterativeLowPassFilter(freq, last, last_old, deltaPhi, deltaPhi_old)
            # constant value empirically tested :p
            phase += (0.0625 * last)
            phase = phase % (2 * np.pi)
            phase = phase if phase < np.pi else (phase - 2 * np.pi)
            # also return phase and signal for debug only
            phaseVect[i] = phase
            sign[i] = signI + 1j*signQ
        return temp, phaseVect, sign

    def _iterativeLowPassFilter(self, cutoffFrequency, y, y_old, x, x_old):
        C1, C2 = self._computeFilterParameters(cutoffFrequency, self.sampleRate)
        # TEST
        #C1, C2 = 0.5, 0.25 ## Fc = 850 kHz
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

    def _compensatePhase(self, phase, signal):
        return np.exp(-1j * phase) * signal

if __name__ == "__main__":
    # Zigbee packet
    sampleRate = 8
    zigbeePayloadNbOfBytes = 127
    freqOffset = 500. # max 450 @ SNR = 10
    phaseOffset = 70. # max 25  @ SNR = 10
    SNR = 10.
    # Butterworth low-pass filter
    cutoff = 2e6
    fs = sampleRate * 1e6
    order = 0

    print "Zigbee payload size = " + str(zigbeePayloadNbOfBytes) + " bytes"
    print "Sample rate = " + str(sampleRate) + " MHz"
    print "Frequency offset = " + str(freqOffset) + " Hz"
    print "Phase offset = " + str(phaseOffset) + " Degrees"
    print "SNR = " + str(SNR) + " dB"
    print "\n"

    # payload in bytes, sample-rate in MHz
    myPacket = ZigBeePacket(zigbeePayloadNbOfBytes, sampleRate)
    N = myPacket.I.__len__()

    # sample-rate (MHz), frequency offset (Hz), phase offset (degrees), SNR (dB)
    myChannel = WirelessChannel(sampleRate, freqOffset, phaseOffset, SNR)
    # receive signal and filter it (change filter order to ZERO to disable filtering)
    receivedSignal = np.roll(utils.butter_lowpass_filter(myChannel.receive(myPacket.IQ), cutoff, fs, order), 0)

    # Instantiate CPS
    # sample rate (MHz)
    synchronizer = CPS(sampleRate)
    correctedSignal, phaseVector, _ = synchronizer.costasLoop(850000, receivedSignal)

    # define ideal noisy signal (no freq or phase offset)
    channel2 = WirelessChannel(sampleRate, 0, 0, SNR)
    idealRecSignal = np.roll(utils.butter_lowpass_filter(channel2.receive(myPacket.IQ), cutoff, fs, order), 0)



    ############################################################################################################### PLOT
    #correctedSignal.imag = np.roll(correctedSignal.imag, 4)
    #idealRecSignal.imag = np.roll(idealRecSignal.imag, 4)# time vector
    maxTime = (1e-6 / sampleRate) * N
    timeStep = 1e-6 / sampleRate
    time = np.arange(0, maxTime, timeStep)

    instPhase = np.zeros(N)
    instPhase[::] = 2 * np.pi * freqOffset * time[::] + phaseOffset * np.pi / 180

    lim = 10000
    ref, = plt.plot(time[:lim], instPhase[:lim], 'c--')
    estimate, = plt.plot(time[:lim], phaseVector[:lim],'b')
    ref.set_linewidth(4)
    plt.show()



    err_corrected = utils.calcAverageError(idealRecSignal, correctedSignal)
    err_received = utils.calcAverageError(idealRecSignal, receivedSignal)

    print "received signal | corrected signal: ", err_received / err_received, " | ", err_corrected / err_received

    offset = 10000
    # plot time domain signal
    rec, = plt.plot(receivedSignal.real[offset:offset+100], 'g')
    rec.set_linewidth(0.5)
    plt.plot(correctedSignal.real[offset:offset+100], 'r')
    plt.plot(idealRecSignal.real[offset:offset+100], 'b--')
    plt.show()

    # plot phase differences
    phaseDifference = np.unwrap(np.angle(receivedSignal)) - np.unwrap(np.angle(myPacket.IQ))
    phaseNoiseCFS, = plt.plot(1e3 * time, phaseDifference, 'orange')
    plt.yticks(np.arange(-100 * np.pi, 100 * np.pi / 2, np.pi / 2))
    phaseDifference = utils.butter_lowpass_filter(phaseDifference, 5000, sampleRate * 1e6, 2)
    phaseCFS, = plt.plot(1e3 * time, phaseDifference, 'r--')
    phaseDifference = np.unwrap(np.angle(correctedSignal)) - np.unwrap(np.angle(myPacket.IQ))
    phaseNoiseCPS, = plt.plot(1e3 * time, phaseDifference, 'b')
    phaseDifference = utils.butter_lowpass_filter(phaseDifference, 5000, sampleRate * 1e6, 2)
    phaseCPS, = plt.plot(1e3 * time, phaseDifference, 'c--')
    phaseNoiseCFS.set_linewidth(0.1)
    phaseNoiseCPS.set_linewidth(0.1)
    phaseCFS.set_linewidth(4)
    phaseCPS.set_linewidth(4)
    plt.legend([phaseCFS, phaseCPS], ['WITHOUT CPS', 'WITH CPS'], loc=3)
    plt.title("PHASE ERROR VS TIME - SNR: " + str(SNR))
    plt.ylabel("PHASE (rad)")
    plt.xlabel("TIME (ms)")
    plt.grid(b=None, which='major', axis='both')
    plt.show()
