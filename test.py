# Test DAC

import struct
import spidev
from time import sleep

spi = spidev.SpiDev()

bus = 0
device = 0

spi.open(bus,device)
spi.max_speed_hz = 1e6
spi.mode = 2
spi.bits_per_word = 8
spi.lsbfirst=False

inputVoltage = 5000
inputVoltage = float(inputVoltage)
noBits = 12
initialIgnore = '{0:02b}'.format(0)

t = 1

# Power up DAC-A and DAC-B
# 00100000 00000000 00000011
spi.xfer2([0x20, 0x00, 0x3])
sleep(t)

# Disable internal reference and reset DACs to gain = 1
# 00111000 00000000 00000000
spi.xfer2([0x38, 0x0, 0x0])
sleep(t)

# Tell that the /LDAC is low
spi.xfer2([0x30, 0x0, 0x4])
sleep(t)

spi.xfer2([0x17, 0x66, 0x60])

spi.close()
