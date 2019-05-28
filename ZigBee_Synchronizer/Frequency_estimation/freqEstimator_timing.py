from System_blocks.ZigBeePacket import ZigBeePacket
from System_blocks.WirelessChannel import WirelessChannel
from System_blocks.CFS_iterative import CFS_iterative
from System_blocks.CFS_direct import CFS_direct
from System_blocks.CPS import CPS
import utils
import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":
    # Zigbee packet
    sampleRate = 8
    zigbeePayloadNbOfBytes = 5
    freqOffset = 200000.0
    phaseOffset = 0.0
    SNR = 8.
    leadingNoiseSamples = 35
    trailingNoiseSamples = 0

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
    receivedSignal = utils.butter_lowpass_filter(
        myChannel.receive(myPacket.IQ,
                          leadingNoiseSamples,
                          trailingNoiseSamples),
        cutoff, fs, order)

    kernel = [0.0, 0.382683432, 0.707106781, 0.923879533, 1.0, 0.923879533, 0.707106781, 0.382683432, 0.0]
    #kernel = [1]



    matched =   np.correlate(receivedSignal.real, kernel, mode='full') + \
                 1j * np.correlate(receivedSignal.imag, kernel, mode='full')

    Sq = abs(matched) ** 2
    Sd = (Sq[2:-1] - Sq[:-3]) * Sq[1:-2]
    #Sd =    receivedSignal.real[1:-2]*(receivedSignal.real[2:-1] - receivedSignal.real[:-3]) \
    #        + receivedSignal.imag[1:-2]*(receivedSignal.imag[2:-1] - receivedSignal.imag[:-3])
    #Sd = matched.real[1:-2] * (matched.real[2:-1] - matched.real[:-3]) \
    #        + matched.imag[1:-2]*(matched.imag[2:-1] - matched.imag[:-3])
    Et = Sd[2:-3] * (Sd[4:-1] - Sd[:-5])
    D = Et[:-5] - Et[4:-1]

    Cn = ((matched.real[:-127] * matched.real[127:] + \
          matched.imag[:-127] * matched.imag[127:]) ** 2 ) * Sq[:-127]

    maxPlot = 60
    plt.plot(Sd[:maxPlot],'bx-')
    #plt.ylim(0,2)
    index = np.argmax(Et[:maxPlot])
    plt.axvline(x = index,color ='k', linewidth=0.5)
    plt.show()
    print index










