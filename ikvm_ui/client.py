# coding: utf-8
if __name__ != 'ikvm_ui.client':
    exit()
from ikvm import *
from ._globals import *
import pygame
import cv2, os, re
import numpy as np
from sys import stdout, stderr
from threading import Thread, Lock
from time import sleep
from datetime import datetime
from math import ceil, copysign
from screeninfo import get_monitors
if OS == 'WINDOWS':
    import keyboard

raw = lambda string: repr(string).replace('\\\\', '\\')

ALARM_TEXT = [
        'Confirm send short power command to controled host?',
        'Confirm send reset command to controled host?',
        'Confirm send long power command to controled host?',
        'Confirm send ctrl+alt+del command to controled host?',
]

class Popup:
    def __init__(self, screen, btn_txt_scale):
        # General settings
        self.show = False
        self._screen = screen
        self.__btn_txt_scale = btn_txt_scale
        self._hover_confirm = False
        self._hover_cancel = False

    def generate_components(self, x, y, w, h, scale):
        solid_h = h-BORDER_THICK*2-POPUP_MARGIN*3 # components occupied height
        content_h = solid_h*scale
        # Frames
        self._border = pygame.Rect(x, y, w, h)
        bg_x, bg_y = [x+BORDER_THICK for x in (x, y)]
        bg_w, bg_h = [x-BORDER_THICK*2 for x in (w, h)]
        self._bg = pygame.Rect(bg_x, bg_y, bg_w, bg_h)
        # Buttons
        btn_w = (w-BORDER_THICK*2-POPUP_MARGIN*3)/2
        btn_h = solid_h*(1-scale)
        confirm_x = x+BORDER_THICK+POPUP_MARGIN
        cancel_x = x+BORDER_THICK+POPUP_MARGIN*2+btn_w
        btn_y = y+BORDER_THICK+POPUP_MARGIN*2+content_h
        self._confirm = pygame.Rect(confirm_x, btn_y, btn_w, btn_h)
        self._cancel = pygame.Rect(cancel_x, btn_y, btn_w, btn_h)
        return content_h

    def render(self):
        # render the border and background
        pygame.draw.rect(self._screen, BORDER_COLOR, self._border, BORDER_THICK)
        pygame.display.update(self._border)
        pygame.draw.rect(self._screen, BG_COLOR, self._bg)
        pygame.display.update(self._bg)
        # render the bottons
        pygame.draw.rect(self._screen, BTN_COLOR_LIGHT if self._hover_confirm else BTN_COLOR_DARK, self._confirm)
        pygame.display.update(self._confirm)
        pygame.draw.rect(self._screen, BTN_COLOR_LIGHT if self._hover_cancel else BTN_COLOR_DARK, self._cancel)
        pygame.display.update(self._cancel)

        txt_size = int(self._confirm.h*self.__btn_txt_scale)
        font = pygame.font.SysFont('serif', txt_size)
        text = font.render('Confirm', True, TXT_COLOR)
        x = self._confirm.x + (self._confirm.w-text.get_size()[0])/2
        y = self._confirm.y + (self._confirm.h-text.get_size()[1])/2
        txt_rect = self._screen.blit(text, (x, y))
        pygame.display.update(txt_rect)

        text = font.render('Cancel', True, TXT_COLOR)
        x = self._cancel.x + (self._cancel.w-text.get_size()[0])/2
        y = self._cancel.y + (self._cancel.h-text.get_size()[1])/2
        txt_rect = self._screen.blit(text, (x, y))
        pygame.display.update(txt_rect)

    def _in_confirm(self, cur):
        x, y, w, h = self._confirm.x, self._confirm.y, self._confirm.w, self._confirm.h
        return x <= cur[0] <= x+w and y <= cur[1] <= y+h

    def _in_cancel(self, cur):
        x, y, w, h = self._cancel.x, self._cancel.y, self._cancel.w, self._cancel.h
        return x <= cur[0] <= x+w and y <= cur[1] <= y+h

    def _out_popup(self, cur):
        x, y, w, h = self._border.x, self._border.y, self._border.w, self._border.h
        return not x <= cur[0] <= x+w or not y <= cur[1] <= y+h 

    def _canceled(self):
        self.show = False
        self._screen.fill(BG_COLOR)
        pygame.display.flip()

    def hover(self, cur):
        if self._in_confirm(cur):
            self._hover_confirm = True
            self._hover_cancel = False
        elif self._in_cancel(cur):
            self._hover_confirm = False
            self._hover_cancel = True
        else: # clear hover status
            self.__hover_confirm = False
            self._hover_cancel = False

class SetLockMousePopup(Popup):
    def __init__(self, screen, lock_key):
        super().__init__(screen, BIG_BTN_TXT_SCALE)
        # Whenever select a send command, warnpopup will save the command for sending until "Confirm" button clicked
        self.lock_key = lock_key
        self.lock_txt = self.__generate_lock_key_text(lock_key)
        self.__temp_lock_key = lock_key
        self.__temp_lock_txt = self.lock_txt
        self.__font = pygame.font.SysFont('serif', LOCK_TXT_SIZE)

    def generate_components(self, x, y, w, h):
        # Set Lock Mouse Text
        self.__lock_txt_h = super().generate_components(x, y, w, h, LOCK_SCALE)

    def render(self):
        if not self.show:
            return
        super().render()
        # render the set lock mouse text
        text = self.__font.render(f'Set key <{self.__temp_lock_txt}> as mouse lock key', True, TXT_COLOR)
        x = self._bg.x+POPUP_MARGIN+(self._bg.w-text.get_size()[0])/2
        y = self._bg.y+POPUP_MARGIN+(self.__lock_txt_h-text.get_size()[1])/2
        txt_rect = self._screen.blit(text, (x, y))
        pygame.display.update(txt_rect)

    def __generate_lock_key_text(self, py_key):
        if py_key in PYGAME_KEY_MAP:
            key = PYGAME_KEY_MAP[py_key][4:]
        elif py_key in PYGAME_EXTRA_KEY_MAP:
            key = PYGAME_EXTRA_KEY_MAP[py_key]
        elif py_key in range(0x80):
            key = chr(py_key)
        else:
            return
        return f'{key}'

    def input_key(self, py_event):
        if not self.show or py_event.type == pygame.KEYDOWN:
            return
        result = self.__generate_lock_key_text(py_event.key)
        if result:
            self.__temp_lock_key = py_event.key 
            self.__temp_lock_txt = result

    def click(self, cur):
        if self._in_confirm(cur):
            self._canceled()
            self.lock_key = self.__temp_lock_key # save the mouse lock key
            self.lock_txt = self.__temp_lock_txt
            return {'result': 'confirm', 'detail': self.lock_key}
        elif self._in_cancel(cur):
            self.__temp_lock_key = self.lock_key # restore the mouse lock key information as canceled
            self.__temp_lock_txt = self.lock_txt
            self._canceled()
            return {'result': 'cancal'}
        elif self._out_popup(cur):
            self.__temp_lock_key = self.lock_key
            self.__temp_lock_txt = self.lock_txt
            self._canceled()
            return {'result': 'out of box'}
        return None

