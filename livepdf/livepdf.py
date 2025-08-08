#!python

from typing import Callable, Sequence
from lazylist import map_lazylist

from imgcat import imgcat
from wand.image import Image # TODO: use fitz and PIL other than wand and PyPDF2
from wand.color import Color
from PyPDF2 import PdfReader
from msvcrt import getch


RATIO_PIXEL_HALF_SCREEN = 1120 / 1305

# imgcat length unit by character
CHAR_WIDTH_HALF_SCREEN = 79
CHAR_HEIGHT_HALF_SCREEN = 44

CHAR_WIDTH_FULL_SCREEN = 158
CHAR_HEIGHT_FULL_SCREEN = 44

CHAR_WIDTH_COMFORTABLE = 114

# length unit by pixel
WINDOW_STEP = 50
# COORDINATE_START = (350, 300) # fit pdf page margin
COORDINATE_START = (0, 0)


DO_NOTHING = lambda: None


def main():
    global p
    def reload():
        global p
        p = PdfViewer('main.pdf', Screen(79, 44, RATIO_PIXEL_HALF_SCREEN), reload=reload)
        p.viewer.view()
    p = PdfViewer('main.pdf', Screen(79, 44, RATIO_PIXEL_HALF_SCREEN), reload=reload)
    p.viewer.view()


def constrain(val, interval):
    minn, maxx = interval
    val = min(maxx, val)
    val = max(minn, val)
    return val


class Coordinate(object):
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"({self.x}, {self.y})"

class Rectangle(object):
    def __init__(self, width=1, height=1):
        self.width = width
        self.height = height

    @property
    def size(self):
       return [self.width, self.height]

    @size.setter
    def size(self, shape):
        it = iter(shape)
        self.width = next(it)
        self.height = next(it)

    @property
    def ratio(self):
        return self.width / self.height

    def expand(self, ratio):
        return Rectangle(self.width * ratio, self.height * ratio)

    def __repr__(self):
        return f"<Rectangle {self.size}>"

class Screen(object):
    """Terminal displaying zone attributes."""
    def __init__(self, col_num=158, row_num=45, \
                 ratio=1920 / 1080):
        self.col_num = col_num
        self.row_num = row_num
        self.ratio = ratio

class Window(object):
    def __init__(self, shape=Rectangle(100,100), screen=Screen()):
        self.shape: Rectangle = shape
        self.screen: Screen = screen

