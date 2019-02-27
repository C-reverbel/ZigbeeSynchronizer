#                   _________                         _____                             _____
#                  |         |                       |     |                           |     |
#  myPacket.IQ --> | CHANNEL | -- receivedSignal --> | CFS | -- preCorrectedSignal --> | CPS | --> correctedSignal
#                  |_________|                       |_____|                           |_____|
#
import numpy as np
import matplotlib.pyplot as plt


if __name__ == "__main__":

    from createVariables import *
    corr = []
    maxCorr = float(abs(np.correlate(idealReceivedSignal, idealReceivedSignal)))
    corr.append(maxCorr/maxCorr)
    corr.append(float(abs(np.correlate(idealReceivedSignal, correctedSignal)        ))/maxCorr)
    corr.append(float(abs(np.correlate(idealReceivedSignal, preCorrectedSignal)     ))/maxCorr)
    corr.append(float(abs(np.correlate(idealReceivedSignal, receivedSignal)         ))/maxCorr)
    print corr

    # time domain plot
    offset = 30000
    numberPoints = 80
    samples = range(offset, offset + numberPoints)
    corrTime, = plt.plot(samples, correctedSignal.real[offset:offset + numberPoints], 'b')
    corrTimeQ, = plt.plot(samples, correctedSignal.imag[offset:offset + numberPoints], 'r')
    idealTimeNoNoise, = plt.plot(samples, myPacket.IQ.real[offset:offset + numberPoints], 'c--')
    idealTimeNoNoiseQ, = plt.plot(samples, myPacket.IQ.imag[offset:offset + numberPoints], '--', color='orange')

    plt.title("TIME DOMAIN IN-PHASE SIGNAL - SNR: " + str(SNR) + ", CFS SAMPLES: " + str(nbOfSamples))
    plt.ylabel("Amplitude (Volts)")
    plt.xlabel("samples")
    plt.axhline(y=0, color='k')
    plt.show()