class WarnPopup(Popup):
    def __init__(self, screen):
        super().__init__(screen, BIG_BTN_TXT_SCALE)
        # Whenever select a send command, warnpopup will save the command for sending until "Confirm" button clicked
        self.send_command = 0xFF
        self.__font = pygame.font.SysFont('serif', WARN_TXT_SIZE)

    def generate_components(self, x, y, w, h):
        # Alarm Text
        self.__alm_txt_h = super().generate_components(x, y, w, h, WARN_SCALE)

    def render(self):
        if not self.show or self.send_command not in range(TOTAL_SEND_CMD):
            return
        super().render()
        # render the alarm text
        text = self.__font.render(ALARM_TEXT[self.send_command], True, TXT_COLOR)
        x = self._bg.x+POPUP_MARGIN+(self._bg.w-text.get_size()[0])/2
        y = self._bg.y+POPUP_MARGIN+(self.__alm_txt_h-text.get_size()[1])/2
        txt_rect = self._screen.blit(text, (x, y))
        pygame.display.update(txt_rect)

    def input_key(self, py_event):
        if self.show and py_event.type == pygame.KEYUP: # click any key to cancel
            self._canceled()

    def click(self, cur):
        if self._in_confirm(cur):
            self._canceled()
            return {'result': 'confirm'}
        elif self._in_cancel(cur):
            self._canceled()
            return {'result': 'cancal'}
        elif self._out_popup(cur):
            self._canceled()
            return {'result': 'out of box'}
        return None

class InputPopup(Popup):
    def __init__(self, screen):
        super().__init__(screen, MIDDLE_BTN_TXT_SCALE)
        self.__input = ''
        self.__font = pygame.font.SysFont('serif', INPUT_TXT_SIZE)

        # Cursor
        chr_w, chr_h = self.__font.size('_')
        self.__cursor = pygame.Rect(0, 0, chr_w, chr_h)

        # Init clipboard scraper
        pygame.scrap.init()
        pygame.scrap.set_mode(pygame.SCRAP_CLIPBOARD)

    def generate_components(self, x, y, w, h):
        # InputBox
        input_x, input_y = [x+BORDER_THICK+POPUP_MARGIN for x in (x, y)]
        input_w = w-(BORDER_THICK+POPUP_MARGIN)*2
        input_h = super().generate_components(x, y, w, h, INPUTBOX_SCALE)
        self.__input_bg = pygame.Rect(input_x, input_y, input_w, input_h)

    def __render_input_text(self):
        lines = self.__input.splitlines()
        chr_h = self.__font.size('^')[1]
        start_x = self.__input_bg.x + INPUTBOX_PAD
        max_x, max_y = [x-INPUTBOX_PAD*2 for x in self.__input_bg.bottomright]
        max_w = self.__input_bg.w-INPUTBOX_PAD*2
        x, y = cur_x, cur_y = self.__input_bg.x + INPUTBOX_PAD, self.__input_bg.y + INPUTBOX_PAD
        for line in lines:
            if y+chr_h > max_y: # do not display overflowed charactor
                break
            for char in line:
                if char == '\t':
                    rem = (max_x-x)/max_w # progress percent of x remain in the width of self.__input_bg
                    offset = max_w*TAB_SCALE*ceil((1-rem)/TAB_SCALE) # \t moved actual offset based on start_x
                    if start_x+offset > max_x:
                        x = start_x+TAB_SCALE*self.__input_bg.w
                        y += chr_h
                    else:
                        x = start_x+offset
                    continue
                text = self.__font.render(char, True, TXT_COLOR)
                chr_w = text.get_size()[0]
                if x+chr_w > max_x:
                    x = start_x # start at newline
                    y += chr_h
                if y+chr_h > max_y: # do not display overflowed charactor
                    break
                txt_rect = self._screen.blit(text, (x, y))
                pygame.display.update(txt_rect)
                x += chr_w
            cur_x, cur_y = x, y
            x = start_x # start at newline
            y += chr_h
        # render cursor
        if self.__input and self.__input[-1] == '\n': # line end with no characters
            cur_x, cur_y = x, y
        if cur_y+chr_h <= max_y:
            cursor = self.__cursor.move(cur_x, cur_y)
            pygame.draw.rect(self._screen, BTN_COLOR_LIGHT, cursor)
            pygame.display.update(cursor)

    def render(self):
        if not self.show:
            return
        super().render()
        # render the border and background
        pygame.draw.rect(self._screen, INPUT_BG_COLOR, self.__input_bg)
        pygame.display.update(self.__input_bg)

        # render the inputbox text
        self.__render_input_text()

    def input_key(self, py_event):
        if not self.show or py_event.type == pygame.KEYDOWN:
            return
        key = py_event.key
        mod = py_event.mod
        if key == pygame.K_ESCAPE: # <Esc>
            self._canceled()
        elif key == pygame.K_TAB: # <Tab>
            self.__input += '\t'
        elif key == pygame.K_BACKSPACE and mod & pygame.KMOD_ALT: # <A-BS> backspace text by word
            remain = re.match(r'^(.*\W)\w+', self.__input, re.DOTALL)
            self.__input = remain.group(1) if remain else ''
        elif key == pygame.K_BACKSPACE or (key == pygame.K_h and mod & pygame.KMOD_CTRL): # <BS> <C-h>
            self.__input = self.__input[:-1]
        elif key == pygame.K_RETURN and mod & pygame.KMOD_CTRL: # <C-CR> commit the send text
            input_txt = self.__input
            self._canceled()
            return {'result': 'ctrl+enter', 'detail': input_txt}
        elif key == pygame.K_RETURN or (key == pygame.K_m and mod & pygame.KMOD_CTRL): # <CR> <C-m>
            self.__input += '\n'
        elif key == pygame.K_z and mod & pygame.KMOD_CTRL: # <C-z> clear input
            self.__input = ''
        elif key == pygame.K_u and mod & pygame.KMOD_CTRL: # <C-u> delete a line
            remain = re.match(r'^(.*\n)[^\n]+', self.__input, re.DOTALL)
            self.__input = remain.group(1) if remain else ''
        elif key == pygame.K_w and mod & pygame.KMOD_CTRL: # <C-w> delete non space/newline word
            remain = re.match(r'^(.*[ \n])[^ \n]+', self.__input, re.DOTALL)
            self.__input = remain.group(1) if remain else ''
        elif key == pygame.K_v and mod & pygame.KMOD_CTRL: # <C-v> paste from clipboard
            clipboard = pygame.scrap.get(pygame.SCRAP_TEXT)
            if clipboard is None:
                return
            # Filter characters that keyboard can type and are printable, exclude <CR> <Tab>
            text = ''.join([chr(char) for char in clipboard if((
                char in range(0x80) and chr(char).isprintable()) or (
                char in map(ord, ('\n', '\t',))))])
            self.__input += text
        elif key == pygame.K_c and mod & pygame.KMOD_CTRL: # <C-c> copy to clipboard
            pygame.scrap.put(pygame.SCRAP_TEXT, self.__input.encode('utf-8'))
        elif key in (pygame.K_KP_PERIOD, pygame.K_KP_DIVIDE, pygame.K_KP_MULTIPLY,
                pygame.K_KP_MINUS, pygame.K_KP_PLUS,): # type a special character
            self.__input += py_event.unicode
        elif key not in PYGAME_KEY_MAP and key in range(0x80): # type a character
            if mod & pygame.KMOD_CTRL:
                self.__input += chr(key)
            else:
                self.__input += py_event.unicode

    def _canceled(self):
        self.__input = ''
        super()._canceled()

    def click(self, cur):
        if self._in_confirm(cur):
            input_txt = self.__input
            self._canceled()
            return {'result': 'confirm', 'detail': input_txt}
        elif self._in_cancel(cur):
            self._canceled()
            return {'result': 'cancal'}
        return None

