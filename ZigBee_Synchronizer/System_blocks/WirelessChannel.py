# This class simulates the effect of a noisy channel + frequency and phase mismatch between transmitter and
# receiver. It receives a clean base-band signal and adds noise, frequency and phase offset to it, returning
# the new base-band signal.
#
# INPUT:
#   - sampleRate  : sample rate in MHz of the waveform. Suggested value = 8 MHz (8 samples per half-sine)
#   - freqOffset  : frequency offset (in Hz) to add to the signal
#   - phaseOffset : phase offset (in Degrees) to add to the signal
#   - SNR         : Signal to Noise Ration of output signal
#
# METHODS:
#   - receive(message)
#       - IN : message --> base-band ZigBee IQ complex signal
#       - OUT: base-band ZigBee IQ complex signal with noise, frequency and phase offset

from ZigBeePacket import ZigBeePacket
import numpy as np
import matplotlib.pyplot as plt

class WirelessChannel:
    def __init__(self, sampleRate, freqOffset, phaseOffset, SNR):
        self.sampleRate  = sampleRate
        self.freqOffset  = freqOffset
        self.phaseOffset = phaseOffset
        self.SNR         = SNR

    def receive(self, message, leadingNoiseSamples = 0, trailingNoiseSamples = 0):
        N = message.__len__()
        n = np.arange(N)

        self.LNS = leadingNoiseSamples
        self.TNS = trailingNoiseSamples

        cos = np.cos(2 * np.pi * 1e-6 * self.freqOffset * n / self.sampleRate + np.pi * self.phaseOffset / 180)
        sin = np.sin(2 * np.pi * 1e-6 * self.freqOffset * n / self.sampleRate + np.pi * self.phaseOffset / 180)

        signalPower = self._computeSignalPower(message)
        noise1 = self._computeNoiseSignal(signalPower, self.SNR, N + self.LNS + self.TNS)
        noise2 = self._computeNoiseSignal(signalPower, self.SNR, N + self.LNS + self.TNS)

        tempReal = message.real * cos - message.imag * sin
        tempImag = message.imag * cos + message.real * sin
        # append leading and trailing zeros to the message
        resultReal = np.pad(tempReal, (self.LNS,self.TNS), 'constant', constant_values=(0,0))
        resultImag = np.pad(tempImag, (self.LNS,self.TNS), 'constant', constant_values=(0,0))

        result = (resultReal + noise1 / np.sqrt(2)) + 1j * (resultImag + noise2 / np.sqrt(2))

        return result

    def _computeSignalPower(self, signal):
        N = signal.__len__()
        signalAbs = abs(signal)
        energy = 0
        for i in range(N):
            energy += signalAbs[i] * signalAbs[i]
        power = energy / N
        return power

    def _computeNoiseSignal(self, signalPower, SNR, N):
        standardDev = np.sqrt(signalPower * 10 **(-SNR/10))
        noise = np.random.normal(0,standardDev,N)
        return noise


