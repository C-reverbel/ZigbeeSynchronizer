import numpy as np
from scipy.signal import butter, lfilter
import matplotlib.pyplot as plt

from System_blocks.ZigBeePacket import ZigBeePacket
from System_blocks.WirelessChannel import WirelessChannel


def _butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = _butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y

# sampleRate in MHz
def plotSpectrum(data, sampleRate, title = "POWER SPECTRUM DENSITY"):
    N = data.__len__()
    f = 1e-6 * np.arange(-sampleRate * 0.5e6, sampleRate * 0.5e6, sampleRate * 1e6 / N)

    spectrum = 20 * np.log10(abs(np.fft.fft(data))) + 30
    spectrum = np.roll(spectrum, N / 2)

    myPlot, = plt.plot(f, spectrum, '-b')
    myPlot.set_linewidth(0.5)
    plt.title(title)
    plt.ylabel("Energy (dBm)")
    plt.xlabel("frequency (MHz)")
    plt.ylim(20, max(spectrum) + 5)
    plt.xlim(-sampleRate / 2, sampleRate / 2)
    plt.show()

def calcAverageError(vectOne, vectTwo):
    N = vectOne.__len__()
    errVector = abs(vectOne - vectTwo)
    return sum(errVector) / N

def convertToQPSK(vector, sampleRate):
    return vector.real + 1j * np.roll(vector.imag, - sampleRate / 2)

def extractPhase(signal):
    return np.sign(signal.real) + 1j * np.sign(signal.imag)

def correlate(signal1, signal2, sizeToPlot, normalizationCte = 1):
    if signal2.__len__() > signal1.__len__():
        N = signal2.__len__()
        tempVec = np.concatenate((signal1, np.zeros(N)), axis=0)
        tempVec = np.roll(tempVec, N)
        tempVec = np.roll(tempVec, -sizeToPlot/2)
        result = []
        for i in range(sizeToPlot):
            temp = float(abs(np.correlate(tempVec[-N:], signal2))) / normalizationCte
            result.append(temp)
            tempVec = np.roll(tempVec,1)
    else:
        N = signal1.__len__()
        tempVec = np.concatenate((signal2, np.zeros(N)), axis=0)
        tempVec = np.roll(tempVec, N)
        tempVec = np.roll(tempVec, -sizeToPlot / 2)
        result = []
        for i in range(sizeToPlot):
            temp = float(abs(np.correlate(tempVec[-N:], signal1))) / normalizationCte
            result.append(temp)
            tempVec = np.roll(tempVec, 1)
    return result

if __name__ == "__main__":
    sampleRate = 8
    # payload size in bytes, sample-rate in MHz
    myPacket = ZigBeePacket(8, sampleRate)
    # sample rate (MHz), frequency offset (Hz), phase offset (degrees), SNR (db)
    myChannel = WirelessChannel(8, 200.e3, 0.0, 100)
    receivedMessage = myChannel.receive(myPacket.IQ)

    N = myPacket.I.__len__()

    # Filter requirements.
    order = 0
    fs = 8e6  # sample rate, Hz
    cutoff = 2e6  # desired cutoff frequency of the filter, Hz

    # Get the filter coefficients so we can check its frequency response.
    #receivedMessage = butter_lowpass_filter(receivedMessage, cutoff, fs, order)

    ## PLOT
    f = 1e-6 * np.arange(-sampleRate * 0.5e6, sampleRate * 0.5e6, sampleRate * 1e6 / N)
    spectrum = 20 * np.log10(abs(np.fft.fft(myPacket.IQ))) + 30
    spectrum = np.roll(spectrum, N / 2)

    spectrum2 = 20 * np.log10(abs(np.fft.fft(receivedMessage))) + 30
    spectrum2 = butter_lowpass_filter(spectrum2, cutoff, fs, order)
    spectrum2 = np.roll(spectrum2, N / 2)
    idealSpectre, = plt.plot(f, spectrum, '-b')
    receivedSpectre, = plt.plot(f, spectrum2, '-r')
    idealSpectre.set_linewidth(0.1)
    receivedSpectre.set_linewidth(0.1)
    plt.title("RECEIVED SIGNAL SPECTRUM")
    plt.ylabel("Energy (dBm)")
    plt.xlabel("frequency (MHz)")
    plt.ylim(-10, 85)
    plt.xlim(-sampleRate / 2, sampleRate / 2)
    plt.show()