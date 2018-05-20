#!/usr/bin/python
import serial
import time
#import keyboard

port = "/dev/serial0"
baudrate=9600
CENTRE_x = int(60)
CENTRE_y = int(150)
SUCCESSFUL_EXCECUTION = 1
DEFAULT_MODE = 1
DISPLAY_ON = True # display the stages in plant recognition on terminal

ser = serial.Serial(port, baudrate, timeout=0.1) # Serial comms arduino <--> Raspi
pan_pos = CENTRE_x
tilt_pos = CENTRE_y
list_modes = {1 : "<Demo Mode>", 2: "<Pump Mode>", 3: "<Vision Mode>"}
LOG = {"Plant": None, "Stage": None, "used_fertilizer": None,
                            "Tank_Level": 1500} # format of logging message

# Read serial buffer until empty
def read_until_empty():
    c = ser.read()
    word = b''
    while (c != b''):
        word += c
        c = ser.read()
    return word

# Check if string is a number
def is_number(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

# Function tells arduino to pump specified amount of liquid
def pump_liquid(amount_ml):
    message = "Pump:fertilize:" + amount_ml + " ml;"
    ser.write(message.encode(encoding='UTF-8'))

# In demo mode rover will fertilizer both sides of the garden row
def fertilize_row():
    pass

# Control Movements of fertilizer system on rover
class SystemControl:
    # Control rover movements using arrow keys
    def move_rover(cmd, param):
        if cmd is "forward":
            ser.write(b"Move:forward:10 cm;")

        elif cmd is "backward":
            ser.write(b"Move:backward:10 cm;")

        elif cmd is "turn" and param is"left":
            ser.write(b"Move:turn:left;")

        else:
            ser.write(b"Move:turn:right;")

    # Move pump with right arrow
    def move_pump_right():
        global pan_pos
        if pan_pos >= 0:
            pan_pos -= 2
        message = "PanTilt:angle:" + str(pan_pos) + ',' + str(tilt_pos) + ';'
        ser.write(message.encode(encoding='UTF-8'))

    # Move pump with left arrow
    def move_pump_left():
        global pan_pos
        if pan_pos <= 140 :
           pan_pos += 2
        message = "PanTilt:angle:" + str(pan_pos) + ',' + str(tilt_pos) + ';'
        ser.write(message.encode(encoding='UTF-8'))

    # Move pump with down arrow
    def move_pump_down():
        global tilt_pos
        if tilt_pos >= 110:
            tilt_pos -= 2
        message = "PanTilt:angle:" + str(pan_pos) + ',' + str(tilt_pos) + ';'
        ser.write(message.encode(encoding='UTF-8'))

    # Move pump with up arrow
    def move_pump_up():
        global tilt_pos
        if tilt_pos <= 175:
            tilt_pos += 2
        message = "PanTilt:angle:" + str(pan_pos) + ',' + str(tilt_pos) + ';'
        ser.write(message.encode(encoding='UTF-8'))

# Process arrow key presses from terminal to move peripherals
def process_system_movements(direction, system, current_mode):
    # Demo Mode
    if current_mode is list_modes[1]:
        if direction is 'up': # Up arrow = forward
            system.move_rover('forward', None)

        elif direction is 'down': # Down arrow = backward
            system.move_rover('backward', None)

        else:
            # Turn in specified direction
            system.move_rover('turn', direction)

    # Pump or Vision Mode
elif current_mode is list_modes[2] or current_mode is list_modes[3]:
        if direction is 'left':
            system.move_pump_left()

        elif direction is 'right':
            system.move_pump_left()

        elif direction is 'up':
            system.move_pump_down() # Tilt is reversed

        elif direction is 'down':
            system.move_pump_up()

# Process typed user input commands from terminal
def process_user_input(cnn, newline, current_mode):
    msg = new_line.split(' ')
    #Check if Mode == Demo Mode and command is valid
    if current_mode == list_modes.get(DEFAULT_MODE):
        if msg[0] == 'Fertilize' and msg[1] == 'Row':
            fertilize_row()
        else:
            return "Invalid command! Use cmd[Fertilize Row]"
    #Check if Mode == Pump Mode and command is valid
    elif current_mode == list_modes.get(2):
        if is_number(msg[0]) and msg[1] == "ml":
            pump_liquid(msg[0])
        else:
            return "Invalid command! Must have formart e.g. [10 ml]"
    # Check if Mode ==  Vision Mode
    else:
        if new_line == "detect":
            predictions = [0,0]
            # Accept detection with a score above 80% accuracy
            while predictions[1] < 0.80:
                image_array = cnn.prepare_images(from_camera=True) # Get piCam image as numpy array
                predictions = cnn.get_predictions(image_array,
                                                 data_type="from_directory",
                                                 display=False)
                time.sleep(0.3) # check 3 frames per second
            return "Predicted label - %s, Score: [%5f]" % (predictions[0],
                                                          predictions[1])

        else:
            return "Invalid command! Use [detect]"