class ImageViewer(object):
    """
    Initilize data should be wand.image.Image objects.
    """
    def __init__(self, imgs: Sequence,
                 screen=Screen(), coord_start=COORDINATE_START, reload=DO_NOTHING):
        self.imgs = imgs
        self.i = 0
        self.curr = self.imgs[0] if self.imgs else Image()

        self.crop_ratio = 0.60
        self.window = Window(
            shape=Rectangle(round(self.curr.width * self.crop_ratio),
                      round(self.curr.width * self.crop_ratio / screen.ratio)),
            screen=screen)
        self.coord_start = coord_start
        self.window_coord = Coordinate(*coord_start) # left top coordinate
        self.step = WINDOW_STEP

        self.displaying: Callable = DO_NOTHING
        self.reload = reload
        self.stop = False

    @property
    def magnification(self):
        return 1 - self.crop_ratio

    def increase_crop_ratio(self, persent):
        """Make window size keep up with screen ratio"""

        self.crop_ratio += persent
        self.crop_ratio = constrain(self.crop_ratio, (0.0, 1.0))
        self.window.shape.size = (round(self.curr.width * self.crop_ratio),
                            round(self.curr.width * self.crop_ratio / self.window.screen.ratio))

    def view(self, f=DO_NOTHING):
        if f is DO_NOTHING:
            f = self.viewh
        f()
        while True:
            ch = getch()

            if self.stop:
                break

            if ch == b'q':
                break
            elif ch == b'r':
                self.reload()
                break
        # 'n'(next) & 'p'(prev) to turn page
            elif ch == b'p':
                self.prev()
                self.window_coord.x, self.window_coord.y = self.coord_start
                f()
            elif ch == b'n':
                self.succ()
                self.window_coord.x, self.window_coord.y = self.coord_start
                f()
        # 'hjkl', vim like page move
            elif ch == b'h':
                self.window_coord.x -= self.step
                self.window_coord.x = constrain(self.window_coord.x, (0, self.curr.width - self.window.shape.width))
                f()
            elif ch == b'l':
                self.window_coord.x += self.step
                self.window_coord.x = constrain(self.window_coord.x, (0, self.curr.width - self.window.shape.width))
                f()
            elif ch == b'j':
                self.window_coord.y += self.step
                self.window_coord.y = constrain(self.window_coord.y, (0, self.curr.height - self.window.shape.height))
                f()
            elif ch == b'k':
                self.window_coord.y -= self.step
                self.window_coord.y = constrain(self.window_coord.y, (0, self.curr.height - self.window.shape.height))
                f()
            elif ch == b'g':
                if getch() == b'g':
                    self.window_coord = Coordinate(0, 0)
                    f()
            elif ch == b'G':
                self.window_coord = Coordinate(
                        self.window_coord.x,
                        self.curr.height - self.window.shape.height)
                f()
        # zoom in/out
            elif ch == b'+':
                self.increase_crop_ratio(-0.05)
                f()
            elif ch == b'-':
                self.increase_crop_ratio(0.05)
                f()
        # 'display' toggle for more info
            elif ch == b'd':
                if self.displaying is DO_NOTHING:
                    self.displaying = f
                    f = (lambda: (self.displaying(), self.display()))
                else:
                    f = self.displaying
                    self.displaying = DO_NOTHING
                f()
        # 's', screen atrribute adjust
            elif ch == b's':
                ch = b''
                while True:
                    ch = getch()
                    if ch == b's': # press 's' again to exit
                        break
                    elif ch == b'C':
                        self.window.screen.col_num += 1
                    elif ch == b'c':
                        self.window.screen.col_num -= 1
                    elif ch == b'R':
                        self.window.screen.row_num += 1
                    elif ch == b'r':
                        self.window.screen.row_num -= 1
                    elif ch == b'h':
                        self.window.screen.ratio += 0.05
                    elif ch == b'v':
                        self.window.screen.ratio -= 0.05
                    f()
                    print(ch)
        # 'insert' for other settings. TODO:
            elif ch == b'i':
                if ch == b'i':
                    cmd = input()
                    print(cmd)
                    # do sth
                # f()

    def crop_curr(self):
        copy = self.curr.clone()
        copy.crop(left=self.window_coord.x, top=self.window_coord.y,
                  width=round(copy.width * self.crop_ratio),
                  height=round(copy.width / self.window.screen.ratio * self.crop_ratio))
        return copy

    def vieww(self):
        """Try to fill the screen horizontally"""
        cropped = self.crop_curr()
        imgcat(cropped.make_blob('png'), width=self.window.screen.col_num)

    def viewh(self):
        """Try to fill the screen vertically"""
        cropped = self.crop_curr()
        imgcat(cropped.make_blob('png'), height=self.window.screen.row_num)

    def succ(self):
        self.i = (self.i + 1) % len(self.imgs)
        self.curr = self.imgs[self.i]

    def prev(self):
        self.i = (self.i + len(self.imgs) - 1) % len(self.imgs)
        self.curr = self.imgs[self.i]

    def display(self):
        print(f"Page: {self.i+1}/{len(self.imgs)}, Offset: {self.window_coord
                }, Magnification: {self.magnification:.2f}")

class LazyViewer(ImageViewer):
    @staticmethod
    def path_to_img(path):
        return Image(filename=path, resolution=200, background=Color('white'))

    def __init__(self, imgs_src: Sequence, to_img_obj=path_to_img,
                 screen=Screen(), coord_start=COORDINATE_START,
                 max_cache_size=6, reload=DO_NOTHING):
        self.lazylist = map_lazylist(to_img_obj, imgs_src, max_cache_size=max_cache_size, on_evict=lambda img: img.close())
        super().__init__([self.lazylist[0]], screen, coord_start, reload)

    def succ(self):
        self.i = (self.i + 1) % len(self.lazylist)
        self.curr = self.lazylist[self.i]

    def prev(self):
        self.i = (self.i + len(self.lazylist) - 1) % len(self.lazylist)
        self.curr = self.lazylist[self.i]

    def display(self):
        print(f"Page: {self.i+1}/{len(self.lazylist)}, Offset: {self.window_coord
                }, Magnification: {self.magnification:.2f}")

class PdfViewer:
    def __init__(self, pdf_path, screen=Screen(), coord_start=COORDINATE_START, max_cache_size=6, reload=DO_NOTHING):
        self.page_num = len(PdfReader(open(pdf_path, 'rb')).pages)
        self.page_indices = range(self.page_num)

        def pdf_page_to_img(page_index):
            path = f"{pdf_path[:-4]}.pdf[{page_index}]"
            img = Image(filename=path, resolution=200, background=Color('white'))
            img.merge_layers('flatten')
            img = Image(blob=img.make_blob('png'))
            return img

        self.lazyviewer = LazyViewer(self.page_indices, pdf_page_to_img,
                                     screen=screen, coord_start=coord_start,
                                     max_cache_size=max_cache_size, reload=reload)
        self.viewer = self.lazyviewer
        self.view = self.viewer.view


if __name__ == "__main__":
    # test()
    main()
