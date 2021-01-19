#!/usr/bin/env python3
from threading import Thread
#import time
import socket
import select
from tkinter import *
#import tkinter as tk
import tkinter
import tkinter.font as tkFont

# ENKEL OP DE RASPBERRY NATUURLIJK
#import RPi.GPIO as GPIO
#import smbus
#PIN = 7

JULIET_IP = "10.10.0.1"
MC_IP = "10.10.0.2"
UDP_PORT = 11991

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', UDP_PORT))

overridePkt =  bytearray([0x75, 0x4a, 0x6f, 0x52, 0xff, 0xff,  0x14, 0x00, 0x04, 0x00, 0x01, 0x00, 0x00,   0x03,   0x00, 0x00, 0x00, 0x00,   0x00, 0x00])
# bijv. verlichting binnenin aanzetten: [0x75, 0x4a, 0x6f, 0x52, 0xff, 0xff,  0x14, 0x00, 0x04, 0x00, 0x01, 0x00, 0x00,   0x05,   0xff, 0xff, 0xff, 0xff,   0x00, 0x00])
#de eerste 13 bytes zijn steeds hetzelfde : 0x75, 0x4a, 0x6f, 0x52, 0xff, 0xff,  0x14, 0x00, 0x04, 0x00, 0x01, 0x00, 0x00
#byte 14 bevat het nummer van de IO die je aanstuurt
#de bytes 15, 16, 17 en 18 bevatten de waarde die je uitstuurt (byte 15 = LSB; byte 18 = MSB) 
#op plaats 19 en 20 twee nul-bytes

getValuePkt = bytearray([0x75, 0x4a, 0x6f, 0x52, 0xff, 0xff,  0x0f, 0x00, 0x04, 0x03,   0x00,   0x00, 0x00, 0x00, 0x00])  # uJoR.. len(2 bytes=15) BCG=4 IC_GetValue=3 zone(1 byte=0) id(4 bytes)
#de eerste 10 bytes zijn steeds hetzelfde: 0x75, 0x4a, 0x6f, 0x52, 0xff, 0xff,  0x0f, 0x00, 0x04, 0x03
#byte 11 is de zone (standaard op nul)
#de bytes 12, 13, 14 en 15 bevatten het nummer van de IO (byte 12 is LSB; byte 15 is MSB)

# LEDje aan GPIO pin 7 van Raspberry aan/uit
#GPIO.setmode(GPIO.BOARD)
##GPIO.setmode(GPIO.BCM)
#GPIO.setup(PIN, GPIO.OUT)
#GPIO.output(PIN, GPIO.LOW)

# via de I2C-bus van de Raspberry babbelen
#bus = smbus.SMBus(1) # pin 3 (SDA) and 5 (SCL) on RPI4 pin header
#address = 9

# verlichting binnenin uitschakelen
lamp = 0 #lamp is off

win = tkinter.Tk()

myFont = tkFont.Font(family = 'Helvetica', size = 16, weight = 'bold')

# Raspberry only: LEDje aan GPIO omschakelen en via I2C pakketje versturen
# ik heb dit gebruikt om de Arduino Mega (die onder mijn grote test-printplaat hangt) commando's te sturen via I2C vanuit een Python programma op mijn RPi
# zo had ik dus een Raspberry met een (of meerdere) zeer grote IO-kaart(en) er aan
#def ledToggle():
#        print("LED button pressed")
#        if GPIO.input(PIN) :
#                GPIO.output(PIN, GPIO.LOW)
#                ledButton["text"] = "uit"
#                bus.write_byte(address, 50)
#        else:
#                GPIO.output(PIN, GPIO.HIGH)
#                ledButton["text"] = "aan"
#                bus.write_byte(address, 53)

# de verlichting binnenin omschakelen
def lampToggle():
        global lamp
        print("lamp button pressed")
        if lamp == 1 :
                lampButton["text"] = "uit"
                sendOverride(5, 0x00000000) #switch on/off output 5 
                lamp = 0
        else:
                lampButton["text"] = "aan"
                sendOverride(5, 0xffffffff) #switch on/off output 5 
                lamp = 1

