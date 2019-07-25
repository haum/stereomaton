#!/usr/bin/env python3

import cairo
import evdev
from random import choice
from time import sleep

class CairoFB:
    def __init__(self, fb='/dev/fb1', sz=(480, 320)):
        from mmap import mmap
        self.fd = open(fb, "r+")
        self.sz = sz
        self.map = mmap(self.fd.fileno(), self.sz[0] * self.sz[1] * 2)
        self.cro = cairo.Context(cairo.ImageSurface.create_for_data(self.map, cairo.FORMAT_RGB16_565, self.sz[0], self.sz[1]))

    def __del__(self):
        self.cro.set_source_rgb(0, 0, 0)
        self.cro.paint()
        self.map.close()
        self.fd.close()

    def cr(self):
        return self.cro

class ClickListener:
    def __init__(self, cb, verbose=False):
        self.dev = evdev.InputDevice('/dev/input/event0')
        self.cb = cb
        self.verbose = verbose
        self.x = 0
        self.y = 0

    def loop(self):
        for event in self.dev.read_loop():
            if self.verbose:
                print(evdev.categorize(event))
            if event.type == evdev.ecodes.EV_ABS:
                if event.code == evdev.ecodes.ABS_X:
                    self.x = event.value
                elif event.code == evdev.ecodes.ABS_Y:
                    self.y = event.value
            elif event.type == evdev.ecodes.EV_KEY and event.code == evdev.ecodes.BTN_TOUCH and event.value == 0:
                x = int((4096 - self.y) / 4096.0 * 480)
                y = int(self.x / 4096.0 * 320)
                if self.cb(x, y):
                    try:
                        for event in self.dev.read():
                            pass # Flush
                    except BlockingIOError:
                        pass

"""Clear screen"""
def clear(cr):
  cr.set_source_rgb(0, 0, 0)
  cr.paint()

"""Display code explaination"""
def text_code_explaination(cr):
  cr.set_source_rgb(1, 1, 1)
  cr.set_font_size(20)
  cr.move_to(15, 30)
  cr.show_text("Code pour récupérer les photos :")

"""Display actual code"""
def text_code(cr, code):
  cr.set_source_rgb(0, 0, 0)
  cr.rectangle(40, 40, 400, 50)
  cr.fill()
  cr.set_source_rgb(1, 0.8, 0)
  cr.set_font_size(35)
  cr.move_to(125, 80)
  cr.show_text(code)

"""Generate code"""
gen_code_phonems = ('BA', 'DE', 'FA', 'KA', 'LE', 'LI', 'MI', 'NO', 'NU', 'PI', 'PO', 'RI', 'TA', 'TE', 'VO', 'VU', 'VE', 'ZO')
def gen_code():
  return ''.join(choice(gen_code_phonems) for _ in range(4))

"""Display buttons"""
def draw_buttons(cr, photos=0, active=True):
  cr.set_source_rgb(0, 0, 0)
  cr.rectangle(0, 100, 480, 220)
  cr.fill()
  if active:
      cr.set_source_rgb(0, 0.8, 1)
  else:
      cr.set_source_rgb(0.5, 0.5, 0.5)
  cr.rectangle(10, 110, 220, 200)
  cr.stroke()
  cr.rectangle(250, 110, 220, 200)
  cr.stroke()
  cr.set_font_size(35)
  cr.move_to(50, 200)
  cr.show_text('Change')
  cr.move_to(80, 240)
  cr.show_text('code')
  cr.move_to(310, 220)
  cr.show_text('Photo')
  if photos:
      cr.set_font_size(20)
      cr.move_to(260, 300)
      cr.show_text(str(photos))

"""Display countdown"""
def draw_countdown(cr, nb):
  cr.set_source_rgb(0, 0, 0)
  cr.rectangle(0, 100, 480, 220)
  cr.fill()
  cr.set_source_rgb(1, 0, 0.8)
  cr.set_font_size(160)
  if nb > 0:
      cr.move_to(190, 250)
      cr.show_text(str(nb))
  else:
      cr.move_to(150, 250)
      cr.show_text(':-)')

################################################################################

MODE_MENU = 0
MODE_PHOTO = 1

mode = MODE_MENU
photo_nb=0
cfb = CairoFB()
cr = cfb.cr()
clear(cr)
text_code_explaination(cr)
code = gen_code()
text_code(cr, code)
draw_buttons(cr)

def photo(code, nb):
    filename = '{}_{:03d}.jpg'.format(code.lower(), nb)
    print('Photo!', filename)

def click_handler(x, y):
    global mode, photo_nb, code
    if mode == MODE_PHOTO:
        draw_buttons(cr, photo_nb, False)
        sleep(2)
        draw_buttons(cr, photo_nb, True)
        mode = MODE_MENU
    elif mode == MODE_MENU:
        if y > 100:
            if x < 230:
                code = gen_code()
                text_code(cr, code)
                photo_nb=0
                draw_buttons(cr, photo_nb, True)
            elif x > 250:
                mode = MODE_PHOTO
                for i in range(5, -1, -1):
                    draw_countdown(cr, i)
                    sleep(1)
                photo_nb += 1
                photo(code, photo_nb)
    return True

cl = ClickListener(click_handler)
cl.loop()
