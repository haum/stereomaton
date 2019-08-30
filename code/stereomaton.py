#!/usr/bin/env python3

import os, shutil
import subprocess, signal
import cairo
import evdev
import cv2
from random import choice
from time import sleep
import numpy as np

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

"""Apply Simplest Color Balance algorithm
Reimplemented based on https://gist.github.com/DavidYKay/9dad6c4ab0d8d7dbf3dc"""
def simplest_cb(img, percent):
    out_channels = []
    channels = cv2.split(img)
    totalstop = channels[0].shape[0] * channels[0].shape[1] * percent / 200.0
    for channel in channels:
        bc = np.bincount(channel.ravel(), minlength=256)
        lv = np.searchsorted(np.cumsum(bc), totalstop)
        hv = 255-np.searchsorted(np.cumsum(bc[::-1]), totalstop)
        out_channels.append(cv2.LUT(channel, np.array(tuple(0 if i < lv else 255 if i > hv else round((i-lv)/(hv-lv)*255) for i in np.arange(0, 256)), dtype="uint8")))
    return cv2.merge(out_channels)

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
  cr.move_to((480-cr.text_extents(code).width)/2, 80)
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
  txt = 'Change'
  cr.move_to((220-cr.text_extents(txt).width)/2+10, (200+cr.text_extents(txt).height)/2+110-25)
  cr.show_text(txt)
  txt = 'code'
  cr.move_to((220-cr.text_extents(txt).width)/2+10, (200+3*cr.text_extents(txt).height)/2+110-15)
  cr.show_text(txt)
  cr.move_to(310, 220)
  txt = 'Photo'
  cr.move_to((220-cr.text_extents(txt).width)/2+250, (200+cr.text_extents(txt).height)/2+110-5)
  cr.show_text(txt)
  if photos:
      cr.set_font_size(20)
      txt = str(photos)
      cr.move_to((220-cr.text_extents(txt).width)/2+250, 270)
      cr.show_text(txt)

"""Display countdown"""
def draw_countdown(cr, nb):
  cr.set_source_rgb(0, 0, 0)
  cr.rectangle(0, 100, 480, 220)
  cr.fill()
  cr.set_source_rgb(1, 0, 0.8)
  cr.set_font_size(160)
  txt = str(nb)
  if nb <= 0:
      if nb == 0:
          txt = ':-)'
      elif nb == -1:
          txt = '.'
      elif nb == -2:
          txt = '..'
      elif nb == -3:
          txt = '...'
  cr.move_to((480-cr.text_extents(txt).width)/2, 250)
  cr.show_text(txt)

################################################################################

MODE_MENU = 0
MODE_PHOTO = 1

mode = MODE_MENU
savepath = '/media/STEREOMATON/'
photo_nb=0
cfb = CairoFB()
cr = cfb.cr()
raspistill = None

hpar=30
vpar=82

def gen_code_check():
    while True:
        newcode = gen_code()
        if not os.path.exists(savepath+newcode+'_001.jpg'):
            return newcode

code = gen_code_check()

def init_screen(cr, btn=True):
    clear(cr)
    text_code_explaination(cr)
    text_code(cr, code)
    draw_buttons(cr, photo_nb, btn)

def shot():
    if os.path.isfile('/tmp/shot.jpg'):
        os.remove('/tmp/shot.jpg')
    raspistill.send_signal(signal.SIGUSR1)
    for _ in range(10):
        sleep(0.1)
        if os.path.isfile('/tmp/shot.jpg'):
            break

def photo_compute(code, nb):
    def nsz(sz, h):
        return (int(sz[0]/sz[1]*h), h)
    filename = '{}_{:03d}.jpg'.format(code.lower(), nb)
    thumbname = '{}_{:03d}_thumb.jpg'.format(code.lower(), nb)
    if not os.path.isdir(savepath):
        os.makedirs(savepath)
    if os.path.isfile('/tmp/shot.jpg'):
        draw_countdown(cr, -3)
        img = cv2.imread('/tmp/shot.jpg')
        imgl = img[:, 0:int(img.shape[1]/2)]
        imgr = img[:, int(img.shape[1]/2):]

        sz = (2500, 1853)
        Hl = np.array((( 9.90540375e-01, -1.57071139e-02, -5.17682426e+01),
                       ( 6.88042594e-04,  9.78034960e-01, -1.05711222e+01),
                       ( 8.08043438e-07, -1.27680590e-05,  1.00000000e+00)))
        Hr = np.array((( 1.00131686e+00,  2.92492676e-03, -9.97647095e+00),
                       (-2.92492676e-03,  1.00131686e+00, -7.91296692e+01),
                       ( 0.00000000e+00,  0.00000000e+00,  1.00000000e+00)))

        imglc = cv2.warpPerspective(imgl, Hl, sz)
        imgrc = cv2.warpPerspective(imgr, Hr, sz)

        imglc = cv2.resize(imglc, nsz(sz, 1080))
        imgrc = cv2.resize(imgrc, nsz(sz, 1080))

        draw_countdown(cr, -2)
        imglc = simplest_cb(imglc, 1)
        imgrc = simplest_cb(imgrc, 1)

        draw_countdown(cr, -1)
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(64, 64))
        labl = cv2.cvtColor(imglc, cv2.COLOR_BGR2LAB)
        labr = cv2.cvtColor(imgrc, cv2.COLOR_BGR2LAB)
        labl[:,0] = clahe.apply(labl[:,0])
        labr[:,0] = clahe.apply(labr[:,0])
        imglc = cv2.cvtColor(labl, cv2.COLOR_LAB2BGR)
        imgrc = cv2.cvtColor(labr, cv2.COLOR_LAB2BGR)

        cv2.imwrite(savepath+filename, np.hstack((imglc, imgrc)))

        thumb = cv2.resize(imglc, nsz(sz, 480))
        cv2.imwrite('/tmp/thumb.jpg', thumb)

        thumb = cv2.resize(thumb, nsz(sz, 240))
        cv2.imwrite(savepath+thumbname, thumb)

        shutil.move('/tmp/shot.jpg', '/tmp/oldshot.jpg')
    with open(savepath+code.lower()+'.json', 'w') as f:
        f.write('{"nb": ' + str(nb) + '}')
    print('Photo!', filename)
    subprocess.run('fbi /tmp/thumb.jpg -d /dev/fb1 -T 1 --noverbose -a'.split(' '))

def click_handler(x, y):
    global mode, photo_nb, code, raspistill
    if mode == MODE_PHOTO:
        init_screen(cr, False)
        sleep(2)
        draw_buttons(cr, photo_nb, True)
        mode = MODE_MENU
    elif mode == MODE_MENU:
        if y > 100:
            if x < 230:
                code = gen_code_check()
                text_code(cr, code)
                photo_nb=0
                draw_buttons(cr, photo_nb, True)
            elif x > 250:
                mode = MODE_PHOTO
                subprocess.run(['killall', 'raspivid'])
                raspistill = subprocess.Popen('raspistill -n -s -t 0 -3d sbs -vf -hf -w 5184 -h 1944 -o /tmp/shot.jpg'.split(' '))
                for i in range(5, -1, -1):
                    draw_countdown(cr, i)
                    if i != 0:
                        sleep(1)
                photo_nb += 1
                shot()
                raspistill.kill()
                raspistill = None
                photo_compute(code, photo_nb)
    return True

init_screen(cr)
cl = ClickListener(click_handler)
cl.loop()
