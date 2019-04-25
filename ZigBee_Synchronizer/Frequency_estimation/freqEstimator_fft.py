from System_blocks.ZigBeePacket import ZigBeePacket
from System_blocks.WirelessChannel import WirelessChannel
from System_blocks.CFS_iterative import CFS_iterative
from System_blocks.CFS_direct import CFS_direct
from System_blocks.CPS import CPS
import utils
import numpy as np
import matplotlib.pyplot as plt

class FrequencyEstimator:
    def __init__(self, sampleRate):
        self.sampleRate = sampleRate
        # kernel assumes sampleRate = 8MHz, todo fix this
        self.kernel = [0.0, 0.382683432, 0.707106781, 0.923879533, 1.0, 0.923879533, 0.707106781, 0.382683432, 0.0]

    def estimateFrequency(self, vector):
        N = vector.__len__()
        # frequency vector
        maxFreq = 1e6 * self.sampleRate / 2
        freqStep = 2 * maxFreq / N
        self.frequencyPos = np.arange(0, maxFreq - freqStep, freqStep)
        frequencyNeg = np.arange(-maxFreq, 0, freqStep)
        frequency = np.append(frequencyNeg, self.frequencyPos)
        # apply matched filter on input vector (can use either real or imaginary part)
        self.rec_convolved = np.correlate(vector.real, self.kernel, mode='full')
        # take FFT of the square of it
        self.rec_fft = np.fft.fft(self.rec_convolved ** 2)
        # compute frequency offset
        m = max(abs(self.rec_fft[10:N/4]))
        index = [i for i, j in enumerate(abs(self.rec_fft)) if j == m]
        # return estimated frequency in Hz
        return abs(1e6 - self.frequencyPos[index[0]])/2


if __name__ == "__main__":
    # Zigbee packet
    sampleRate = 8
    zigbeePayloadNbOfBytes = 50
    freqOffset = 10000.0
    phaseOffset = 0.0
    SNR = 6.
    # Butterworth low-pass filter
    cutoff = 3e6
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

    ## FREQUENCY ESTIMATOR
    freqEst = FrequencyEstimator(8)

    freqEstVect = []
    indexes = []
    for i in np.arange(128,N,128):
        temp = freqEst.estimateFrequency(receivedSignal.real[:i])
        freqEstVect.append(temp)
        indexes.append(i)
        print i, temp
        #plt.plot(freqEst.frequencyPos[10:i/4]/1000,abs(freqEst.rec_fft[10:i/4]))
        #plt.show()
    plt.plot(indexes,freqEstVect)
    plt.axhline(y=abs(freqOffset),color='k')
    plt.axvline(x=1024, color='k')
    plt.axvline(x=1536, color='k')
    plt.show()