# om "override" UDP-pakketten naar Juliet te sturen
def sendOverride(IOnumber, IOvalue):
        #print("Sending override")
        overridePkt[13] = IOnumber
        overridePkt[14] = IOvalue & 0xff
        overridePkt[15] = (IOvalue & 0xff00) >> 8
        overridePkt[16] = (IOvalue & 0xff0000) >> 16
        overridePkt[17] = (IOvalue & 0xff000000) >> 24
        sock.sendto(overridePkt, (JULIET_IP, UDP_PORT))
        #print(len(overridePkt))

# om de RGB-kleurtjes voor de statuslamp te verzenden
def sendColors():
        red = sliderR.get()
        green = sliderG.get()
        blue = sliderB.get()
        print('Sending RGB colors(', red, green, blue,')')
        sendOverride(2, red)
        sendOverride(3, green)
        sendOverride(4, blue)

# om UDP-pakketten van Juliet te ontvangen
def receiveMessages():
        print("Receiving UDP packets")
        data, addr = sock.recvfrom(1024)
        print("received packet: ", data)
        win.after(1000, receiveMessages)

# om bijvoorbeeld de waarde van een ingang van Juliet op te vragen
def getValue(IOnumber):
        getValuePkt[11] = IOnumber & 0xff
        getValuePkt[12] = (IOnumber & 0xff00) >> 8
        getValuePkt[13] = (IOnumber & 0xff0000) >> 16
        getValuePkt[14] = (IOnumber & 0xff000000) >> 24

        try:
            print('Request sent')
            sent = sock.sendto(getValuePkt, (JULIET_IP, UDP_PORT))
            sock.settimeout(3.5)

            ready = select.select([sock], [], [], 3) # timeout_in_seconds
            if ready[0]:
                data = sock.recv(1024)
                print(data) #eerste 10 bytes zijn altijd hetzelfde, vervolgens 4 keer 0x00, dan 2 bytes die meetwaarde bevatten, tot slot nog twee nul-bytes
                #print(len(data))
            #data, server = sock.recvfrom(1024)
            #print('received {!r}'.format(data))
        finally:
            print('Voila')
            #sock.close()

def getAnalogValues():
        getValue(0x00) # temperature
        #getValue(0x04) # CO2 (0..5V)
        #getValue(0x06) # hum (0..1V)

def exitProgram():
        print("Exit Button pressed")
        #GPIO.cleanup()
        win.quit()


win.title("OX2020 test")
win.geometry('800x600')

#ledButton = Button(win, text = "toggle GPIO", font = myFont, command = ledToggle, height = 1, width = 16)
#ledButton.pack()
lampButton = Button(win, text = "toggle lamp", font = myFont, command = lampToggle, height = 1, width = 16)
lampButton.pack()

colorButton = Button(win, text = "send colors", font = myFont, command = sendColors, height = 1, width = 16)
colorButton.pack()

#sliderR = Tkinter.Scale(win, from_ = 0, to = 1000, orient = Tkinter.HORIZONTAL)
sliderR = tkinter.Scale(win, from_ = 0, to = 1000, orient = tkinter.HORIZONTAL)
sliderR.set(200)
sliderR.pack()
sliderG = tkinter.Scale(win, from_ = 0, to = 1000, orient = tkinter.HORIZONTAL)
sliderG.set(250)
sliderG.pack()
sliderB = tkinter.Scale(win, from_ = 0, to = 1000, orient = tkinter.HORIZONTAL)
sliderB.set(300)
sliderB.pack()

anaButton = Button(win, text = "get analog values", font = myFont, command = getAnalogValues, height = 1, width = 16)
anaButton.pack()

exitButton = Button(win, text = "exit", font = myFont, command = exitProgram, height = 1, width = 16)
exitButton.pack(side = BOTTOM)

#win.after(5000, receiveMessages)
mainloop()
