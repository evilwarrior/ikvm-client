# coding: utf-8

import pygame
from platform import system

# generals
OS = system().upper()
LOG_LEVEL = ('FATAL', 'ERROR', 'WARN', 'INFO', 'DEBUG', 'TRACE')
LOG_BUFSIZE = 1
LOG_SEND_TXT_MAX_SHOW = 50 # the max length of send text can be written into logfile
RETRY = 3 # Retry whenever start service failed

# Pygame global variables
BG_COLOR        = (40, 40, 40)
SIDE_W, SIDE_H  = 240, 135
TXT_COLOR       = (51, 255, 51)
BTN_COLOR_LIGHT = (100, 149, 104)
BTN_COLOR_DARK  = (43, 83, 41)
BTN_AND_PAD_H   = 96
BTN_W_SCALE     = 0.8
BTN_H_SCALE     = 0.5
POPUP_MARGIN    = 20
BORDER_THICK    = 2
BORDER_COLOR    = (100, 149, 104)
WARN_W_SCALE    = 0.55
WARN_H_SCALE    = 0.35
WARN_TXT_SIZE   = 24
WARN_SCALE      = 0.8
LOCK_W_SCALE    = 0.5
LOCK_H_SCALE    = 0.35
LOCK_TXT_SIZE   = 25
LOCK_SCALE      = 0.8
INPUT_W_SCALE   = 0.75
INPUT_H_SCALE   = 0.65
INPUT_TXT_SIZE  = 16
INPUT_BG_COLOR  = (63, 63, 63)
INPUTBOX_PAD    = 7
INPUTBOX_SCALE  = 0.85
TAB_SCALE       = 0.066

SMALL_BTN_TXT_SCALE  = 0.3
MIDDLE_BTN_TXT_SCALE = 0.36
BIG_BTN_TXT_SCALE    = 0.5

# Main menu items
FULLSCREEN_NO   = 0
ALT_SERIAL_NO   = 1
ALT_CAPTURE_NO  = 2
SEND_CMD_NO     = 3
SCREENSHOT_NO   = 4
SEND_TXT_NO     = 5
SET_LOCK_KEY_NO = 6
HOOK_KEY_NO     = 7

# Send command menu items
SHORT_PWR_NO    = 0
RESET_NO        = 1
LONG_PWR_NO     = 2
C_A_DEL_NO      = 3
TOTAL_SEND_CMD  = 4

# Default menu items text
MAIN_MENU_FULL_TXT = ['', 'Alt Serial', 'Alt Video', 'Send Command', 'Screenshot', 'Send Text', '',]
if OS == 'WINDOWS':
    MAIN_MENU_FULL_TXT.append('')
SEND_MENU_FULL_TXT = ['Short Power', 'Reset', 'Long Power', 'Ctrl+Alt+Del',]

# Selected menu number
MAIN_MENU       = 0
SERIAL_MENU     = 1
CAPTURE_MENU    = 2
RESOLUTION_MENU = 3
FRAMERATE_MENU  = 4
SEND_MENU       = 5
TOTAL_MENU      = 6

MOUSE_LEFT       = 1
MOUSE_MIDDLE     = 2
MOUSE_RIGHT      = 3
MOUSE_WHEEL_UP   = 4
MOUSE_WHEEL_DOWN = 5

PYGAME_MOUSE_MAP = {
        MOUSE_LEFT: "MOUSE_LEFT",
        MOUSE_MIDDLE: "MOUSE_MIDDLE",
        MOUSE_RIGHT: "MOUSE_RIGHT",}

ARDUINO_MOUSE_MAP = {
        "MOUSE_LEFT": 1,
        "MOUSE_MIDDLE": 4,
        "MOUSE_RIGHT": 2,}

