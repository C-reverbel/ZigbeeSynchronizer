from ZigBeePacket import ZigBeePacket
import numpy as np
import matplotlib.pyplot as plt

class WirelessChannel:
    def __init__(self, sampleRate, freqOffset, phaseOffset, SNR):
        self.sampleRate  = sampleRate
        self.freqOffset  = freqOffset
        self.phaseOffset = phaseOffset
        self.SNR         = SNR

    def receive(self, message):
        N = message.__len__()
        n = np.arange(N)

        cos = np.cos(2 * np.pi * 1e-6 * self.freqOffset * n / self.sampleRate + np.pi * self.phaseOffset / 180)
        sin = np.sin(2 * np.pi * 1e-6 * self.freqOffset * n / self.sampleRate + np.pi * self.phaseOffset / 180)
        resultReal = message.real * cos - message.imag * sin
        resultImag = message.imag * cos + message.real * sin
        tempResult = resultReal + 1j * resultImag

        signalPower = self._computeSignalPower(tempResult)
        noise = self._computeNoiseSignal(signalPower, self.SNR, N)

        result = (tempResult.real + noise / np.sqrt(2)) + 1j * (tempResult.imag + noise / np.sqrt(2))
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
    # 2 bytes payload, 8 MHz sample-rate
    myPacket = ZigBeePacket(2,8)
    # sample rate (MHz), frequency offset (Hz), phase offset (degrees), SNR (db)
    myChannel = WirelessChannel(8, 5e3, 10, 500)

    signalPower =  myChannel._computeSignalPower(myPacket.IQ)
    receivedMessage = myChannel.receive(myPacket.IQ)



    ## PLOTS
    # CONSTELLATION PLOT
    transmitted, = plt.plot(myPacket.IQ.real, myPacket.IQ.imag, '-bo')
    transmitted.set_linewidth(4)
    received, = plt.plot(receivedMessage.real, receivedMessage.imag, '-rx')
    received.set_linewidth(0.5)
    plt.title("O-QPSK CONSTELLATION DIAGRAM")
    plt.legend([transmitted, received], ['IDEAL', 'DISTORTED'], loc=3)
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
    spectrum = 10 * np.log10(np.fft.fft(myPacket.IQ))
    spectrum = np.roll(spectrum, spectrum.__len__()/2)
    plt.plot(spectrum, '-b')
    plt.show()