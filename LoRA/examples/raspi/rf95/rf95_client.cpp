// rf95_client.cpp
//
// Example program showing how to use RH_RF95 on Raspberry Pi
// Uses the bcm2835 library to access the GPIO pins to drive the RFM95 module
// Requires bcm2835 library to be already installed
// http://www.airspayce.com/mikem/bcm2835/
// Use the Makefile in this directory:
// cd example/raspi/rf95
// make
// sudo ./rf95_client
//
// Contributed by Charles-Henri Hallard based on sample RH_NRF24 by Mike Poublon
// Modified by Elecrow-keen

#include <bcm2835.h>
#include <stdio.h>
#include <signal.h>
#include <unistd.h>

#include <RH_RF69.h>
#include <RH_RF95.h>
#include <cstdlib> 
#include <ctime>
#include <iostream>
#include <fstream>
#include <string>
#include <stdlib.h>
#include <stdio.h>
#include <mysql/mysql.h>
#include <vector>
#include <sstream>
using namespace std;

#define BOARD_LORASPI

#include "../RasPiBoards.h"

// Our RFM95 Configuration 
#define RF_FREQUENCY  915.00
#define RF_NODE_ID    1
//#define RF_GATEWAY_ID 2

// Create an instance of a driver
RH_RF95 rf95(RF_CS_PIN, RF_IRQ_PIN);
//RH_RF95 rf95(RF_CS_PIN);

//Flag for Ctrl-C
volatile sig_atomic_t force_exit = false;

void sig_handler(int sig)
{
  printf("\n%s Break received, exiting!\n", __BASEFILE__);
  force_exit=true;
}

void storeData(uint8_t* buf,size_t lena, uint8_t from) {

    std::vector<uint8_t> buffer(buf, buf + lena);
    buffer.push_back('\0');
    std::string receivedData(reinterpret_cast<const char*>(buf), lena);

    std::cout << "Received Data: " << receivedData << std::endl;
    // Parse the received data string to extract individual data points
    std::istringstream ss(receivedData);
    std::vector<std::string> dataPoints;
    std::string token;
    while (std::getline(ss, token, ',')) {
        dataPoints.push_back(token);
    }

    std::cout << "Parsed Data Points: " << std::endl;
    for (const auto& point : dataPoints) {
        std::cout << point << std::endl;
    }
    // Ensure we have exactly 5 data points
    if (dataPoints.size() != 6) {
        std::cerr << "Error: Unexpected number of data points" << std::endl;
        return;
    }

    // Extract individual data points
    std::string date = dataPoints[0];
    std::string time = dataPoints[1];
    std::string latitude = dataPoints[2];
    std::string longitude = dataPoints[3];
    std::string speed = dataPoints[4];
    std::string id_node = dataPoints[5];

    // Connect to MySQL database
    MYSQL *conn = mysql_init(NULL);
    if (conn == NULL) {
        std::cerr << "Error initializing MySQL connection" << std::endl;
        return;
    }

    if (!mysql_real_connect(conn, "localhost", "root", "raspbian", "capstone", 0, NULL, 0)) {
        std::cerr << "Error connecting to MySQL: " << mysql_error(conn) << std::endl;
        mysql_close(conn);
        return;
    }

    // Prepare SQL query
    char query[500]; // Adjust size as needed
    //snprintf(query, sizeof(query), "INSERT INTO lora_test (number, node) VALUES ('%s', '%s')",
    snprintf(query, sizeof(query), "INSERT INTO gps_data (date, time, node, latitude, longitude, speed) VALUES ('%s', '%s', '%s', '%s', '%s', '%s')",
            //date.c_str(), time.c_str());
            date.c_str(), time.c_str(), id_node.c_str(), latitude.c_str(), longitude.c_str(), speed.c_str());

    // Execute SQL query
    if (mysql_query(conn, query)) {
        std::cerr << "Error executing SQL query: " << mysql_error(conn) << std::endl;
        mysql_close(conn);
        return;
    }

    printf("gps data from %s data stored successfully",  id_node);

    // Close MySQL connection
    mysql_close(conn);
}