HOOK_KEY_MAP = {
        "esc":pygame.K_ESCAPE,
        "f1":pygame.K_F1,
        "f2":pygame.K_F2,
        "f3":pygame.K_F3,
        "f4":pygame.K_F4,
        "f5":pygame.K_F5,
        "f6":pygame.K_F6,
        "f7":pygame.K_F7,
        "f8":pygame.K_F8,
        "f9":pygame.K_F9,
        "f10":pygame.K_F10,
        "f11":pygame.K_F11,
        "f12":pygame.K_F12,
        "f13":pygame.K_F13,
        "f14":pygame.K_F14,
        "f15":pygame.K_F15,
        "f16":1073741931,
        "f17":1073741932,
        "f18":1073741933,
        "f19":1073741934,
        "f20":1073741935,
        "f21":1073741936,
        "f22":1073741937,
        "f23":1073741938,
        "f24":1073741939,
        "print screen":pygame.K_PRINT,
        "scroll lock":pygame.K_SCROLLOCK,
        "pause":pygame.K_PAUSE,
        "insert":pygame.K_INSERT,
        "home":pygame.K_HOME,
        "page up":pygame.K_PAGEUP,
        "delete":pygame.K_DELETE,
        "end":pygame.K_END,
        "page down":pygame.K_PAGEDOWN,
        "up":pygame.K_UP,
        "down":pygame.K_DOWN,
        "left":pygame.K_LEFT,
        "right":pygame.K_RIGHT,
        "num lock":pygame.K_NUMLOCK,
        "`":pygame.K_BACKQUOTE,
        "0":pygame.K_0,
        "1":pygame.K_1,
        "2":pygame.K_2,
        "3":pygame.K_3,
        "4":pygame.K_4,
        "5":pygame.K_5,
        "6":pygame.K_6,
        "7":pygame.K_7,
        "8":pygame.K_8,
        "9":pygame.K_9,
        "-":pygame.K_MINUS,
        "=":pygame.K_EQUALS,
        "a":pygame.K_a,
        "b":pygame.K_b,
        "c":pygame.K_c,
        "d":pygame.K_d,
        "e":pygame.K_e,
        "f":pygame.K_f,
        "g":pygame.K_g,
        "h":pygame.K_h,
        "i":pygame.K_i,
        "j":pygame.K_j,
        "k":pygame.K_k,
        "l":pygame.K_l,
        "m":pygame.K_m,
        "n":pygame.K_n,
        "o":pygame.K_o,
        "p":pygame.K_p,
        "q":pygame.K_q,
        "r":pygame.K_r,
        "s":pygame.K_s,
        "t":pygame.K_t,
        "u":pygame.K_u,
        "v":pygame.K_v,
        "w":pygame.K_w,
        "x":pygame.K_x,
        "y":pygame.K_y,
        "z":pygame.K_z,
        "[":pygame.K_LEFTBRACKET,
        "]":pygame.K_RIGHTBRACKET,
        "\\":pygame.K_BACKSLASH,
        ";":pygame.K_SEMICOLON,
        "'":pygame.K_QUOTE,
        ",":pygame.K_COMMA,
        ".":pygame.K_PERIOD,
        "/":pygame.K_SLASH,
        "~":pygame.K_BACKQUOTE,
        ")":pygame.K_0,
        "!":pygame.K_1,
        "@":pygame.K_2,
        "#":pygame.K_3,
        "$":pygame.K_4,
        "%":pygame.K_5,
        "^":pygame.K_6,
        "&":pygame.K_7,
        "*":pygame.K_8,
        "(":pygame.K_9,
        "_":pygame.K_MINUS,
        "+":pygame.K_EQUALS,
        "A":pygame.K_a,
        "B":pygame.K_b,
        "C":pygame.K_c,
        "D":pygame.K_d,
        "E":pygame.K_e,
        "F":pygame.K_f,
        "G":pygame.K_g,
        "H":pygame.K_h,
        "I":pygame.K_i,
        "J":pygame.K_j,
        "K":pygame.K_k,
        "L":pygame.K_l,
        "M":pygame.K_m,
        "N":pygame.K_n,
        "O":pygame.K_o,
        "P":pygame.K_p,
        "Q":pygame.K_q,
        "R":pygame.K_r,
        "S":pygame.K_s,
        "T":pygame.K_t,
        "U":pygame.K_u,
        "V":pygame.K_v,
        "W":pygame.K_w,
        "X":pygame.K_x,
        "Y":pygame.K_y,
        "Z":pygame.K_z,
        "{":pygame.K_LEFTBRACKET,
        "}":pygame.K_RIGHTBRACKET,
        "|":pygame.K_BACKSLASH,
        ":":pygame.K_SEMICOLON,
        '"':pygame.K_QUOTE,
        "<":pygame.K_COMMA,
        ">":pygame.K_PERIOD,
        "?":pygame.K_SLASH,
        "backspace":pygame.K_BACKSPACE,
        "tab": pygame.K_TAB,
        "caps lock":pygame.K_CAPSLOCK,
        "enter":pygame.K_RETURN,
        "space":pygame.K_SPACE,
        "shift":pygame.K_LSHIFT,
        "right shift":pygame.K_RSHIFT,
        "ctrl":pygame.K_LCTRL,
        "right ctrl":pygame.K_RCTRL,
        "alt":pygame.K_LALT,
        "right alt":pygame.K_RALT,
        "left windows":pygame.K_LSUPER,
        "right windows":pygame.K_RSUPER,
        "menu": 1073741925,
        "browser search key":1073742092,
        "browser start and home":1073742093,
        "browser back":1073742094,
        "browser forward":1073742095,
        "browser stop":1073742096,
        "browser refresh":1073742097,
        "browser favorites":1073742098,
        "volume up":1073741952,
        "volume down":1073741953,
        "next track":1073742082,
        "previous track":1073742083,
        "stop media":1073742084,
        "play/pause media":1073742085,
        "volume mute":1073742086,
        "select media":1073742098,
        "start mail":1073742089,
        }

