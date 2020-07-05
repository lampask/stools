import win32gui
import win32process
import cv2
import ctypes
import time
import math
import click
import numpy as np
from pywinauto.application import Application
from pywinauto.keyboard import send_keys
from PIL import ImageGrab
import threading
from cmd import Cmd

DISPLAY = True
FOCUS_CHECK = False
FOCUS_RATE = 100 # frames
BAR_HAIGHT = 30
EXIT = False

timer = time.time()
frames = 0

@click.command()
@click.option('--display', '-D', is_flag=True)
def main(display):
    global DISPLAY
    DISPLAY = display
    click.echo("Welcome to the STO automation tool ✨")
    loop = threading.Thread(name="MainLoop", target=WatchFrames)
    loop.start()
    Shell().cmdloop()

# Command loop

class Shell(Cmd):
    global timer, frames
    prompt = 'sTools> '
    intro = "Type ? to see usable commands"

    def do_exit(self, inp):
        global EXIT
        EXIT = True
        print("Bye bye fnuk")
        return True
 
    def do_add(self, inp):
        print("Adding '{}'".format(inp))

    def do_framerate(self, inp):
        print (math.ceil(1/(time.time()-timer)))
    
    def do_toggledisplay(self, inp):
        global DISPLAY
        DISPLAY = not DISPLAY
    
    def emptyline(self):
        pass

# Main loop
hwnd = win32gui.FindWindow(None, 'Star Trek Online')
threadid, pid = win32process.GetWindowThreadProcessId(hwnd)
app = Application().connect(process=pid, path=r"E:\Steam\steamapps\common\Star Trek Online")
ctypes.windll.user32.SetProcessDPIAware()


def WatchFrames():
    global timer, frames, DISPLAY
    while(True):
        # IMAGE CAPTURE
        window_object = win32gui.FindWindow(None, 'Star Trek Online')
        rect = win32gui.GetWindowRect(window_object)
        screen = np.array(ImageGrab.grab(bbox=rect), dtype=np.uint8)
        
        # IMAGE PROCESSING
        
        # IMAGE DISPLAY
        if DISPLAY: 
            # DRAW CUSTOM FUNCTIONS
            cv2.rectangle(screen, (0, 0), (rect[2], BAR_HAIGHT), (255,255,255), -1)
            cv2.putText(screen,f'FPS: {math.ceil(1/(time.time()-timer))}', (10,20), cv2.FONT_HERSHEY_PLAIN, 1, (0,0,0), 1)
            # IMG
            cv2.imshow('REEEE', cv2.cvtColor(screen, cv2.COLOR_BGR2RGB))
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                DISPLAY = False
            if FOCUS_CHECK: frames += 1
        else:
            cv2.destroyAllWindows()
        if EXIT:
            cv2.destroyAllWindows()
            break
        frames += 1
        timer = time.time()

if __name__ == "__main__":
    main()
