# Test DAC

import struct
import spidev
from time import sleep

spi = spidev.SpiDev()

bus = 0
device = 0

spi.open(bus,device)
spi.max_speed_hz = 1*1000*1000
spi.mode = 2
spi.bits_per_word = 8
spi.lsbfirst=False

t = 1

# Power up DAC-A and DAC-B
# 00100000 00000000 00000011
spi.xfer2([0x20, 0x00, 0x3])
sleep(t)

# Disable internal reference and reset DACs to gain = 1
# 00111000 00000000 00000000
spi.xfer2([0x38, 0x0, 0x0])
sleep(t)

# LDAC pin inactive for DAC-B and DAC-A
# 00110000 00000000 00000011
spi.xfer2([0x30, 0x0, 0x3])
sleep(t)

# Write to DAC-A input register and update all DACs
# 00010111 10000000 00000000
a = ((2**8 * 0x66) + 0x60) << 4

##c >> 4 = 2**8 * a + b
spi.xfer2([23, 11100110, 96])
a = float(a)
expected = float(a/4096*5000)
print("expected [mV]", expected)
spi.close()
