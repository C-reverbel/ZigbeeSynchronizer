# ZigBeePacket Class creates IEEE 802.15.4 compliant waveforms. The O-QPSK modulated signal varies in amplitude from -1
# to +1.
#
# INPUTS:
#  - payloadNbOfBytes : size of payload in bytes, from 0 to 127. payload value generated randomly
#  - sampleRate       : sample rate in MHz of the waveform. Suggested value = 8 MHz (8 samples per half-sine)
#
# OUTPUT:
#  - IQ : complex vector with In-phase (real part) and Quadrature (imaginary part) components

import random
import numpy as np
import matplotlib.pyplot as plt

symbol2Chip = {
    "0000" : "01110100010010101100001110011011",
    "0001" : "01000100101011000011100110110111",
    "0010" : "01001010110000111001101101110100",
    "0011" : "10101100001110011011011101000100",
    "0100" : "11000011100110110111010001001010",
    "0101" : "00111001101101110100010010101100",
    "0110" : "10011011011101000100101011000011",
    "0111" : "10110111010001001010110000111001",
    "1000" : "11011110111000000110100100110001",
    "1001" : "11101110000001101001001100011101",
    "1010" : "11100000011010010011000111011110",
    "1011" : "00000110100100110001110111101110",
    "1100" : "01101001001100011101111011100000",
    "1101" : "10010011000111011110111000000110",
    "1110" : "00110001110111101110000001101001",
    "1111" : "00011101111011100000011010010011"
} # formatted in MSB first

class ZigBeePacket:
    def __init__(self, payloadNbOfBytes, sampleRate):
        # variables in symbols
        self.preambleInSymbol    = ["0000", "0000",
                                    "0000", "0000",
                                    "0000", "0000",
                                    "0000", "0000"]
        self.SFDInSymbol         = ["1010", "0111"]
        self.PHRInSymbol         = self.computePHR(payloadNbOfBytes)
        self.payloadInSymbol     = self.randomPayload(payloadNbOfBytes)
        # variables in chip format (already formatted to be sent)
        self.preamble = self.symbolToChip(self.preambleInSymbol)
        self.SFD      = self.symbolToChip(self.SFDInSymbol)
        self.PHR      = self.symbolToChip(self.PHRInSymbol)
        self.payload  = self.symbolToChip(self.payloadInSymbol)
        # final message formatted in +1 to -1 range
        self.messageInChip  = self.preamble + self.SFD + self.PHR + self.payload
        self.messageI       = self.messageInChip[0::2]
        self.messageQ       = self.messageInChip[1::2]
        # I and Q oversampled in +1 to -1 range
        self.oversampledI   = self.oversampleMessage(self.messageI, sampleRate)
        self.oversampledQ   = self.oversampleMessage(self.messageQ, sampleRate)
        # I and Q fully formatted in half-sine format
        self.tempI = self.halfSineShaping(self.oversampledI, sampleRate)
        self.tempQ = self.halfSineShaping(self.oversampledQ, sampleRate)
        tempZeros  = np.zeros(sampleRate / 2)
        self.Q     = np.insert(self.tempQ, 0, tempZeros)
        self.I     = np.insert(self.tempI, self.tempI.__len__(), tempZeros)
        self.IQ    = self.I + 1j * self.Q
        self.IQ_QPSK = self.I + 1j * np.roll(self.Q, - (sampleRate / 2))

    def computePHR(self, preambleNbOfBytes):
        temp = "0" + '{0:07b}'.format(preambleNbOfBytes)
        return [temp[:4], temp[4:]]

    def randomPayload(self, preambleNbOfBytes):
        result = []
        for i in range(preambleNbOfBytes * 2):
            result.append('{0:04b}'.format(random.randint(0,15)))
        return result

    def symbolToChip(self, field):
        fieldSizeInBytes = field.__len__() / 2
        result = ""
        for i in range(fieldSizeInBytes):
            temp = symbol2Chip[field[2 * i + 1]]
            result += temp[::-1]
            temp = symbol2Chip[field[2 * i]]
            result += temp[::-1]
        # result is in LSB first format
        return result

    def oversampleMessage(self, message, simulationFrequency):
        result = []
        for i in range(message.__len__()):
            for j in range(simulationFrequency): # bit periode = 1 / 1 MHz
                result.append(str(2 * int(message[i]) - 1))
        return result

    def halfSineShaping(self, message, simulationFrequency):
        x = np.arange(message.__len__())
        halfSine = np.abs(np.sin(np.pi * x / simulationFrequency))#
        messageInt = map(int, message)
        result = halfSine * messageInt
        return result


if __name__ == "__main__":
    simFreq = 8
    payloadSize = 2
    myPacket = ZigBeePacket(payloadSize, simFreq)

    N = myPacket.Q.__len__()

    plt.plot(myPacket.I, myPacket.Q, '--bo')
    plt.title("O-QPSK CONSTELLATION DIAGRAM")
    plt.show()

    plt.subplot(2, 1, 1)
    inphase,    = plt.plot(myPacket.IQ.real[:200], '--ro')
    plt.subplot(2, 1, 2)
    quadrature, = plt.plot(myPacket.IQ.imag[:133], '--bo')
    #plt.legend([inphase, quadrature], ['IN-PHASE', 'QUADRATURE'])
    plt.title("BEGINNING OF ZIGBEE PREAMBLE")
    plt.ylabel("voltage")
    plt.xlabel("samples")
    plt.show()

    #inphase, = plt.plot(myPacket.IQ.real[:100], '--r')
    #quadrature, = plt.plot(myPacket.IQ.imag[:100], '--b')
    ##mixSquare, = plt.plot(0.5 * (myPacket.IQ.real[:100]**2 - myPacket.IQ.imag[:100]**2), '--go')
    ##mix, = plt.plot(myPacket.IQ.real[:100] * myPacket.IQ.imag[:100], '--ko')
    #mult, = plt.plot(0.5 * (myPacket.IQ.real[:100]**2 - myPacket.IQ.imag[:100]**2) + myPacket.IQ.real[:100] * myPacket.IQ.imag[:100], '--ko')
    #inphase.set_linewidth(0.5)
    #quadrature.set_linewidth(0.5)
    #plt.show()
