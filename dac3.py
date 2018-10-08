
# Pulse DAC

import spidev
import sys
import time
bus = 0
device = 0

spi = spidev.SpiDev()

spi.open(bus,device)
spi.max_speed_hz = 1000000 # 1 MHz                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
spi.mode = 2
spi.bits_per_word = 8
spi.lsbfirst = False
bits = 12

def operation(DAC, outputmV, inputVoltage, command):
## Possible Commands:
##    0 = write to register only
##    1 = update register only
##    2 = write to register and update all DACs
##    3 = write and update nominated register only
    commands = ['000','001','010','011']
    addresses = ['000','001','111'] # [DAC-A, DAC-B, both]
    commandBinary = commands[command]

    if (DAC == 'a'):
        address = addresses[0]
    elif (DAC == 'b'):
        address = addresses[1]
    elif (DAC == 'both'):
        address = addresses[2]
    else:
        print("DAC not correct, please enter either 'a', 'b', or 'both'")
        sys.exit()

    outputmV = float(outputmV)
    inputVoltage = float(inputVoltage)
    data = int(outputmV/inputVoltage*(2**bits)) # bits to be sent as input data out of 2^12
    outputmV_bin = '{0:012b}'.format(data)

    output = str('00' + commandBinary + address + outputmV_bin + '0000')
    trueOutput = float(data)/(2**bits)*inputVoltage
    
    return output, trueOutput

def power(data):
    #output = powerUp(DAC, data) ## where DAC = 'a' or 'b' or 'both'
##                                and data is a command from 0 to 11 
## Possible commands:
##    0 = Power up DAC-A
##    1 = Power-up DAC-B
##    2 = Power-up DAC-A and DAC-B
##    3 = Power down DAC-A: 1 kOhm to GND
##    4 = Power down DAC-B: 1 kOhm to GND
##    5 = Power down DAC-A and DAC-B: 1 kOhm to GND
##    6 = Power down DAC-A: 100 kOhm to GND
##    7 = Power down DAC-B: 100 kOhm to GND
##    8 = Power down DAC-A and DAC-B: 100 kOhm to GND
##    9 = Power down DAC-A: Open circuit
##    10 = Power down DAC-B: Open circuit
##    11 = Power down DAC-A and DAC-B: Open circuit
    commands = ['001000000000000000000001', 
                '001000000000000000000010',
                '001000000000000000000011',
                '001000000000000000010001',
                '001000000000000000010010',
                '001000000000000000010011',
                '001000000000000000100001',
                '001000000000000000100010',
                '001000000000000000100011',
                '001000000000000000110001',
                '001000000000000000110010',
                '001000000000000000110011']
    output = commands[data]
    return output

def other(command):
##    Possible commands:
##        0 = Reset DAC-A and DAC-B input register and update all DACs
##        1 = Reset all registers and update all DACs (power on reset update)
##        2 = /LDAC pin active for DAC-B and DAC-A
##        3 = /LDAC pin active for DAC-B; inactive for DAC-A
##        4 = /LDAC pin inactive for DAC-B; active for DAC-A
##        5 = /LDAC pin inactive for DAC-B and DAC-A
##        6 = Disable internal reference and reset DACs to gain = 1
##        7 = Enable internal reference and reset DACs to gain = 2
    commands = ['001010000000000000000000',
                '001010000000000000000001',
                '001100000000000000000000',
                '001100000000000000000001',
                '001100000000000000000010',
                '001100000000000000000011',
                '001110000000000000000000',
                '001110000000000000000001']
    output = commands[command]
    return output

def convertToThreeBytes(input):
    # convert to three eight bit integers for spi library
    output = [int(input[:8],2), int(input[8:16],2), int(input[16:],2)]
    return output

def setup():
    # Power up device
    powerUp = power(2)
    msg = convertToThreeBytes(powerUp)
    spi.xfer2(msg)

    # Disable internal reference
    reference = other(7) # enable internal reference
    msg = convertToThreeBytes(reference)
    spi.xfer2(msg)

    # Use internal LDAC pin to have synchronous updates
    LDAC = other(5)
    msg = convertToThreeBytes(LDAC)
    spi.xfer2(msg)

def constantOutput(DAC, outputmV, inputmV, command):
    try:
        output, expectedOutput = operation(DAC, outputmV, inputmV, 2)
        msg = convertToThreeBytes(output)
        spi.xfer2(msg)
    except (KeyboardInterrupt, SystemExit):
        output, expectedOutput = operation(DAC, 0, inputmV, 2)
        msg = convertToThreeBytes(output)
        spi.xfer2(msg)
        spi.close()
        sys.exit("Constant output error - system stopped. Returned to 0 V")

def pulsedOutput(DAC, outputmV, inputmV, command, on, off):
    try:
        output, expectedOutput = operation(DAC, outputmV, inputmV, command)
        msg = convertToThreeBytes(output)
        spi.xfer2(msg)
        time.sleep(on)
        output, expectedOutput = operation(DAC, 0, inputmV, command)
        msg = convertToThreeBytes(output)
        spi.xfer2(msg)
        time.sleep(off)
    except (KeyboardInterrupt, SystemExit):
        output, expectedOutput = operation(DAC, 0, inputmV, command)
        msg = convertToThreeBytes(output)
        spi.xfer2(msg)
        spi.close()
        sys.exit("Pulsing system stopped. Returned to 0 V")

def main(argv):
    setup()
    inputmV = 5000
    DAC = sys.argv[1]
    output = float(sys.argv[2])
    frequency = float(sys.argv[3])
    on = float(sys.argv[4])/1000.0000
    
    if frequency == 0:
        constantOutput(DAC, output, inputmV, 2)
        print("Output:", output, "mV")
        print("Frequency: ", frequency, "Hz")
        print("On pulse:", on*1000, "ms")
    elif on == 0:
        on = 1./(frequency*2)-0.0001111
        off = on
        print("Output:", output, "mV")
        print("Frequency: ", frequency, "Hz")
        print("On pulse:", on*1000, "ms")
        while True:
          pulsedOutput(DAC, output, inputmV, 2, on, off)
    else:
        if (1.0000/frequency < on):
            sys.exit("On pulse longer than frequency")
        else:
            on = on/1000.0000
        # Set output voltage and update, max pulse is 9 kHz
        # time = 0 => wavelength = 111.11 us
        on = on - 0.0001111
        off = 1 - on
        print("Output:", output, "mV")
        print("Frequency: ", frequency, "Hz")
        print("On pulse:", on*1000, "ms")   
        while True:
          pulsedOutput(DAC, output, inputmV, 2, on, off)
        
if __name__ == '__main__':
    main(sys.argv[1:])

