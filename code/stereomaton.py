#!/usr/bin/env python3

import cairo
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
gen_code_phonems = ('BA', 'DE', 'FA', 'KA', 'LI', 'MI', 'NO', 'NU', 'PI', 'PO', 'RI', 'TA', 'VO', 'VU', 'ZO')
def gen_code():
  return ''.join(choice(gen_code_phonems) for _ in range(5))

cfb = CairoFB()
cr = cfb.cr()
clear(cr)
text_code_explaination(cr)
for _ in range(50):
    text_code(cr, gen_code())
    sleep(0.25)

text_code(cr, gen_code())
sleep(10)