class iKvmClient:
    def __init__(self, ikvm, mjpg, fullscreen=False, cap_res_in_win=(0, 0), logfile=None, log_level=3):
        """ ikvm: required
                    Kvm instance for sending kvm control command

            mjpg: required
                    MjpgClient instance for getting capture frames from mjpg-streamer

            fullscreen: optional, <bool>, default False
                    init instance in fullscreen mode when value is True

            cap_res_in_win: optional, <tuple> with 2 <int>, default (0, 0)
                    tuple of width and height resolution of capture display area in windowed mode
                    use (0, 0) as adaptive screen size

            logfile: optional, <str>, default None
                    specific the path of logfile, use stdout and stderr when value is None

            log_level: optional, <int>, default 3
                    check whether program records log information
                    if argument level in __log_write(level, txt) is less than or equal log_level,
                    then the message txt will be written into logfile
        """
        assert isinstance(ikvm, Kvm)
        assert isinstance(mjpg, MjpgClient)
        assert isinstance(fullscreen, bool)
        assert isinstance(cap_res_in_win, tuple)
        assert len(cap_res_in_win) == 2
        assert all([isinstance(x, int) for x in cap_res_in_win])
        assert (all([x > 0 for x in cap_res_in_win]) or
                all([x == 0 for x in cap_res_in_win]))
        assert isinstance(logfile, (str, type(None)))
        assert log_level in range(6)
        ## Settings of iKVM
        self.__ikvm = ikvm
        self.__caps = [] # a list of video captures get from ikvm
        self.__mjpg_ip = f'[{self.__ikvm.ip}]' if address_family(self.__ikvm.ip) == 'ipv6' else self.__ikvm.ip
        self.__mjpg_port = self.__ikvm.mjpg_port

        ## Settings of Video Capture
        self.__capture = mjpg

        ## Settings of PyGame
        self.__run = False
        pygame.init()
        pygame.display.set_caption('iKVM')
        self.__fullscreen = fullscreen
        self.__win_x, self.__win_y = 0, 0 # window position
        if cap_res_in_win == (0, 0):
            w, h = get_monitors()[0].width, get_monitors()[0].height
            self.__cap_res_in_win = (w-SIDE_W-160, h-90)
        else:
            self.__cap_res_in_win = cap_res_in_win

        # self.__side_no: decide what side menu display
        #  MAIN_MENU       (0): main menu
        #  SERIAL_MENU     (1): serial device selection menu
        #  CAPTURE_MENU    (2): capture video selection menu, device pane
        #  RESOLUTION_MENU (3): capture video selection menu, resolution pane, submenu of #2
        #  FRAMERATE_MENU  (4): capture video selection menu, frame rate selection, submenu of #3
        #  SEND_MENU       (5): send atx signal/hotkeys selection menu
        self.__side_no       = 0
        self.__side_txt      = [] # displayed menu items
        self.__side_full_txt = [] # saved full menu items for current menu
        self.__side_show_max = 0 # maximal number of the displayed menu items, recompute whenever __render_main() called
        self.__side_page     = 0 # what part of __side_txt shown in side menu

        self.__mouse_locked = False # is mouse locked in video capture area
        self.__lock_mouse_key = pygame.K_F7 # click the setted lock key, mouse will lock/unlock in video capture area
        self.__lock_mouse_key_txt = 'F7'

        ## Settings of Popup
        self.__warnpopup = None
        self.__inputpopup = None
        self.__set_lock_mouse_popup = None

        ## Settings of LOG
        self.log_level = log_level
        self.logfile = logfile

        ## Settings of Keyboard Hook
        self.__hooked = False

    def __get_resolution(self):
        monitors = get_monitors()
        for monitor in monitors:
            if (self.__win_x <  monitor.x+monitor.width and
                self.__win_x >= monitor.x and
                self.__win_y <  monitor.y+monitor.height and
                self.__win_y >= monitor.y):
                return (monitor.width, monitor.height)
        return (monitors[0].width, monitors[0].height)

    def __open_serial_device(self, device):
        for i in range(1, RETRY+1):
            res = self.__ikvm.open_serial_device(device)
            if res['result'] == 'success':
                self.__log_write(3, 'Open serial device success. Detail: %s' %res['detail'])
                return True
            self.__log_write(1, 'Open serial device failed, detail: %s, retry %d' %(res['detail'], i))
            if i == RETRY:
                self.__log_write(1, 'Open serial device reach the max retry times')
                return False

    def __alt_capture(self, device, resolution, fps):
        for i in range(1, RETRY+1):
            res = self.__ikvm.alt_capture(device, resolution, fps)
            if res['result'] == 'success':
                self.__log_write(3, 'Alt video capture success. Detail: %s' %res['detail'])
                return True
            self.__log_write(1, 'Alt video capture failed, detail: %s, retry %d' %(res['detail'], i))
            if i == RETRY:
                self.__log_write(1, 'Exit client as reach the max retry times')
                self.__run = False
                return False

    def __connect_mjpg(self):
        for i in range(1, RETRY+1):
            res = self.__capture.open(f'http://{self.__mjpg_ip}:{self.__mjpg_port}/?action=stream')
            if res['result'] == 'success':
                return True
            if not self.__ikvm.is_run(): # check if the failure reason is disconnected from server
                self.__log_write(3, "MJPG-Streamer is not running since client is disconnected from iKVM server")
                return False
            self.__log_write(1, 'Connect MJPG-Streamer failed. Detail: %s. Retry %d' %(res['detail'], i))
            if i == RETRY:
                self.__log_write(1, 'Exit client as reach the max retry times')
                self.__run = False
                return False

    def __response_handler(self):
        while self.__run:
            res = self.__ikvm.read_last_send_key_result()
            if res is not None:
                self.__log_write(4, 'Echo(Key) => {} <= [{}]'.format(res['detail'], res['result']))
                if res['detail'] == 'Kvm instance not started':
                    return

            res = self.__ikvm.read_last_send_mouse_result()
            if res is not None:
                self.__log_write(4, 'Echo(Mouse) => {} <= [{}]'.format(res['detail'], res['result']))
                if res['detail'] == 'Kvm instance not started':
                    return

            res = self.__ikvm.read_last_send_atx_result()
            if res is not None:
                self.__log_write(4, 'Echo(ATX) => {} <= [{}]'.format(res['detail'], res['result']))
                if res['detail'] == 'Kvm instance not started':
                    return

            sleep(0.01)

    def __log_write(self, level: int, txt):
        if self.log_level < level:
            return
        out = '{} [{}]: {}\n'.format(datetime.now().isoformat(), LOG_LEVEL[level], txt)
        with self.__log_lock:
            if self.__log_fh is stdout and level < 2:
                stderr.write(out)
            else:
                self.__log_fh.write(out)

    def __compute_side_show_max(self):
        if self.__fullscreen:
            gui_h = self.__get_resolution()[1]
        else:
            cap_h = self.__cap_res_in_win[1]
            gui_h = SIDE_H if cap_h < SIDE_H else cap_h

        return int(gui_h/BTN_AND_PAD_H)

    def __render_main(self):
        ## Settings of Screen
        if self.__fullscreen:
            gui_w, gui_h = self.__get_resolution()
            self.__cap_res = (gui_w-SIDE_W, gui_h)
            self.__screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            cap_w = self.__cap_res[0]
        else:
            self.__cap_res = self.__cap_res_in_win
            cap_w, cap_h = self.__cap_res
            gui_w  = cap_w + SIDE_W
            gui_h = SIDE_H if cap_h < SIDE_H else cap_h
            self.__screen = pygame.display.set_mode((gui_w, gui_h))

        self.__side_show_max = show = int(gui_h/BTN_AND_PAD_H)

        total = len(self.__side_txt)

        self.__screen.fill(BG_COLOR)

        ## Button Style
        self.__btn_w = SIDE_W*BTN_W_SCALE
        self.__btn_h = gui_h/show*BTN_H_SCALE
        w_shift = (SIDE_W-self.__btn_w)/2
        h_pad   = gui_h/show*(1-BTN_H_SCALE)/2

        self.__btn_pos = [(cap_w+w_shift, i*gui_h/show+h_pad) for i in range(total)]

        ## Text Style
        txt_size = int(self.__btn_h*SMALL_BTN_TXT_SCALE)

        font = pygame.font.SysFont('serif', txt_size)
        self.__text = [font.render(self.__side_txt[i], True, TXT_COLOR) for i in range(total)]

        txt_pad = (self.__btn_h-font.size(self.__side_txt[0])[1])/2

        self.__txt_pos = [(
                cap_w+w_shift+(self.__btn_w-font.size(self.__side_txt[i])[0])/2,
                i*gui_h/show+h_pad+txt_pad) for i in range(total)]

        ## Rendering Screen
        for i in range(total):
            pygame.draw.rect(
                    self.__screen, BTN_COLOR_DARK, [
                        *self.__btn_pos[i],
                        self.__btn_w,
                        self.__btn_h])
            self.__screen.blit(self.__text[i], self.__txt_pos[i])

        pygame.display.flip()

    def __generate_side_args(self, act, side_no, proto_txt):
        total = len(proto_txt)
        # Calculate how much text items can be shown
        avail = self.__side_show_max if side_no == MAIN_MENU else self.__side_show_max-1

        if act == 'init':
            side_page = 0
        elif act == 'next':
            size = ceil(total/avail)
            side_page = (self.__side_page+1)%size
        elif act == 'previous':
            size = ceil(total/avail)
            side_page = (self.__side_page-1)%size
        else:
            return

        at = side_page*avail
        if at+1 > total:
            raise ValueError('Generate side menu arguments "at" unexpected')
        show = avail if total-at > avail else total-at

        side_txt = proto_txt[at:at+show]
        if side_no != MAIN_MENU:
            side_txt.append('Back')

        return (side_no, proto_txt, side_page, side_txt)

    def __in_side_page(self, btn_no): # check if the given button by seqno in __side_full_txt is in current menu page
        avail = self.__side_show_max if self.__side_no == MAIN_MENU else self.__side_show_max-1
        return int(btn_no/avail) == self.__side_page

    def __in_button(self, cur, btn_no): # check if the cursor is in the given button by seqno in __side_full_txt
        avail = self.__side_show_max if self.__side_no == MAIN_MENU else self.__side_show_max-1
        return self.__in_visible_button(cur, btn_no%avail)

    def __back_button_no(self, cur): # get the seqno in __side_txt of "Back" button
        if self.__side_no == MAIN_MENU:
            return False
        total = len(self.__side_full_txt)
        avail = self.__side_show_max-1
        end_page = int(total/avail) # when total is divisible by avail, function will return avail as back button position
        return total%avail if end_page == self.__side_page else avail

    def __render_side_button(self, cur):
        total = len(self.__side_txt)
        for i in range(total):
            in_btn = self.__in_visible_button(cur, i)
            btn_rect = pygame.draw.rect(
                        self.__screen,
                        BTN_COLOR_LIGHT if in_btn else BTN_COLOR_DARK, [
                            *self.__btn_pos[i],
                            self.__btn_w,
                            self.__btn_h])
            txt_rect = self.__screen.blit(self.__text[i], self.__txt_pos[i])
            pygame.display.update(btn_rect)
            pygame.display.update(txt_rect)

    def __fetch_frame(self):
        try:
            cap_out = self.__capture.next_frame()
        except (TimeoutError, OSError,):
            cap_out = None

        if cap_out is None:
            self.__log_write(2, "Fetch frame from MJPG-Streamer timeout, now re-connnect")
            self.__connect_mjpg()
            return None
        elif cap_out['result'] == 'lost':
            self.__log_write(1, "Disconnected from MJPG-Streamer, now re-connnect")
            self.__connect_mjpg()
            return None
        elif cap_out['result'] == 'error':
            self.__log_write(2, "Fetch frame from MJPG-Streamer failed. Detail: " + cap_out['detail'])
            return None

        return cap_out['detail']

    def __render_cap_area(self):
        cap_img = self.__fetch_frame()
        if cap_img is None:
            return

        # Logitech C270i webcam will reproduce the "extraneous bytes" error since the incorrect implementation of mjpeg
        # refer: https://github.com/opencv/opencv/issues/9477#issuecomment-837104940
        arr = np.frombuffer(cap_img, np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        # Enlarge prefer INTER_LINEAR/INTER_CUBIC
        # Shrink prefer INTER_AREA
        enlarge = self.__cap_res[0]*self.__cap_res[1] > frame.shape[0]*frame.shape[1]
        interpolation = cv2.INTER_LINEAR if enlarge else cv2.INTER_AREA
        frame = cv2.resize(frame, self.__cap_res, interpolation=interpolation)
        cap_img = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], 'BGR').convert_alpha()
        cap_rect = self.__screen.blit(cap_img, (0, 0))
        pygame.display.update(cap_rect)

    def __in_visible_button(self, cur, no): # check if cursor is in visible button by seqno in __side_txt
        x = self.__btn_pos[no][0]
        y = self.__btn_pos[no][1]
        return x <= cur[0] <= x+self.__btn_w and y <= cur[1] <= y+self.__btn_h

    def __in_cap(self, cur): # check if cursor is in video capture display area
        return (cur[0] <= self.__cap_res[0] and 
                cur[0] > 0 and
                cur[1]+1 < self.__cap_res[1] and
                cur[1] > 0)

    def __hook_key(self, e):
        cur = pygame.mouse.get_pos()
        # Check if all popups (except set-lock-mouse) is off and mouse in video capture display area
        if ((not (self.__warnpopup.show or self.__inputpopup.show) and
            pygame.mouse.get_focused() and self.__in_cap(cur)) or self.__set_lock_mouse_popup.show):
            # Send key to pygame for process
            try:
                key = HOOK_KP_MAP[e.name] if e.is_keypad else HOOK_KEY_MAP[e.name]
            except KeyError:
                return
            e_type = pygame.KEYUP if e.event_type == keyboard.KEY_UP else pygame.KEYDOWN
            py_event = pygame.event.Event(e_type, key=key)
            pygame.event.post(py_event)
        else:
            # Feedback the same key to operating system
            key = e.scan_code if e.name in HOOK_BUG_KEYS else e.name # keyboard library BUG: use scan_code instead
            keyboard.release(key) if e.event_type == keyboard.KEY_UP else keyboard.press(key)

    def start(self):
        # Open log file
        self.__log_lock = Lock()
        self.__log_fh = open(self.logfile, 'a', LOG_BUFSIZE) if self.logfile else stdout

        ## Init ikvm and mjpg client
        for i in range(1, RETRY+1):
            res = self.__ikvm.start()
            if res['result'] == 'success':
                break
            self.__log_write(1, 'Connect iKVM failed, detail => %s <= Retry %d' %(': '.join(res['detail']), i))
            if i == RETRY:
                self.__log_write(1, 'Exit client as reach the max retry times')
                return
        self.__log_write(3, 'iKVM connected')
        if not self.__connect_mjpg():
            return
        self.__log_write(3, 'MJPG-Streamer connected')

        # List serial devices in advance
        res = self.__ikvm.list_serial_devices()
        if res['result'] == 'success':
            self.__serials = res['detail']
            self.__log_write(4, 'List serial device success')
        else:
            self.__log_write(2, 'List serial device from iKVM failed. Detail: ' + res['detail'])

        # List video captures in advance
        res = self.__ikvm.list_captures()
        if res['result'] == 'success':
            self.__log_write(4, 'List video captures success')
            self.__caps = res['detail']
        else:
            self.__log_write(2, 'List video captures from iKVM failed. Detail: ' + res['detail'])

        ## Render GUI
        self.__side_show_max = self.__compute_side_show_max() # pre-compute for invocation of __generate_side_args
        self.__to_main_menu()
        # Init Popups
        cur_w, cur_h = pygame.display.Info().current_w, pygame.display.Info().current_h
        x, y = (1-WARN_W_SCALE)*cur_w/2, (1-WARN_H_SCALE)*cur_h/2
        w, h = cur_w*WARN_W_SCALE, cur_h*WARN_H_SCALE
        self.__warnpopup = WarnPopup(self.__screen)
        self.__warnpopup.generate_components(x, y, w, h)

        x, y = (1-LOCK_W_SCALE)*cur_w/2, (1-LOCK_H_SCALE)*cur_h/2
        w, h = cur_w*LOCK_W_SCALE, cur_h*LOCK_H_SCALE
        self.__set_lock_mouse_popup = SetLockMousePopup(self.__screen, self.__lock_mouse_key)
        self.__set_lock_mouse_popup.generate_components(x, y, w, h)

        x, y = (1-INPUT_W_SCALE)*cur_w/2, (1-INPUT_H_SCALE)*cur_h/2
        w, h = cur_w*INPUT_W_SCALE, cur_h*INPUT_H_SCALE
        self.__inputpopup = InputPopup(self.__screen)
        self.__inputpopup.generate_components(x, y, w, h)
        self.__log_write(4, 'Created InputPopup component')
        # Setup clock
        clock = pygame.time.Clock()

        self.__run = True # Starting
        ## Start thread for handing response from key_send/mouse_send/axt_send
        Thread(target=self.__response_handler).start()
        self.__log_write(4, 'Response handler thread start')

        ## Exit as 1. user close the window, or 2. mjpg-streamer or ikvm server are not running
        while self.__run:
            cur = pygame.mouse.get_pos()

            ## Rendering Buttons
            if self.__warnpopup.show:
                self.__warnpopup.hover(cur)
            elif self.__inputpopup.show:
                self.__inputpopup.hover(cur)
            elif self.__set_lock_mouse_popup.show:
                self.__set_lock_mouse_popup.hover(cur)
            else:
                self.__render_side_button(cur)

            ## Rendering Video Capture Area
            self.__render_cap_area()

            ## Rendering All Popups
            self.__warnpopup.render()
            self.__inputpopup.render()
            self.__set_lock_mouse_popup.render()

            ## Hide Mouse in Video Capture Area when there is no popup
            cur_in_cap = self.__in_cap(cur)
            if not (self.__warnpopup.show or self.__inputpopup.show or self.__set_lock_mouse_popup.show):
                if cur_in_cap and pygame.mouse.get_visible():
                    pygame.mouse.set_visible(False)
                    self.__log_write(4, 'Mouse hid')
                if not cur_in_cap and not pygame.mouse.get_visible():
                    pygame.mouse.set_visible(True)
                    self.__log_write(4, 'Mouse appeared')

            ## Event Handling
            for py_event in pygame.event.get():
                ## Close Window
                if py_event.type == pygame.QUIT:
                    self.__ikvm.release_keys()
                    self.__log_write(4, 'Release all pressed key before quit')
                    self.__log_write(4, 'Pygame received quit event')
                    self.__run = False

                ## Window Moved
                elif py_event.type == pygame.WINDOWMOVED:
                    self.__win_x, self.__win_y = py_event.x, py_event.y
                    self.__screen.fill(BG_COLOR)
                    self.__render_main()

                ## Window Restored
                elif py_event.type == pygame.WINDOWRESTORED:
                    self.__screen.fill(BG_COLOR)
                    self.__render_main()

                ## Mouse Click
                elif py_event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN):
                    self.__mouse_click_event(py_event, cur_in_cap, cur)

                ## Keyboard Input
                elif py_event.type in (pygame.KEYUP, pygame.KEYDOWN):
                    self.__keyboard_input_event(py_event, cur_in_cap)

                ## Mouse Move
                elif py_event.type == pygame.MOUSEMOTION:
                    self.__mouse_move_event(cur_in_cap)

            if not self.__ikvm.is_run():
                self.__log_write(3, 'Disconnected from iKVM server')
                self.__run = False

            clock.tick(120)

        # Handling Exit
        if OS == 'WINDOWS' and self.__hooked:
            keyboard.unhook_all()
            self.__log_write(4, 'Keyboard unhooked')
        pygame.quit()
        self.__log_write(4, 'Pygame quit')
        self.__ikvm.end()
        self.__log_write(3, 'Client exit completely')
        if self.__log_fh is not stdout:
            self.__log_fh.close()

    def __mouse_click_event(self, py_event, cur_in_cap, cur):
        py_button = py_event.button

        # handle popup first
        if self.__warnpopup.show or self.__inputpopup.show or self.__set_lock_mouse_popup.show:
            if py_button != MOUSE_LEFT or py_event.type != pygame.MOUSEBUTTONUP:
                return
            if self.__warnpopup.show:
                self.__warnpopup_click(cur)
            elif self.__inputpopup.show:
                self.__inputpopup_click(cur)
            else:
                self.__set_lock_mouse_popup_click(cur)
            return

        if cur_in_cap:
            press = (py_event.type == pygame.MOUSEBUTTONDOWN)
            press_txt = 'Pressed' if press else 'Released'

            if py_button in PYGAME_MOUSE_MAP:
                button = ARDUINO_MOUSE_MAP[PYGAME_MOUSE_MAP[py_button]]
                self.__log_write(4, '{} {} <{:02X}>'.format(press_txt, PYGAME_MOUSE_MAP[py_button], py_button))

                press_txt = 'press' if press else 'release'
                res = self.__ikvm.click_mouse(press_txt, button)
                if res['result'] != 'success':
                    self.__log_write(2, 'Send {} mouse button <{:02X}> to iKVM failed'.format(press_txt, py_button))
            elif py_button == MOUSE_WHEEL_UP:
                self.__log_write(4, 'Mouse scroll wheel up')

                res = self.__ikvm.scroll_mouse_wheel_up()
                if res['result'] != 'success':
                    self.__log_write(2, 'Send mouse scroll wheel up to iKVM failed')
            elif py_button == MOUSE_WHEEL_DOWN:
                self.__log_write(4, 'Mouse scroll wheel down')

                res = self.__ikvm.scroll_mouse_wheel_down()
                if res['result'] != 'success':
                    self.__log_write(2, 'Send mouse scroll wheel down to iKVM failed')
            else: # maybe has other buttons, not sure
                self.__log_write(4, '{} an invalid button: {}'.format(press_txt, py_button))

        elif py_event.type == pygame.MOUSEBUTTONUP: # mouse event in side menu
            if py_button == MOUSE_LEFT: # clicked left in side menu
                if self.__side_no not in range(TOTAL_MENU):
                    self.__log_write(1, 'Unkown side menu number <%d>' %self.__side_no)
                    return
                iKvmClient.__BUTTON_ACTION_SWITCH[self.__side_no](self, cur)
            elif py_button in (MOUSE_WHEEL_UP, MOUSE_WHEEL_DOWN): # scroll wheel in side menu
                self.__scroll_page(py_button)

    def __to_main_menu(self):
        side_full_txt = MAIN_MENU_FULL_TXT
        side_full_txt[FULLSCREEN_NO] = 'Windowed' if self.__fullscreen else 'Fullscreen'
        side_full_txt[HOOK_KEY_NO] = 'Unhook Keyboard' if self.__hooked else 'Hook Keyboard'
        side_full_txt[SET_LOCK_KEY_NO] = '{}ock Mouse <{}>'.format(
                'Unl' if self.__mouse_locked else 'L', self.__lock_mouse_key_txt)
        (self.__side_no, self.__side_full_txt, self.__side_page, self.__side_txt
        )   = self.__generate_side_args('init', MAIN_MENU, side_full_txt)
        self.__render_main()
        self.__log_write(4, 'Init side menu to main menu')

    def __warnpopup_click(self, cur):
        res = self.__warnpopup.click(cur)
        if not res:
            return
        if res['result'] == 'out of box':
            self.__log_write(4, 'Clicked out of WarnPopup')
            return
        self.__log_write(4, 'Clicked WarnPopup "%s" button' %res['result'].capitalize())
        if res['result'] == 'confirm':
            if self.__warnpopup.send_command not in range(TOTAL_SEND_CMD):
                self.__log_write(1, 'WarnPopup saved an unkown send command number <%d>' %self.__warnpopup.send_command)
                return
            iKvmClient.__SEND_COMMAND_ACTION_SWITCH[self.__warnpopup.send_command](self)

    def __send_short_power(self):
        res = self.__ikvm.send_atx('short power')
        if res['result'] == 'success':
            self.__log_write(3, 'Send short power atx signal to controled host sucess')
        else:
            self.__log_write(2, 'Send short power atx signal to controled host failed. Detail: ' + res['detail'])

    def __send_reset(self):
        res = self.__ikvm.send_atx('reset')
        if res['result'] == 'success':
            self.__log_write(3, 'Send reset atx signal to controled host sucess')
        else:
            self.__log_write(2, 'Send reset atx signal to controled host failed. Detail: ' + res['detail'])

    def __send_long_power(self):
        res = self.__ikvm.send_atx('long power')
        if res['result'] == 'success':
            self.__log_write(3, 'Send long power atx signal to controled host sucess')
        else:
            self.__log_write(2, 'Send long power atx signal to controled host failed. Detail: ' + res['detail'])

    def __send_ctrl_alt_del(self):
        self.__ikvm.release_keys()
        self.__log_write(4, 'Release all pressed key before send "Ctrl+Alt+Del"')
        cmds = (('press', ARDUINO_KEY_MAP['KEY_LEFT_CTRL']),
                ('press', ARDUINO_KEY_MAP['KEY_LEFT_ALT']),
                ('press', ARDUINO_KEY_MAP['KEY_DELETE']),
                ('release', ARDUINO_KEY_MAP['KEY_LEFT_CTRL']),
                ('release', ARDUINO_KEY_MAP['KEY_LEFT_ALT']),
                ('release', ARDUINO_KEY_MAP['KEY_DELETE']),)
        is_fail = False
        for act, key in cmds:
            res = self.__ikvm.send_key(act, key)
            is_fail = is_fail if res['result'] == 'success' else True
        if not is_fail:
            self.__log_write(3, 'Send "Ctrl+Alt+Del" to controled host sucess')
        else:
            self.__log_write(2, 'Send "Ctrl+Alt+Del" to controled host failed')

    __SEND_COMMAND_ACTION_SWITCH = {
            SHORT_PWR_NO: __send_short_power,
            RESET_NO: __send_reset,
            LONG_PWR_NO: __send_long_power,
            C_A_DEL_NO: __send_ctrl_alt_del,
    }

    def __inputpopup_commit(self, send_txt):
        if not send_txt: # not send empty text
            self.__log_write(4, 'Not send empty input')
            return
        if len(send_txt) > 0x10000: # exceed quarter size of unsigned short, protocol prohibit
            send_txt = send_txt[:0xFFFF]
            self.__log_write(3, 'Send text exceed the size 65535, truncated')
        res = self.__ikvm.send_text(send_txt)
        is_success = res['result'] == 'success'
        send_txt = send_txt[:LOG_SEND_TXT_MAX_SHOW]
        self.__log_write(3 if is_success else 2, 'Send text started with => %s <= to iKVM %s' %(
            raw(send_txt), 'success' if is_success else ('failed. Detail: '+res['detail'])))

    def __inputpopup_click(self, cur):
        res = self.__inputpopup.click(cur)
        if not res:
            return
        self.__log_write(4, 'Clicked InputPopup "%s" button' %res['result'].capitalize())
        if res['result'] == 'confirm': 
            self.__inputpopup_commit(res['detail'])

    def __set_lock_mouse_popup_click(self, cur):
        res = self.__set_lock_mouse_popup.click(cur)
        if not res:
            return
        if res['result'] == 'out of box':
            self.__log_write(4, 'Clicked out of SetLockMousePopup')
            return
        self.__log_write(4, 'Clicked SetLockMousePopup "%s" button' %res['result'].capitalize())
        if res['result'] == 'confirm':
            key = res['detail']
            if not (key in PYGAME_KEY_MAP or key in PYGAME_EXTRA_KEY_MAP or key in range(0x80)):
                self.__log_write(1, f'SetLockMousePopup saved an unkown lock key <{key}>')
                return
            key_txt = self.__set_lock_mouse_popup.lock_txt
            self.__log_write(3, f'Set the lock mouse key as <{key_txt}>')
            self.__lock_mouse_key = key
            self.__lock_mouse_key_txt = key_txt
            self.__to_main_menu()

    def __scroll_page(self, py_event):
        total = len(self.__side_full_txt)
        avail = self.__side_show_max if self.__side_no == MAIN_MENU else self.__side_show_max-1
        if ceil(total/avail) == 1: # return if total page is one
            return

        is_up = py_event == MOUSE_WHEEL_UP
        act = 'previous' if is_up else 'next'
        (self.__side_no, self.__side_full_txt, self.__side_page, self.__side_txt
        )   = self.__generate_side_args(act, self.__side_no, self.__side_full_txt)
        self.__render_main()
        self.__log_write(4, 'Side menu changed: mouse scroll wheel ' + ('up' if is_up else 'down'))

    def __main_menu_button_action(self, cur):
        if self.__in_side_page(FULLSCREEN_NO) and self.__in_button(cur, FULLSCREEN_NO):
            ## Set GUI to fullscreen or window
            self.__log_write(4, 'Clicked "%s" button' %self.__side_full_txt[FULLSCREEN_NO])
            self.__fullscreen = not self.__fullscreen
            # Re-render GUI
            self.__side_show_max = self.__compute_side_show_max() # pre-compute for invocation of __generate_side_args
            self.__to_main_menu()
            # Re-generate All Popups components
            cur_w, cur_h = pygame.display.Info().current_w, pygame.display.Info().current_h
            x, y = (1-WARN_W_SCALE)*cur_w/2, (1-WARN_H_SCALE)*cur_h/2
            w, h = cur_w*WARN_W_SCALE, cur_h*WARN_H_SCALE
            self.__warnpopup.generate_components(x, y, w, h)

            x, y = (1-LOCK_W_SCALE)*cur_w/2, (1-LOCK_H_SCALE)*cur_h/2
            w, h = cur_w*LOCK_W_SCALE, cur_h*LOCK_H_SCALE
            self.__set_lock_mouse_popup.generate_components(x, y, w, h)

            x, y = (1-INPUT_W_SCALE)*cur_w/2, (1-INPUT_H_SCALE)*cur_h/2
            w, h = cur_w*INPUT_W_SCALE, cur_h*INPUT_H_SCALE
            self.__inputpopup.generate_components(x, y, w, h)

        elif self.__in_side_page(ALT_SERIAL_NO) and self.__in_button(cur, ALT_SERIAL_NO):
            ## Goto alternates serial device menu
            self.__log_write(4, 'Clicked "%s" button' %self.__side_full_txt[ALT_SERIAL_NO])
            if not self.__serials:
                res = self.__ikvm.list_serial_devices()
                if res['result'] != 'success':
                    self.__log_write(2, 'List serial device from iKVM failed. Detail: ' + res['detail'])
                    return
                self.__serials = res['detail']
            (self.__side_no, self.__side_full_txt, self.__side_page, self.__side_txt
            )   = self.__generate_side_args(
                    'init', SERIAL_MENU, ['{} {:04X}:{:04X}'.format(*uart) for uart in self.__serials])
            self.__render_main()

        elif self.__in_side_page(ALT_CAPTURE_NO) and self.__in_button(cur, ALT_CAPTURE_NO):
            ## Goto alternates video capture device menu
            self.__log_write(4, 'Clicked "%s" button' %self.__side_full_txt[ALT_CAPTURE_NO])
            if not self.__caps:
                res = self.__ikvm.list_captures()
                if res['result'] != 'success':
                    self.__log_write(2, 'List video capture from iKVM failed. Detail: ' + res['detail'])
                    return
                self.__caps = res['detail']
            (self.__side_no, self.__side_full_txt, self.__side_page, self.__side_txt
            )   = self.__generate_side_args('init', CAPTURE_MENU, [cap[0] for cap in self.__caps])
            self.__render_main()

        elif self.__in_side_page(SEND_CMD_NO) and self.__in_button(cur, SEND_CMD_NO):
            ## Goto send atx/hotkeys command
            self.__log_write(4, 'Clicked "%s" button' %self.__side_full_txt[SEND_CMD_NO])
            (self.__side_no, self.__side_full_txt, self.__side_page, self.__side_txt
            )   = self.__generate_side_args('init', SEND_MENU, SEND_MENU_FULL_TXT)
            self.__render_main()

        elif self.__in_side_page(SCREENSHOT_NO) and self.__in_button(cur, SCREENSHOT_NO):
            ## Take a screenshot and save to program running folder
            self.__log_write(4, 'Clicked "%s" button' %self.__side_full_txt[SCREENSHOT_NO])
            cap_img = self.__fetch_frame()
            if cap_img is None:
                self.__log_write(3, 'Take a screenshot failed')
                return
            filename = 'Screenshot_{}.jpg'.format(datetime.now().strftime('%Y%m%d-%H%M%S'))
            with open(filename, 'wb') as f:
                f.write(cap_img)
            self.__log_write(3, 'Screenshot saved to "%s"' %os.path.join(os.getcwd(), filename))

        elif self.__in_side_page(SEND_TXT_NO) and self.__in_button(cur, SEND_TXT_NO):
            ## Open InputPopup box that can take keyboard input as text and send text to controled device
            self.__log_write(4, 'Clicked "%s" button' %self.__side_full_txt[SEND_TXT_NO])
            self.__inputpopup.show = not self.__inputpopup.show

        elif self.__in_side_page(SET_LOCK_KEY_NO) and self.__in_button(cur, SET_LOCK_KEY_NO):
            self.__log_write(4, 'Clicked "%s" button' %self.__side_full_txt[SET_LOCK_KEY_NO])
            self.__set_lock_mouse_popup.show = not self.__set_lock_mouse_popup.show

        elif self.__in_side_page(HOOK_KEY_NO) and self.__in_button(cur, HOOK_KEY_NO):
            ## Enable or disable keyboard hook, Windows only
            self.__log_write(4, 'Clicked "%s" button' %self.__side_full_txt[HOOK_KEY_NO])
            if OS != 'WINDOWS':
                return
            ## (Un)Hook all keys
            keyboard.unhook_all() if self.__hooked else keyboard.hook(self.__hook_key, suppress=True)
            self.__hooked = not self.__hooked
            self.__to_main_menu() # re-render gui
            self.__log_write(3, 'Keyboard {}hooked'.format('' if self.__hooked else 'un'))

    def __serial_menu_button_action(self, cur):
        total = len(self.__side_full_txt)
        for i in range(total):
            if self.__in_side_page(i) and self.__in_button(cur, i):
                self.__log_write(4, 'Clicked "%s" button in serial menu' %self.__side_full_txt[i])

                # Open/Re-open serial device
                device = self.__serials[i][0]
                self.__open_serial_device(device)

                # Return to main menu
                self.__to_main_menu()
                return
        # Back to main menu
        end = self.__back_button_no(cur)
        if self.__in_visible_button(cur, end):
            self.__log_write(4, 'Clicked "%s" button in serial menu' %self.__side_txt[end])
            self.__to_main_menu()

    def __capture_menu_button_action(self, cur):
        total = len(self.__side_full_txt)
        for i in range(total):
            if self.__in_side_page(i) and self.__in_button(cur, i):
                self.__log_write(4, 'Clicked "%s" button in capture menu' %self.__side_full_txt[i])
                # Next to resolution menu
                self.__cap_menu_loc = [i,] # locate what capture be selected in next-level menu
                (self.__side_no, self.__side_full_txt, self.__side_page, self.__side_txt
                )   = self.__generate_side_args(
                        'init', RESOLUTION_MENU, ['%dx%d' %(*reso[0],) for reso in self.__caps[i][1]])
                self.__render_main()
                return
        # Back to main menu
        end = self.__back_button_no(cur)
        if self.__in_visible_button(cur, end):
            self.__log_write(4, 'Clicked "%s" button in capture menu' %self.__side_txt[end])
            self.__to_main_menu()

    def __resolution_menu_button_action(self, cur):
        total = len(self.__side_full_txt)
        for j in range(total):
            if self.__in_side_page(j) and self.__in_button(cur, j):
                self.__log_write(4, 'Clicked "%s" button in resolution menu' %self.__side_full_txt[j])
                # Next to frame rate menu
                i = self.__cap_menu_loc[0]
                self.__cap_menu_loc.append(j) # locate what resolution be selected in next-level menu
                (self.__side_no, self.__side_full_txt, self.__side_page, self.__side_txt
                )   = self.__generate_side_args(
                        'init', FRAMERATE_MENU, ['%d fps' %fps for fps in self.__caps[i][1][j][1]])
                self.__render_main()
                return
        # Back to capture menu
        end = self.__back_button_no(cur)
        if self.__in_visible_button(cur, end):
            self.__log_write(4, 'Clicked "%s" button in resolution menu' %self.__side_txt[end])
            (self.__side_no, self.__side_full_txt, self.__side_page, self.__side_txt
            )   = self.__generate_side_args(
                    'init', CAPTURE_MENU, [cap[0] for cap in self.__caps])
            self.__render_main()

    def __frame_rate_menu_button_action(self, cur):
        total = len(self.__side_full_txt)
        for k in range(total):
            if self.__in_side_page(k) and self.__in_button(cur, k):
                self.__log_write(4, 'Clicked "%s" button in frame rate menu' %self.__side_full_txt[k])

                # found selected video capture and specifications
                i = self.__cap_menu_loc[0]
                j = self.__cap_menu_loc[1]
                device = self.__caps[i][0]
                resolution = self.__caps[i][1][j][0]
                fps = self.__caps[i][1][j][1][k]

                # close mjpg client
                self.__capture.close()
                # Restart MJPG-Streamer with specific arguments
                if not self.__alt_capture(device, resolution, fps):
                    return
                # Re-open mjpg client
                if not self.__connect_mjpg():
                    return

                # Return to main menu
                self.__to_main_menu()
                return
        # Back to resolution menu
        end = self.__back_button_no(cur)
        if self.__in_visible_button(cur, end):
            self.__log_write(4, 'Clicked "%s" button in frame rate menu' %self.__side_txt[end])
            i = self.__cap_menu_loc[0]
            self.__cap_menu_loc = [i,] # locate what capture be selected in next-level menu
            (self.__side_no, self.__side_full_txt, self.__side_page, self.__side_txt
            )   = self.__generate_side_args(
                    'init', RESOLUTION_MENU, ['%dx%d' %(*reso[0],) for reso in self.__caps[i][1]])
            self.__render_main()

    def __send_menu_button_action(self, cur):
        # Back to main menu
        end = self.__back_button_no(cur)
        if self.__in_visible_button(cur, end):
            self.__log_write(4, 'Clicked "%s" button in send command menu' %self.__side_txt[end])
            self.__to_main_menu()
            return
        if self.__in_side_page(SHORT_PWR_NO) and self.__in_button(cur, SHORT_PWR_NO):
            self.__log_write(4, 'Clicked "%s" button' %self.__side_full_txt[SHORT_PWR_NO])
            self.__warnpopup.show = not self.__warnpopup.show
            self.__warnpopup.send_command = SHORT_PWR_NO

        elif self.__in_side_page(RESET_NO) and self.__in_button(cur, RESET_NO):
            self.__log_write(4, 'Clicked "%s" button' %self.__side_full_txt[RESET_NO])
            self.__warnpopup.show = not self.__warnpopup.show
            self.__warnpopup.send_command = RESET_NO

        elif self.__in_side_page(LONG_PWR_NO) and self.__in_button(cur, LONG_PWR_NO):
            self.__log_write(4, 'Clicked "%s" button' %self.__side_full_txt[LONG_PWR_NO])
            self.__warnpopup.show = not self.__warnpopup.show
            self.__warnpopup.send_command = LONG_PWR_NO

        elif self.__in_side_page(C_A_DEL_NO) and self.__in_button(cur, C_A_DEL_NO):
            self.__log_write(4, 'Clicked "%s" button' %self.__side_full_txt[C_A_DEL_NO])
            self.__warnpopup.show = not self.__warnpopup.show
            self.__warnpopup.send_command = C_A_DEL_NO
        # Do not return to main menu, stay in send menu

    __BUTTON_ACTION_SWITCH = {
            MAIN_MENU: __main_menu_button_action,
            SERIAL_MENU: __serial_menu_button_action,
            CAPTURE_MENU: __capture_menu_button_action,
            RESOLUTION_MENU: __resolution_menu_button_action,
            FRAMERATE_MENU: __frame_rate_menu_button_action,
            SEND_MENU: __send_menu_button_action,
    }

    def __keyboard_input_event(self, py_event, cur_in_cap):
        if self.__warnpopup.show:
            self.__warnpopup.input_key(py_event) # input into warnpopup box
        elif self.__inputpopup.show:
            res = self.__inputpopup.input_key(py_event) # input into inputpopup box
            if res and res['result'] == 'ctrl+enter': # user type hotkey <C-CR>
                self.__log_write(4, 'Input Ctrl+Enter in InputPopup')
                self.__inputpopup_commit(res['detail'])
        elif self.__set_lock_mouse_popup.show: # input into set lock mouse popup
            self.__set_lock_mouse_popup.input_key(py_event)
        elif cur_in_cap:
            if py_event.key == self.__lock_mouse_key: # prevent the setted lock mouse key written into ikvm
                if py_event.type == pygame.KEYUP:
                    # trigger the key that will lock/unlock the mouse in the video capture area
                    self.__mouse_locked = not self.__mouse_locked
                    self.__log_write(3, '{}ocked mouse'.format('L' if self.__mouse_locked else 'Unl'))
                    self.__to_main_menu()
                return
            self.__type_key(py_event.type, py_event.key) # send a key to ikvm

    def __type_key(self, act, py_key):
        press = (act == pygame.KEYDOWN)
        press_txt = 'Pressed' if press else 'Released'

        if py_key in PYGAME_KEY_MAP: # Special keyboard keys
            key = ARDUINO_KEY_MAP[PYGAME_KEY_MAP[py_key]]
            self.__log_write(4, '{} {} <{:02X}>'.format(press_txt, PYGAME_KEY_MAP[py_key], key))
        elif py_key in range(0x80): # ASCII key only
            key = py_key
            self.__log_write(4, '{} "{}" <{:02X}>'.format(press_txt, chr(key), key))
        else:
            key = None
            py_key = PYGAME_EXTRA_KEY_MAP[py_key] if py_key in PYGAME_EXTRA_KEY_MAP else py_key
            self.__log_write(4, '{} an invalid key: {}'.format(press_txt, py_key))

        press_txt = 'press' if press else 'release'
        res = self.__ikvm.send_key(press_txt, key) if key else {'result': 'success'}
        if res['result'] != 'success':
            self.__log_write(2, 'Send {} key <{:02X}> to iKVM failed'.format(press_txt, key))

    def __mouse_move_event(self, cur_in_cap):
        if self.__warnpopup.show or self.__inputpopup.show or self.__set_lock_mouse_popup.show:
            return
        if not self.__mouse_locked and not cur_in_cap: # return when mouse locked as cursor not in video capture
            return

        # get the shifted coordinates
        rel = tuple(map(lambda x: x if abs(x)<128 else int(copysign(127, x)), pygame.mouse.get_rel()))
        if rel == (0, 0): # cursor not moved, return
            return
        self.__ikvm.move_mouse(*rel)
        if self.__mouse_locked: # if lock mouse key is pressed, set mouse position into video capture area center
            x, y = tuple(map(lambda x: x/2, self.__cap_res))
            pygame.mouse.set_pos(x, y)