HOOK_KP_MAP = {
        "num lock":pygame.K_NUMLOCK,
        "/":pygame.K_KP_DIVIDE,
        "*":pygame.K_KP_MULTIPLY,
        "-":pygame.K_KP_MINUS,
        "+":pygame.K_KP_PLUS,
        "0":pygame.K_KP0,
        "1":pygame.K_KP1,
        "2":pygame.K_KP2,
        "3":pygame.K_KP3,
        "4":pygame.K_KP4,
        "5":pygame.K_KP5,
        "6":pygame.K_KP6,
        "7":pygame.K_KP7,
        "8":pygame.K_KP8,
        "9":pygame.K_KP9,
        "decimal":pygame.K_KP_PERIOD,
        "insert":pygame.K_KP0,
        "end":pygame.K_KP1,
        "down":pygame.K_KP2,
        "page down":pygame.K_KP3,
        "left":pygame.K_KP4,
        "clear":pygame.K_KP5,
        "right":pygame.K_KP6,
        "home":pygame.K_KP7,
        "up":pygame.K_KP8,
        "page up":pygame.K_KP9,
        "delete":pygame.K_KP_PERIOD,
        "enter":pygame.K_KP_ENTER,}

HOOK_BUG_KEYS = ('Q', 'P', 'D', 'F', 'G', 'J', 'C', 'B', 'M', '-', '+', '*',)