if __name__ == "__main__":
    sampleRate = 8
    SNR = 15
    freqOffset = 0.
    phaseOffset = 10
    # payload size in bytes, sample-rate in MHz
    myPacket = ZigBeePacket(20, sampleRate)
    # sample rate (MHz), frequency offset (Hz), phase offset (degrees), SNR (db)
    myChannel = WirelessChannel(sampleRate, freqOffset, phaseOffset, SNR)

    N = myPacket.I.__len__()
    txSignalPower = myChannel._computeSignalPower(myPacket.IQ)
    receivedMessage = myChannel.receive(myPacket.IQ, 10, 5)
    rxSignalPower = myChannel._computeSignalPower(receivedMessage)


    print "Sample rate = " + str(sampleRate) + " MHz"
    print "Frequency offset = " + str(freqOffset / 1000) + " kHz"
    print "Phase offset = " + str(phaseOffset) + " Degrees"
    print "SNR = " + str(SNR) + " dB"

    print "Transmitted signal power = " + str(10 * np.log10(txSignalPower) + 30) + " dBm"
    print "Received signal power = " + str(10 * np.log10(rxSignalPower) + 30) + " dBm"
    print "Estimated noise power = " + str(10 * np.log10(rxSignalPower - txSignalPower) + 30) + " dBm"


    ## PLOTS
    # CONSTELLATION PLOT
    transmitted, = plt.plot(myPacket.IQ.real, myPacket.IQ.imag, '-bo')
    received, = plt.plot(receivedMessage.real, receivedMessage.imag, '-r')
    plt.legend([transmitted, received], ['IDEAL', 'DISTORTED'], loc=3)
    transmitted.set_linewidth(4)
    received.set_linewidth(0.1)
    plt.title("O-QPSK CONSTELLATION DIAGRAM")
    plt.show()
    # TIME-DOMAIN PLOT
    ## Transmitted IQ signals
    inphaseTx, = plt.plot(myPacket.IQ.real[:100], '--ro')
    quadratureTx, = plt.plot(myPacket.IQ.imag[:100], '--bo')
    plt.legend([inphaseTx, quadratureTx], ['IN-PHASE', 'QUADRATURE'], loc=3)
    plt.title("BEGINNING OF ZIGBEE PREAMBLE - Tx")
    plt.ylabel("voltage")
    plt.xlabel("samples")
    plt.show()
    ## Received IQ signals
    inphaseRx, = plt.plot(receivedMessage.real[:100], '--ro')
    quadratureRx, = plt.plot(receivedMessage.imag[:100], '--bo')
    plt.legend([inphaseRx, quadratureRx], ['IN-PHASE', 'QUADRATURE'], loc=3)
    plt.title("BEGINNING OF ZIGBEE PREAMBLE - Rx")
    plt.ylabel("voltage")
    plt.xlabel("samples")
    plt.show()
    ## I signals comparison
    inphaseTx, = plt.plot(myPacket.IQ.real[:100], '-b')
    inphaseTx.set_linewidth(2)
    inphaseRx, = plt.plot(receivedMessage.real[:100], '-rx')
    inphaseRx.set_linewidth(0.5)
    plt.legend([inphaseTx, inphaseRx], ['TRANSMITTED', 'RECEIVED'], loc=3)
    plt.title("COMPARISON: IN-PHASE SIGNALS")
    plt.ylabel("voltage")
    plt.xlabel("samples")
    plt.show()
    ## Q signals comparison
    quadratureTx, = plt.plot(myPacket.IQ.imag[:100], '-b')
    quadratureTx.set_linewidth(2)
    quadratureRx, = plt.plot(receivedMessage.imag[:100], '-rx')
    quadratureRx.set_linewidth(0.5)
    plt.legend([quadratureTx, quadratureRx], ['TRANSMITTED', 'RECEIVED'], loc=3)
    plt.title("COMPARISON: QUADRATURE SIGNALS")
    plt.ylabel("voltage")
    plt.xlabel("samples")
    plt.show()
    ## plot spectrum
    f = 1e-6 * np.arange(-sampleRate * 0.5e6, sampleRate * 0.5e6, sampleRate * 1e6 / N)

    spectrum = 20 * np.log10(abs(np.fft.fft(myPacket.IQ))) + 30
    spectrum = np.roll(spectrum, N/2)

    spectrum2 = 20 * np.log10(abs(np.fft.fft(receivedMessage))) + 30
    spectrum2 = np.roll(spectrum2, N / 2)

    idealSpectre, = plt.plot(f, spectrum, '-b')
    receivedSpectre, = plt.plot(f, spectrum2, '-r')
    plt.legend([idealSpectre, receivedSpectre], ['TRANSMITTED', 'RECEIVED'], loc=1)
    idealSpectre.set_linewidth(0.1)
    receivedSpectre.set_linewidth(0.1)
    plt.title("RECEIVED SIGNAL POWER SPECTRUM")
    plt.ylabel("Energy (dBm)")
    plt.xlabel("frequency (MHz)")
    plt.ylim(30, 85)
    plt.xlim(-sampleRate/2, sampleRate/2)
    plt.show()