//Main Function
int main (int argc, const char* argv[] )
{
  std::string line;
  std::string new1;
  static unsigned long last_millis;
  long lastSendTime = 0;
  int interval = 500;
  srand(time(NULL));

  unsigned long led_blink = 0;
  
  signal(SIGINT, sig_handler);
  printf( "%s\n", __BASEFILE__);

  if (!bcm2835_init()) {
    fprintf( stderr, "%s bcm2835_init() Failed\n\n", __BASEFILE__ );
    return 1;
  }
  
  printf( "RF95 CS=GPIO%d", RF_CS_PIN);

#ifdef RF_LED_PIN
  pinMode(RF_LED_PIN, OUTPUT);
  digitalWrite(RF_LED_PIN, HIGH );
#endif

#ifdef RF_IRQ_PIN
  printf( ", IRQ=GPIO%d", RF_IRQ_PIN );
  // IRQ Pin input/pull down
  pinMode(RF_IRQ_PIN, INPUT);
  bcm2835_gpio_set_pud(RF_IRQ_PIN, BCM2835_GPIO_PUD_DOWN);
  // Now we can enable Rising edge detection
  bcm2835_gpio_ren(RF_IRQ_PIN);
#endif
  
#ifdef RF_RST_PIN
  printf( ", RST=GPIO%d", RF_RST_PIN );
  // Pulse a reset on module
  pinMode(RF_RST_PIN, OUTPUT);
  digitalWrite(RF_RST_PIN, LOW );
  bcm2835_delay(150);
  digitalWrite(RF_RST_PIN, HIGH );
  bcm2835_delay(100);
#endif

#ifdef RF_LED_PIN
  printf( ", LED=GPIO%d", RF_LED_PIN );
  digitalWrite(RF_LED_PIN, LOW );
#endif

  if (!rf95.init()) {
    fprintf( stderr, "\nRF95 module init failed, Please verify wiring/module\n" );
  } else {
    // Defaults after init are 915.0MHz, 13dBm, Bw = 125 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on

    // The default transmitter power is 13dBm, using PA_BOOST.
    // If you are using RFM95/96/97/98 modules which uses the PA_BOOST transmitter pin, then 
    // you can set transmitter powers from 5 to 23 dBm:
    //  driver.setTxPower(23, false);
    // If you are using Modtronix inAir4 or inAir9,or any other module which uses the
    // transmitter RFO pins and not the PA_BOOST pins
    // then you can configure the power transmitter power for -1 to 14 dBm and with useRFO true. 
    // Failure to do that will result in extremely low transmit powers.
    // rf95.setTxPower(14, true);


    // RF95 Modules don't have RFO pin connected, so just use PA_BOOST
    // check your country max power useable, in EU it's +14dB
    rf95.setTxPower(14, false);

    // You can optionally require this module to wait until Channel Activity
    // Detection shows no activity on the channel before transmitting by setting
    // the CAD timeout to non-zero:
    //rf95.setCADTimeout(10000);

    // Adjust Frequency
    rf95.setFrequency(RF_FREQUENCY);
    
    // If we need to send something
   rf95.setThisAddress(RF_NODE_ID);
   rf95.setHeaderFrom(RF_NODE_ID);
    
    // Be sure to grab all node packet 
    // we're sniffing to display, it's a demo
    rf95.setPromiscuous(true);

    // We're ready to listen for incoming message
    rf95.setModeRx();

   // printf( " OK NodeID=%d @ %3.2fMHz\n", RF_NODE_ID, RF_FREQUENCY );
    printf( "Listening packet...\n" );

    //Begin the main body of code
    while (!force_exit) {
      
      #ifdef RF_LED_PIN
        digitalWrite(RF_LED_PIN, LOW);
	    #endif
      
      // Send a message to rf95_server
      if (millis() - lastSendTime > interval) {
        // Buka file gps.txt untuk mengambil data gps yang akan dikirim
        ifstream myfile("/home/pi/gps.txt");
        while (getline (myfile,line)){
         new1=line;
        }
        new1 += ",1";
        myfile.close();
        
        // ifstream myfile("/home/pi/test.txt");
        // while (getline (myfile,line)){
        //  new1=line;
        // }
        // new1 += ",1";
        // myfile.close();

        const uint8_t *data = reinterpret_cast<const uint8_t*>(new1.c_str());
        uint8_t len = new1.length();
        printf("Sending %02d bytes  : ", len);
        cout <<data<< endl;
        printf("\n" );
        #ifdef RF_LED_PIN
        	digitalWrite(RF_LED_PIN, HIGH);
	      #endif
        rf95.send(data,len);
        rf95.waitPacketSent();
        
        lastSendTime = millis();
        interval = 500 + rand() % 500;
      }

      // Now wait for a reply
      uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
      uint8_t lena  = sizeof(buf);
      uint8_t from = rf95.headerFrom();
      // uint8_t id   = rf95.headerId();
      // uint8_t flags= rf95.headerFlags();;
      int8_t rssi  = rf95.lastRssi();

      if (rf95.recv(buf, &lena)) {
        printf("Received packet[%02d] bytes from node #%d %ddB: ", lena, from, rssi);
        printbuffer(buf, lena);
        printf("\n" );
        storeData(buf,lena, from);
      }

        // if (rf95.waitAvailableTimeout(500)) { 
        //   // Should be a reply message for us now   
        //   if (rf95.recv(buf, &lena)) {
        //     printf("Received packet[%02d] bytes from node #%d %ddB: ", lena, from, rssi);
        //     printbuffer(buf, lena);
        //     printf("\n" );
        //     storeData(buf,lena, from);
        //   } else {
        //     printf("recv failed");
        //   }
        // } else {
        //   printf("No reply\n");
        // }
      //printf("\n");

      // Let OS doing other tasks
      // For timed critical appliation you can reduce or delete
      // this delay, but this will charge CPU usage, take care and monitor
      bcm2835_delay(20);
    }
  }

  printf( "\n%s Ending\n", __BASEFILE__ );
  bcm2835_close();
  return 0;
}