PYGAME_KEY_MAP = {
    pygame.K_LCTRL:"KEY_LEFT_CTRL",
    pygame.K_LSHIFT:"KEY_LEFT_SHIFT",
    pygame.K_LALT:"KEY_LEFT_ALT",
    pygame.K_LSUPER:"KEY_LEFT_GUI",
    pygame.K_RCTRL:"KEY_RIGHT_CTRL",
    pygame.K_RSHIFT:"KEY_RIGHT_SHIFT",
    pygame.K_RALT:"KEY_RIGHT_ALT",
    pygame.K_RSUPER:"KEY_RIGHT_GUI",
    pygame.K_UP:"KEY_UP_ARROW",
    pygame.K_DOWN:"KEY_DOWN_ARROW",
    pygame.K_LEFT:"KEY_LEFT_ARROW",
    pygame.K_RIGHT:"KEY_RIGHT_ARROW",
    pygame.K_BACKSPACE:"KEY_BACKSPACE",
    pygame.K_TAB:"KEY_TAB",
    pygame.K_RETURN:"KEY_RETURN",
    pygame.K_PAUSE:"KEY_PAUSE",
    pygame.K_ESCAPE:"KEY_ESC",
    pygame.K_INSERT:"KEY_INSERT",
    pygame.K_DELETE:"KEY_DELETE",
    pygame.K_PAGEUP:"KEY_PAGE_UP",
    pygame.K_PAGEDOWN:"KEY_PAGE_DOWN",
    pygame.K_HOME:"KEY_HOME",
    pygame.K_END:"KEY_END",
    pygame.K_NUMLOCK:"KEY_NUM_LOCK",
    pygame.K_CAPSLOCK:"KEY_CAPS_LOCK",
    pygame.K_SCROLLOCK:"KEY_SCROLL_LOCK",
    pygame.K_PRINT:"KEY_PRINT_SCREEN",
    pygame.K_F1:"KEY_F1",
    pygame.K_F2:"KEY_F2",
    pygame.K_F3:"KEY_F3",
    pygame.K_F4:"KEY_F4",
    pygame.K_F5:"KEY_F5",
    pygame.K_F6:"KEY_F6",
    pygame.K_F7:"KEY_F7",
    pygame.K_F8:"KEY_F8",
    pygame.K_F9:"KEY_F9",
    pygame.K_F10:"KEY_F10",
    pygame.K_F11:"KEY_F11",
    pygame.K_F12:"KEY_F12",
    pygame.K_F13:"KEY_F13",
    pygame.K_F14:"KEY_F14",
    pygame.K_F15:"KEY_F15",
    1073741931:"KEY_F16",
    1073741932:"KEY_F17",
    1073741933:"KEY_F18",
    1073741934:"KEY_F19",
    1073741935:"KEY_F20",
    1073741936:"KEY_F21",
    1073741937:"KEY_F22",
    1073741938:"KEY_F23",
    1073741939:"KEY_F24",
    pygame.K_KP0:"KEY_KP_0",
    pygame.K_KP1:"KEY_KP_1",
    pygame.K_KP2:"KEY_KP_2",
    pygame.K_KP3:"KEY_KP_3",
    pygame.K_KP4:"KEY_KP_4",
    pygame.K_KP5:"KEY_KP_5",
    pygame.K_KP6:"KEY_KP_6",
    pygame.K_KP7:"KEY_KP_7",
    pygame.K_KP8:"KEY_KP_8",
    pygame.K_KP9:"KEY_KP_9",
    pygame.K_KP_PERIOD:"KEY_KP_DOT",
    pygame.K_KP_DIVIDE:"KEY_KP_SLASH",
    pygame.K_KP_MULTIPLY:"KEY_KP_ASTERISK",
    pygame.K_KP_MINUS:"KEY_KP_MINUS",
    pygame.K_KP_PLUS:"KEY_KP_PLUS",
    pygame.K_KP_ENTER:"KEY_KP_ENTER",
    pygame.K_MENU:"KEY_MENU",
    1073741925:"KEY_MENU",}

ARDUINO_KEY_MAP = {
    "KEY_LEFT_CTRL":128,
    "KEY_LEFT_SHIFT":129,
    "KEY_LEFT_ALT":130,
    "KEY_LEFT_GUI":131,
    "KEY_RIGHT_CTRL":132,
    "KEY_RIGHT_SHIFT":133,
    "KEY_RIGHT_ALT":134,
    "KEY_RIGHT_GUI":135,
    "KEY_UP_ARROW":218,
    "KEY_DOWN_ARROW":217,
    "KEY_LEFT_ARROW":216,
    "KEY_RIGHT_ARROW":215,
    "KEY_BACKSPACE":178,
    "KEY_TAB":179,
    "KEY_RETURN":176,
    "KEY_PAUSE":208,
    "KEY_ESC":177,
    "KEY_INSERT":209,
    "KEY_DELETE":212,
    "KEY_PAGE_UP":211,
    "KEY_PAGE_DOWN":214,
    "KEY_HOME":210,
    "KEY_END":213,
    "KEY_NUM_LOCK":219,
    "KEY_CAPS_LOCK":193,
    "KEY_SCROLL_LOCK":207,
    "KEY_PRINT_SCREEN":206,
    "KEY_F1":194,
    "KEY_F2":195,
    "KEY_F3":196,
    "KEY_F4":197,
    "KEY_F5":198,
    "KEY_F6":199,
    "KEY_F7":200,
    "KEY_F8":201,
    "KEY_F9":202,
    "KEY_F10":203,
    "KEY_F11":204,
    "KEY_F12":205,
    "KEY_F13":240,
    "KEY_F14":241,
    "KEY_F15":242,
    "KEY_F16":243,
    "KEY_F17":244,
    "KEY_F18":245,
    "KEY_F19":246,
    "KEY_F20":247,
    "KEY_F21":248,
    "KEY_F22":249,
    "KEY_F23":250,
    "KEY_F24":251,
    "KEY_KP_0":234,
    "KEY_KP_1":225,
    "KEY_KP_2":226,
    "KEY_KP_3":227,
    "KEY_KP_4":228,
    "KEY_KP_5":229,
    "KEY_KP_6":230,
    "KEY_KP_7":231,
    "KEY_KP_8":232,
    "KEY_KP_9":233,
    "KEY_KP_DOT":235,
    "KEY_KP_SLASH":220,
    "KEY_KP_ASTERISK":221,
    "KEY_KP_MINUS":222,
    "KEY_KP_PLUS":223,
    "KEY_KP_ENTER":224,
    "KEY_MENU":237,}

