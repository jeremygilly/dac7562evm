# Pulse DAC

# Recommended pin out assuming RPi 3 (SPI bus 2, device 0) to DAC7562EVM
# 5V to J3.3 (AVdd)
# GND to J3.5

# GND to J1.1
# Vout to J1.2

# SPI1 MOSI (pin 38) to J2.11 
# SPI1 MISO (pin 35) to [not required, it sends nothing back]
# SPI1 SCLK (pin 40) to J2.3
# SPI1 CE0 (pin 12) to J2.9

import numpy as np
import spidev
import sys
import time

class DAC7562():
    address_dict = dict([
		('a','000'),
        ('b','001'),
        ('gain','010'),
        ('ab','111'),
	])
    
    command_dict = dict([
		('write_no_update','000'),
        ('ldac_update','001'),
        ('write_update_all','010'),
        ('write_update','011'),
        ('power','100'),
        ('software_reset','101'),
        ('ldac','110'),
        ('reference','111'),
	])
    gain_dict = dict([
		('2','0'),
        ('1','1'),
	])
    mode_dict = dict([
        ('power_up', '00'),
        ('power_down_1k_gnd', '01'),
        ('power_down_100k_gnd', '10'),
        ('power_down_hi-z_gnd', '11'),
    ])
    ldac_dict = dict([
        ('ldac','0'),
        ('synchronous','1'),
    ])
    software_reset_dict = dict([
        ('reset_dac','0'),
        ('reset_all','1'),
    ])
    
    inv_address_dict = {v: k for k, v in address_dict.items()}
    inv_command_dict = {v: k for k, v in command_dict.items()}
    inv_gain_dict = {v: k for k, v in gain_dict.items()}
    inv_mode_dict = {v: k for k, v in mode_dict.items()}
    inv_ldac_dict = {v: k for k, v in ldac_dict.items()}
    inv_software_reset_dict = {v: k for k, v in software_reset_dict.items()}
    
    def __init__(self, 
                    bus = 1, # changed to 1 to work alongside ADS1261
                    device = 0,
                    max_speed_hz = 1000000,
                    mode = 2,
                    bits_per_word = 8,
                    lsbfirst = False):

        
        self.bus = bus
        self.device = device
        self.spi = spidev.SpiDev()
        self.spi.open(self.bus,self.device)
        self.spi.max_speed_hz = 1000000 # 1 MHz                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
        self.spi.mode = 2
        self.spi.bits_per_word = 8
        self.spi.lsbfirst = False
        bits = 12
        # gain = 2 by default when using internal reference (pg 28 DAC7562 datasheet)
        
    def help(self):
        print("DAC:",str(list(self.address_dict.keys())))
        print("Commands:",str(list(self.command_dict.keys())))
        print("Gain:", str(list(self.gain_dict.keys())))
        print("Mode:", str(list(self.mode_dict.keys())))
        print("Selection:", str(list(self.ldac_dict.keys())))
        print("Software Reset:", str(list(self.software_reset_dict.keys())))
        print("Vout: between -300 and 5700 mV (depending on power source).")
    
    def convertToThreeBytes(self, m):
        # convert to three eight bit integers for spi library
        if len(m) != 24 or type(m) != str: self.end(a = "Error! 24 bits not sent to DAC\nMessage sent: " + m + "\nLength: "+ str(len(m)))
        output = [int(m[:8],2), int(m[8:16],2), int(m[16:],2)]
        return output
        
    def Vout_to_bin(self, Vout, Vref = 2500, gain = 2):
        # returns the binary that is loaded into the DAC register
        # takes a Vout [mV] value to be created (between 0 and x), a reference Voltage, and gain
        #~ bits = 2**n, where n = 12 (pre-loaded as 4096 to speed up calculation)
        if Vout < 5700 and Vout > -300:
            data = int(Vout*4096/(Vref*gain))
            Din = '{0:012b}'.format(data)
            #~ print(data, Din)
        else:
            a = "Vout was beyond the absolute maximum rating for a DAC7562 (Table 7.1 in DAC7562 datasheet).\nIt must be between -300 and 5700 mV and you asked for " + str(Vout) + " mV.\nPlease check your Vout and try again."
            self.end(a = a)
        return Din 
        
    def send(self, message):
        #~ print(message)
        try:
            returned = self.spi.xfer2(message)
            #~ print(message, returned) # prints [0,0,0] [0,0,0] - why??
            return returned
        except Exception as e:
            print ("Message send failure:", message)
            print(e)
            self.end()
    
    def Vout(self, dac, command, Vout, Vref = 2500, gain = 2):
        Din = self.Vout_to_bin(Vout = Vout, Vref = Vref, gain = gain)
        command = command.lower()
        dac = dac.lower()

        if dac in self.address_dict:
            address_bit = self.address_dict[dac]
        else:
            a = "DAC address not available.\nYou requested '" + dac + "' but only "+str(list(self.address_dict.keys()))+" are available."
            self.end(a = a)
            
        if command in self.command_dict:
            command_bit = self.command_dict[command]
        else:
            a = "Command not available.\nYou requested '" + command + "' but only " + str(list(self.command_dict.keys())) + " are available."
            self.end(a = a)
        
        message_to_send = str('00' + str(command_bit) + str(address_bit) + str(Din) + '0000')   
        #~ message_to_send = str('00' + str(command_bit) + str(address_bit) + '111111111111' + '0000')   
               
        #~ print("Message to send:", message_to_send, len(message_to_send), int(message_to_send[8:20],2)/4096*5000)         
        message_to_send = self.convertToThreeBytes(message_to_send)
        #~ print("Message to send after conversion to 3 bytes:", message_to_send, len(message_to_send))  
        command_response = self.send(message = message_to_send)
        #~ print(command_response, int(Din,2)/4096*5000)
        return Vout
        
    def gain(self, dac_a = 1, dac_b = 1):
        dac_a = str(dac_a)
        dac_b = str(dac_b)
        if dac_a in self.gain_dict:
            if dac_b in self.gain_dict:
                message_to_send = '00' + '000' + self.address_dict['gain'] + '00000000000000' + self.gain_dict[dac_b] + self.gain_dict[dac_a]
                message_to_send = self.convertToThreeBytes(message_to_send)
                command_response = self.send(message_to_send)
            else:
                a = "dac_b was not available.\nYou requested '" + dac_b + "' but only " + str(list(self.gain_dict.keys())) + " are available."
                self.end(a = a)
        else:
            a = "dac_a was not available.\nYou requested '" + dac_a + "' but only " + str(list(self.gain_dict.keys())) + " are available."
            self.end(a = a)        
        return int(dac_a), int(dac_b)
        
    def reset(self, software_reset = 'reset_dac'):
        software_reset = software_reset.lower()
        if software_reset in self.software_reset_dict:
            message_to_send = '00' + self.command_dict['software_reset'] + '000' + '000000000000000' + self.software_reset_dict[software_reset]
            message_to_send = self.convertToThreeBytes(message_to_send)
            command_response = self.send(message_to_send)
        else:
            a = "Reference not available.\nYou requested '" + software_reset + "' but only " + str(list(software_reset_dict.keys())) + " are available."
            self.end(a = a)
        return 0
    
    def ldac(self, ldac_a = 'synchronous', ldac_b = 'synchronous'):
        ldac_a = ldac_a.lower()
        ldac_b = ldac_b.lower()
        if ldac_a in self.ldac_dict:
            if ldac_b in self.ldac_dict:
                message_to_send = '00' + self.command_dict['ldac'] + '000' + '00000000000000' + self.ldac_dict[ldac_b] + self.ldac_dict[ldac_a]
                message_to_send = self.convertToThreeBytes(message_to_send)
                command_response = self.send(message_to_send)
            else:
                a = "LDAC selection not available.\nYou requested '" + ldac_b + "' but only " + str(list(ldac_dict.keys())) + " are available."
                self.end(a = a)
        else:
            a = "LDAC selection not available.\nYou requested '" + ldac_a + "' but only " + str(list(ldac_dict.keys())) + " are available."
            self.end(a = a)
        return 0

    def power(self, mode = 'power_up', dac = 'ab'):
        dac = dac.lower()
        dac_dict = {'a':'01', 'b':'10', 'ab':'11'}
        if mode in self.mode_dict:
            if dac in dac_dict:
                message_to_send = '00' + self.command_dict['power'] + '000' + '0000000000' + self.mode_dict[mode] + '00' + dac_dict[dac]
                message_to_send = self.convertToThreeBytes(message_to_send)
                command_response = self.send(message_to_send)
            else:
                a = "DAC not available.\nYou requested '" + dac + "' but only " + str(list(dac_dict.keys())) + " are available."
                self.end(a = a)
        else:
            a = "Mode not available.\nYou requested '" + mode + "' but only " + str(list(mode_dict.keys())) + " are available."
            self.end(a = a)
        return 0
        
    def reference(self, reference = 'internal'):
        reference = reference.lower()
        reference_dict = {'external': '0', 'internal':'1'}
        if reference in reference_dict:
            message_to_send = '00' + self.command_dict['reference'] + '000' + '000000000000000' + reference_dict[reference]
            message_to_send = self.convertToThreeBytes(message_to_send)
            command_response = self.send(message_to_send)
            if reference == 'internal': Vref = 2500
            else: Vref = 5000
            return Vref
        else:
            a = "Reference not available.\nYou requested '" + reference + "' but only " + str(list(reference_dict.keys())) + " are available."
            self.end(a = a)
        return 0
    
    def check_actual_sample_oscillation_rate(self, duration = 5, Vout = 1500, Vref = 2500, gain = 1):
        i = 0
        start_time = time.time()
        while time.time() - start_time < duration:
            Vout = self.Vout(dac = 'a', command = 'write_update', Vout = Vout, Vref = Vref, gain = gain)
            i += 1
            Vout = self.Vout(dac = 'a', command = 'write_update', Vout = 0, Vref = Vref, gain = gain)
            i += 1
        print("Number of iterations:", i)
        print("Duration (sec):", duration)
        print("Iterations per second:", i/duration)
        return 0
                
    def end(self, a = ''):
        self.spi.close()
        print("\nSPI closed. System exited.\n")
        sys.exit(a)

# operations below this line will not be used when imported as a module
def main():
    dac = DAC7562()
    dac.power(mode = 'power_up', dac = 'ab')
    dac.ldac(ldac_a = 'synchronous', ldac_b = 'synchronous')
    Vref = dac.reference(reference = 'internal')
    dac_a, dac_b = dac.gain(dac_a = 2, dac_b = 2) # does this do anything?
    #~ print(Vref, dac_a)
    Vout = dac.Vout(dac = 'a', command = 'write_update', Vout = 5000, Vref = Vref, gain = dac_a)
    #~ Vout = dac.Vout(dac = 'b', command = 'write_update', Vout = 5000, Vref = 2500, gain = dac_b)
    print(Vout)
    #~ Vout = dac.Vout(dac = 'a', command = 'write_update', Vout = 3000, Vref = Vref, gain = da)
    #~ dac.check_actual_sample_oscillation_rate(duration = 5, Vout = 1500, Vref = Vref, gain = dac_a)
    #~ print(Vout, "mV output set.")
    dac.end(a = 'Main program closed.')
            
if __name__ == '__main__':
    main()

