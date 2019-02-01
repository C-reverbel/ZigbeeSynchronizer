from ZigBeePacket import ZigBeePacket
from WirelessChannel import WirelessChannel
from CFS2 import CFS2
import utils
import numpy as np
import matplotlib.pyplot as plt

class CPS:
    def __init__(self, sampleRate):
        self.sampleRate = sampleRate

    def _loopFilter(self, freq, vector):
        temp = vector.copy()
        C1, C2 = self._computeFilterParameters(freq, self.sampleRate)
        N = vector.__len__()
        phase = 0
        last_old = 0
        last = 0
        deltaPhi_old = 0
        deltaPhi = 0
        for i in range(N):
            # rotate point
            temp[i] = self.compensatePhase(phase, temp[i])
            # compute phase error
            signI = np.sign(temp.real[i])
            signQ = np.sign(temp.imag[i])
            deltaPhi = - temp.real[i] * signQ + temp.imag[i] * signI
            # loop filter
            last = C1 * last_old + C2 * (deltaPhi + deltaPhi_old)
            # update parameters
            deltaPhi_old = deltaPhi
            last_old = last
            phase += last
        return temp

    def _computeFilterParameters(self, freq, sampleRate):
        C1 = (2 - 2 * np.pi * freq * 1e-6 / sampleRate) / (2 + 2 * np.pi * freq * 1e-6 / sampleRate)
        C2 = (2 * np.pi * freq * 1e-6 / sampleRate) / (2 + 2 * np.pi * freq * 1e-6 / sampleRate)
        return C1, C2

    def compensatePhase(self, phase, signal):
        cos = np.cos(phase)
        sin = np.sin(phase)
        resultReal = signal.real * cos + signal.imag * sin
        resultImag = - signal.real * sin + signal.imag * cos
        result = resultReal + 1j * resultImag
        return result

if __name__ == "__main__":
    # Zigbee packet
    nbOfSamples = 1024
    sampleRate = 8
    zigbeePayloadNbOfBytes = 127
    freqOffset = 500e3
    phaseOffset = 15
    SNR = 1000
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
    myChannel = WirelessChannel(sampleRate, 5e3, 0, SNR)
    # receive signal and filter it (change filter order to ZERO to disable filtering)
    receivedSignal = np.roll(utils.butter_lowpass_filter(myChannel.receive(myPacket.IQ), cutoff, fs, order), 0)
    # convert to QPSK
    receivedSignal.imag = np.roll(receivedSignal.imag,-4)
    # sample rate (MHz), number of samples - 2 to compute linear regression
    synchronizer = CPS(8)
    correctedSignal = synchronizer._loopFilter(10e3, receivedSignal)
    plt.plot(myPacket.I[5000:5100], 'b')
    plt.plot(correctedSignal.real[5000:5100], 'r')
    plt.plot(receivedSignal.real[5000:5100], 'g')
    plt.show()