PYGAME_EXTRA_KEY_MAP = {
    1073741951:"MUTE",
    1073741952:"VOLUMEUP",
    1073741953:"VOLUMEDOWN",
    1073742082:"AUDIONEXT",
    1073742083:"AUDIOPREV",
    1073742084:"AUDIOSTOP",
    1073742085:"AUDIOPLAY",
    1073742086:"AUDIOMUTE",
    1073742098:"MEDIASELECT",
    1073742089:"MAIL",
    1073742092:"AC_SEARCH",
    1073742093:"AC_HOME",
    1073742094:"AC_BACK",
    1073742095:"AC_FORWARD",
    1073742096:"AC_STOP",
    1073742097:"AC_REFRESH",
    1073742098:"AC_BOOKMARKS",}

__all__ = [
        'OS',
        'LOG_LEVEL',
        'LOG_BUFSIZE',
        'LOG_SEND_TXT_MAX_SHOW',
        'RETRY',
        'BG_COLOR',
        'SIDE_W',
        'SIDE_H',
        'TXT_COLOR',
        'BTN_COLOR_LIGHT',
        'BTN_COLOR_DARK',
        'BTN_AND_PAD_H',
        'BTN_W_SCALE',
        'BTN_H_SCALE',
        'POPUP_MARGIN',
        'BORDER_THICK',
        'BORDER_COLOR',
        'WARN_W_SCALE',
        'WARN_H_SCALE',
        'WARN_TXT_SIZE',
        'WARN_SCALE',
        'LOCK_W_SCALE',
        'LOCK_H_SCALE',
        'LOCK_TXT_SIZE',
        'LOCK_SCALE',
        'INPUT_W_SCALE',
        'INPUT_H_SCALE',
        'INPUT_TXT_SIZE',
        'INPUT_BG_COLOR',
        'INPUTBOX_PAD',
        'INPUTBOX_SCALE',
        'TAB_SCALE',
        'SMALL_BTN_TXT_SCALE',
        'MIDDLE_BTN_TXT_SCALE',
        'BIG_BTN_TXT_SCALE',
        'MAIN_MENU_FULL_TXT',
        'SEND_MENU_FULL_TXT',
        'FULLSCREEN_NO',
        'ALT_SERIAL_NO',
        'ALT_CAPTURE_NO',
        'SEND_CMD_NO',
        'SCREENSHOT_NO',
        'SEND_TXT_NO',
        'SET_LOCK_KEY_NO',
        'HOOK_KEY_NO',
        'SHORT_PWR_NO',
        'RESET_NO',
        'LONG_PWR_NO',
        'C_A_DEL_NO',
        'TOTAL_SEND_CMD',
        'MAIN_MENU',
        'SERIAL_MENU',
        'CAPTURE_MENU',
        'RESOLUTION_MENU',
        'FRAMERATE_MENU',
        'SEND_MENU',
        'TOTAL_MENU',
        'MOUSE_LEFT',
        'MOUSE_MIDDLE',
        'MOUSE_RIGHT',
        'MOUSE_WHEEL_UP',
        'MOUSE_WHEEL_DOWN',
        'PYGAME_MOUSE_MAP',
        'ARDUINO_MOUSE_MAP',
        'HOOK_KEY_MAP',
        'HOOK_KP_MAP',
        'HOOK_BUG_KEYS',
        'PYGAME_KEY_MAP',
        'ARDUINO_KEY_MAP',
        'PYGAME_EXTRA_KEY_MAP',
]
