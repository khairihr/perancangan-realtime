// spi_scan.cpp
//
// Example program showing how to detect multiple module RH_RF69/RH_RF95 on Raspberry Pi
// Requires pigpio library to be already installed
// Use the Makefile in this directory:
// cd example/raspi/spi_scan
// make
// sudo ./spi_scan
//
// Will check for RFM92/95/96/98 or RFM69/RFM69HCW/RFM69W modules on SPI BUS
// scan with CS = GPIO6, CE0, CE1 and GPIO26
// So it should detect the following boards
// LoRasPi board => https://github.com/hallard/LoRasPI
// RasPI Lora Gateway Board iC880A and LinkLab Lora => https://github.com/ch2i/iC880A-Raspberry-PI
// Raspberri PI Lora Gateway => https://github.com/hallard/RPI-Lora-Gateway
// Dragino Raspberry PI hat => https://github.com/dragino/Lora
//
// Contributed by Charles-Henri Hallard (hallard.me)

#include <pigpio.h>
#include <stdio.h>

#include "RH_RF69.h"
#include "RH_RF95.h"

uint8_t readRegister(uint8_t cs_pin, uint8_t addr)
{
    char spibuf[2];
    spibuf[0] = addr & 0x7F;
    spibuf[1] = 0x00;

    gpioWrite(cs_pin, 0);
    spiXfer(0, spibuf, spibuf, sizeof(spibuf));
    gpioWrite(cs_pin, 1);
    return spibuf[1];
}

void getModuleName(uint8_t version)
{ 
    printf(" => ");
    if (version == 0x00 || version == 0xFF)
        printf("Nothing!\n");
    else if (version == 0x12)
        printf("SX1276 RF95/96");
    else if (version == 0x22)
        printf("SX1272 RF92");
    else if (version == 0x24)
        printf("SX1231 RFM69");
    else
        printf("Unknown");

    if (version != 0x00 && version != 0xFF)
        printf(" (V=0x%02X)\n", version);
}

void readModuleVersion(uint8_t cs_pin)
{
    printf("Checking register(0x42) with CS=GPIO%02d", cs_pin);
    getModuleName(readRegister(cs_pin, 0x42));

    printf("Checking register(0x10) with CS=GPIO%02d", cs_pin);
    getModuleName(readRegister(cs_pin, 0x10));
}

int main(int argc, char **argv)
{
    if (gpioInitialise() < 0) {
        printf("pigpio initialization failed. Are you running as root?\n");
    } else {
        // List of all CS lines where modules can be connected
        // GPIO6, GPIO8/CE0, GPIO7/CE1, GPIO26
        uint8_t CS_pins[] = {6, 7, 8, 26};
        uint8_t i;

        // Initialize SPI
        int spi_handle = spiOpen(0, 500000, 0);  // Open SPI channel 0 at 500 kHz, mode 0

        if (spi_handle < 0) {
            printf("spiOpen failed\n");
            gpioTerminate();
            return 1;
        }

        // Drive all CS lines as output and set them High to avoid any conflict
        for (i = 0; i < sizeof(CS_pins); i++) {
            gpioSetMode(CS_pins[i], PI_OUTPUT);
            gpioWrite(CS_pins[i], 1);
        }

        // Now try to detect all modules
        for (i = 0; i < sizeof(CS_pins); i++) {
            readModuleVersion(CS_pins[i]);
        }

        spiClose(spi_handle);
        gpioTerminate();
    }

    return 0;
}
