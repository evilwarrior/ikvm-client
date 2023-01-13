# coding: utf-8
if __name__ != 'ikvm.kvm':
    exit()
from . import *
import socket, struct, errno, threading, re
from copy import deepcopy as copy
from time import sleep, time
from functools import partial
from math import gcd

res_scale = lambda w, h: (int(w/gcd(w, h)), int(h/gcd(w, h)))

class Kvm:
    def __init__(self, ip, port,
            mjpg_port, cap_name=None, cap_scale=None, cap_quality='best',
            uart_port=None, usbid=None):
        """ ip, port: required, <str> and <int>

            mjpg_port: required, <int>
                running mjpg-streamer server port on ikvm server

            cap_name: optional, <str>
                specific video capture when starting
                support partial match, e.g. 'video0' can match '/dev/video0'

            cap_scale: optional, <str>/<tuple> with 2 <int>, e.g. '16:9' or (16, 9)
                resolution scale priority, if the scale exists then select, else ignore

            cap_quality: optional, <str>, default 'best'
                stream quality, there are two options, 'best' and 'worst'
                'best' select the resolution with maximal area and maximal fps
                'worst' select the resolution with minimal area and minimal fps

            uart_port: optional, <str>
                specific serial device name
                support partial match, e.g. 'USB0' can match '/dev/ttyUSB0'

            usbid: optional, <str>/<>
                specific serial device vid:pid, ignore when uart_port specified
        """
        self.ip = ip
        self.port = port
        self.mjpg_port = mjpg_port
        self.cap_name = cap_name
        self.cap_scale = cap_scale
        self.cap_quality = cap_quality
        self.uart_port = uart_port
        self.usbid = usbid
        self.__run = False
        self.__sock = None

    def __setattr__(self, key, value):
        if key in ('ip',):
            assert isinstance(value, str)
            self.__dict__[key] = value
        elif key in ('port', 'mjpg_port',):
            assert value in range(1, 0x10000)
            self.__dict__[key] = value
        elif key in ('cap_name', 'uart_port',):
            assert isinstance(value, (str, type(None)))
            self.__dict__[key] = value
        elif key == 'cap_scale':
            if isinstance(value, str) and re.match(r'^\d+:\d+$', value):
                self.__dict__[key] = tuple(map(int, value.split(':')))
            elif value is None or(
                    isinstance(value, tuple) and
                    len(value) == 2 and
                    all([x in range(1, 0x10000) for x in value])):
                self.__dict__[key] = value
            else:
                raise TypeError("Type of cap_scale should be None, <str> or <tuple> with 2 <int>, "\
                        "and value should between 0 and 65535, e.g. '16:9' or (16, 9)")
        elif key == 'cap_quality':
            assert value in ('best', 'worst')
            self.__dict__[key] = value
        elif key == 'usbid':
            if isinstance(value, str) and re.match(r'^[A-Fa-f0-9]{1,4}:[A-Fa-f0-9]{1,4}$', value):
                self.__dict__[key] = tuple(map(partial(int, base=16), value.split(':')))
            elif value is None or(
                    isinstance(value, tuple) and
                    len(value) == 2 and
                    all([x in range(1, 0x10000) for x in value])):
                self.__dict__[key] = value
            else:
                raise TypeError( "Type of usbid should be None, <str> or <tuple> with 2 <int>, "\
                        "and value should between 0 and 65535, e.g. '0483:df11' or (0x0483, 0xdf11)")
        else:
            ## No Catch
            self.__dict__[key] = value

    def start(self):
        ## Do handshake with server
        res = self.__hello()
        if res['result'] == 'error':
            res['detail'] = ('Handshake with server failed', res['detail'])
            return res

        ## Successfully established a connection with server
        self.__run = True
        ## registers of response messages resolved from ikvm server
        #  e.g. received msg FF31D5 80 01 0C b'/dev/ttyUSB0' 0483 df11 saved to ->
        #       __resolv_msg[TYPE_LIST_UART_RES] = {
        #           'result': 'success',
        #           'detail': [('/dev/ttyUSB0', 0x0483, 0xdf11),]}
        self.__resolv_msg = dict(zip(Kvm.__RECV_HANDLE_SWITCH, [None for i in range(len(Kvm.__RECV_HANDLE_SWITCH))]))
        self.__lock = threading.Lock()
        self.__condition = threading.Condition()

        threading.Thread(target=self.__recv_handler).start()

        ## Open serial device
        res = self.__uart_select()
        if res['result'] in ('error', 'failure'):
            self.end()
            res['detail'] = (
                'Open serial device {}failed'.format(f'"{self.uart_port}" ' if self.uart_port else ''),
                res['detail']
            )
            return res

        ## Start MJPG-Streamer
        res = self.__capture_select()
        if res['result'] in ('error', 'failure'):
            self.end()
            res['detail'] = ('Start MJPG-Streamer service failed', res['detail'])
            return res

        return {'result': 'success'}

    def end(self):
        if not self.__run:
            return {'result': 'success'}
        ## Quit thread secure
        self.__run = False
        ## Wait thread quit
        with self.__condition:
            self.__condition.wait()
        ## Say goodbye to server w/o receiving response
        res = self.__send(GOODBYE_MSG)
        self.__sock.close()
        return res

    ## non-blocking socket.recv handling process
    def __recv(self):
        try:
            recv = self.__sock.recv(BUF)
            if recv == b'':
                # Disconnected from server sent by FIN
                self.__goodbye()
                return Quit
            return recv
        except socket.error as e:
            if e.args[0] in (errno.EAGAIN, errno.EWOULDBLOCK,):
                # No data yet
                sleep(0.01)
                return None
            elif e.args[0] in (errno.ECONNRESET, errno.ECONNABORTED,):
                # Disconnected from server sent by RST/aborted or connection not established
                self.__goodbye()
                return Quit
            else:
                raise e

    def __recv_handler(self):
        self.__buf = b''
        while self.__run:
            if self.__buf == b'':
                res = self.__recv()
                if res in (None, Quit):
                    continue
                self.__buf += res
            loc = self.__buf.find(MAGIC)
            if loc == -1:
                self.__buf = b''
                continue
            head = self.__buf[loc:][:4] # protocol magic and type
            if len(head) < 4:
                continue
            # Handle response individually (see __RECV_HANDLE_SWITCH for a specific function)
            case = Kvm.__RECV_HANDLE_SWITCH.get(head[-1]) # get function by protocol type
            self.__buf = self.__buf[loc+4:] # trim magic and type
            case(self) if case else None

        ## Thread quit actions
        with self.__condition:
            self.__condition.notify() # Notify main thread thread quit completely

    def __goodbye(self):
        self.__run = False
        self.__sock.close()

    def __handle_ask_alive(self):
        self.__send(REPLY_ALIVE_MSG)

    def __handle_list_uarts_response(self):
        uarts = []
        ## Read number of available serial devices
        uarts_num = 0
        while True:
            if len(self.__buf) == 0:
                res = self.__recv()
                if res is None:
                    continue
                elif res is Quit:
                    return
                self.__buf += res
                continue
            uarts_num = self.__buf[0]
            self.__buf = self.__buf[1:]
            break

        ## Return if no serial devices
        if uarts_num == 0:
            with self.__lock:
                self.__resolv_msg[TYPE_LIST_UART_RES] = {'result': 'success', 'detail': []}
            return

        ## Handle each available serial devices
        for i in range(uarts_num):
            ## Read serial device name
            uart_name = ''
            while True:
                if len(self.__buf) == 0: # for get name length
                    res = self.__recv()
                    if res is None:
                        continue
                    elif res is Quit:
                        return
                    self.__buf += res
                    continue
                uart_name_len = self.__buf[0]
                if uart_name_len == 0:
                    ## Return if no serial device name found
                    with self.__lock:
                        self.__resolv_msg[TYPE_LIST_UART_RES] = {
                                'result': 'error',
                                'detail': 'Server Error: Serial device name length is 0'}
                    return
                elif len(self.__buf)-1 < uart_name_len: # for get name
                    res = self.__recv()
                    if res is None:
                        continue
                    elif res is Quit:
                        return
                    self.__buf += res
                    continue
                try:
                    uart_name = self.__buf[1:][:uart_name_len].decode('utf-8')
                except UnicodeDecodeError:
                    ## Return if serial device name is not UTF-8 encoding
                    with self.__lock:
                        self.__resolv_msg[TYPE_LIST_UART_RES] = {
                                'result': 'error',
                                'detail': 'Protocol Error: Serial device name is not valid UTF-8 encoding'}
                    return
                self.__buf = self.__buf[1+uart_name_len:]
                break

            ## Read serial device vid:pid
            vid, pid = 0, 0
            while True:
                if len(self.__buf) < 4: # for get usb vid:pid
                    res = self.__recv()
                    if res is None:
                        continue
                    elif res is Quit:
                        return
                    self.__buf += res
                    continue
                vid, pid = struct.unpack('!HH', self.__buf[:4])
                self.__buf = self.__buf[4:]
                break

            uarts.append((uart_name, vid, pid))

        ## Success get serial devices information
        with self.__lock:
            self.__resolv_msg[TYPE_LIST_UART_RES] = {'result': 'success', 'detail': copy(uarts)}

    def __handle_list_captures_response(self):
        caps = []
        ## Read number of available serial devices
        caps_num = 0
        while True:
            if len(self.__buf) == 0:
                res = self.__recv()
                if res is None:
                    continue
                elif res is Quit:
                    return
                self.__buf += res
                continue
            caps_num = self.__buf[0]
            self.__buf = self.__buf[1:]
            break

        ## Return if no video captures
        if caps_num == 0:
            with self.__lock:
                self.__resolv_msg[TYPE_LIST_CAP_RES] = {'result': 'success', 'detail': []}
            return

        ## Handle each available video captures
        for i in range(caps_num):
            ## Read video capture name
            cap_name = ''
            while True:
                if len(self.__buf) == 0: # for get length of name
                    res = self.__recv()
                    if res is None:
                        continue
                    elif res is Quit:
                        return
                    self.__buf += res
                    continue
                cap_name_len = self.__buf[0]
                if cap_name_len == 0:
                    ## Return if no video capture name found
                    with self.__lock:
                        self.__resolv_msg[TYPE_LIST_CAP_RES] = {
                                'result': 'error',
                                'detail': 'Server Error: Video capture name length is 0'}
                    return
                elif len(self.__buf)-1 < cap_name_len: # for get name
                    res = self.__recv()
                    if res is None:
                        continue
                    elif res is Quit:
                        return
                    self.__buf += res
                    continue
                try:
                    cap_name = self.__buf[1:][:cap_name_len].decode('utf-8')
                except UnicodeDecodeError:
                    ## Return if video capture name is not UTF-8 encoding
                    with self.__lock:
                        self.__resolv_msg[TYPE_LIST_CAP_RES] = {
                                'result': 'error',
                                'detail': 'Protocol Error: Video capture name is not valid UTF-8 encoding'}
                    return
                self.__buf = self.__buf[1+cap_name_len:]
                break

            ## Read number of resolution
            res_num = 0
            while True:
                if len(self.__buf) == 0:
                    res = self.__recv()
                    if res is None:
                        continue
                    elif res is Quit:
                        return
                    self.__buf += res
                    continue
                res_num = self.__buf[0]
                self.__buf = self.__buf[1:]
                break

            ## Return if no resolution
            if res_num == 0:
                with self.__lock:
                    self.__resolv_msg[TYPE_LIST_CAP_RES] = {
                            'result': 'error',
                            'detail': 'Server Error: Video capture "%s" no resolution' %cap_name}
                return

            attr = []
            for j in range(res_num):
                ## Read resolution
                width, height = 0, 0
                while True:
                    if len(self.__buf) < 4: # for get width and height
                        res = self.__recv()
                        if res is None:
                            continue
                        elif res is Quit:
                            return
                        self.__buf += res
                        continue
                    width, height = struct.unpack('!HH', self.__buf[:4])
                    self.__buf = self.__buf[4:]
                    break

                ## Read number of frame rates
                fps_num = 0
                while True:
                    if len(self.__buf) == 0:
                        res = self.__recv()
                        if res is None:
                            continue
                        elif res is Quit:
                            return
                        self.__buf += res
                        continue
                    fps_num = self.__buf[0]
                    self.__buf = self.__buf[1:]
                    break

                ## Return if no frame rate
                if fps_num == 0:
                    with self.__lock:
                        self.__resolv_msg[TYPE_LIST_CAP_RES] = {
                                'result': 'error',
                                'detail': 'Server Error: Video capture "%s" no frame rate' %cap_name}
                    return

                fps = []
                for k in range(fps_num):
                    ## Read frame rate
                    rate = 0
                    while True:
                        if len(self.__buf) == 0: # for get frame rate
                            res = self.__recv()
                            if res is None:
                                continue
                            elif res is Quit:
                                return
                            self.__buf += res
                            continue
                        rate  = self.__buf[0]
                        self.__buf = self.__buf[1:]
                        break
                    fps.append(rate)

                attr.append(((width, height), fps))

            caps.append((cap_name, attr))

        ## Success get video captures information
        with self.__lock:
            self.__resolv_msg[TYPE_LIST_CAP_RES] = {'result': 'success', 'detail': copy(caps)}

    def __handle_status_code_response(self, res_type):
        ## Read status code
        status = 0xFF
        while True:
            if len(self.__buf) == 0: # for get status code
                res = self.__recv()
                if res is None:
                    continue
                elif res is Quit:
                    return
                self.__buf += res
                continue
            status = self.__buf[0]
            self.__buf = self.__buf[1:]
            break

        if status in STATUS_CODE:
            ## Read detail
            detail = ''
            while True:
                if len(self.__buf) == 0: # for get detail length
                    res = self.__recv()
                    if res is None:
                        continue
                    elif res is Quit:
                        return
                    self.__buf += res
                    continue
                detail_len = self.__buf[0]
                if len(self.__buf)-1 < detail_len: # for get detail
                    res = self.__recv()
                    if res is None:
                        continue
                    elif res is Quit:
                        return
                    self.__buf += res
                    continue
                try:
                    detail = self.__buf[1:][:detail_len].decode('utf-8')
                except UnicodeDecodeError:
                    ## Return if detail is not UTF-8 encoding
                    with self.__lock:
                        self.__resolv_msg[res_type] = {
                                'result': 'error',
                                'detail': 'Protocol Error: %s detail message is not valid UTF-8 encoding' %(
                                    STATUS_CODE[status].capitalize(),)}
                    return
                self.__buf = self.__buf[1+detail_len:]
                break

            ## Success get detail
            with self.__lock:
                self.__resolv_msg[res_type] = {'result': STATUS_CODE[status], 'detail': detail}
        else:
            ## Return failure if unknown status code occured
            with self.__lock:
                self.__resolv_msg[res_type] = {
                        'result': 'error',
                        'detail': 'Protocol Error: Invalid status code <{:02X}>'.format(status)}

    __RECV_HANDLE_SWITCH = {
        TYPE_GOODBYE: __goodbye,
        TYPE_ASK_ALIVE: __handle_ask_alive,
        #TYPE_REPLY_ALIVE: __handle_reply_alive,
        TYPE_LIST_UART_RES: __handle_list_uarts_response,
        TYPE_LIST_CAP_RES: __handle_list_captures_response,
        TYPE_RUN_MJPG_RES: partial(__handle_status_code_response, res_type=TYPE_RUN_MJPG_RES),
        TYPE_OPEN_UART_RES: partial(__handle_status_code_response, res_type=TYPE_OPEN_UART_RES),
        TYPE_SEND_KEY_RES: partial(__handle_status_code_response, res_type=TYPE_SEND_KEY_RES),
        TYPE_SEND_MOUSE_RES: partial(__handle_status_code_response, res_type=TYPE_SEND_MOUSE_RES),
        TYPE_SEND_ATX_RES: partial(__handle_status_code_response, res_type=TYPE_SEND_ATX_RES),}

    ## secure socket.send
    def __send(self, msg):
        sent, timer = 0, 0
        while True:
            sleep(0.01)
            if timer > TIMEOUT_RT:
                return {'result': 'error', 'detail': 'socket.send timeout'}
            try:
                sent = self.__sock.send(msg)
            except socket.error as e:
                if e.args[0] == errno.ECONNRESET:
                    # Disconnected from client sent by RST
                    self.__goodbye()
                    return {'result': 'error', 'detail': 'client got RST'}
                elif e.args[0] == errno.ECONNABORTED:
                    # Disconnected since server aborted
                    self.__goodbye()
                    return {'result': 'error', 'detail': 'connection aborted'}
                else:
                    raise e
            msg = msg[sent:]
            if len(msg) > 0:
                timer += 1
                continue
            return {'result': 'success'}

    def __hello(self):
        ## Init ikvm client socket
        AF_INET = socket.AF_INET6 if address_family(self.ip) == 'ipv6' else socket.AF_INET
        self.__sock = socket.socket(AF_INET, socket.SOCK_STREAM) # connection with iKVM's ip using ipv4/ipv6
        self.__sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1) # disable Nagle Delay
        self.__sock.setblocking(False)
        try:
            self.__sock.connect((self.ip, self.port))
        except socket.error as e:
            if e.args[0] != errno.EWOULDBLOCK: # skipped non-blocking error
                raise e

        ## Send handshake message to server
        timer = time()
        while True:
            sleep(0.01)
            if time()-timer > TIMEOUT_LAG:
                return {'result': 'error', 'detail': 'Send message timeout'}
            try:
                res = self.__send(HANDSHAKE_MSG)
            except socket.error as e:
                ## TCP connection is still not established, re-send handshake message
                if e.args[0] == errno.ENOTCONN:
                    continue
                ## Connection refused by server
                elif e.args[0] == errno.ECONNREFUSED:
                    return {'result': 'error', 'detail': 'Connection Refused'}
                raise e
            if res['result'] == 'error':
                return res
            break

        ## Wait until handshake message received from server
        buf, timer = b'', time()
        while True:
            sleep(0.01)
            if time()-timer > TIMEOUT_LAG:
                return {'result': 'error', 'detail': 'Received response timeout'}
            if buf == b'':
                res = self.__recv()
                if res is None:
                    continue
                elif res is Quit:
                    return {'result': 'error', 'detail': 'Connection Reset: Exist client connected'}
                buf += res
            loc = buf.find(MAGIC)
            if loc == -1:
                buf = b''
                continue
            head = buf[loc:][:4] # protocol magic and type
            if len(head) < 4 or head[-1] != TYPE_HANDSHAKE:
                continue
            return {'result': 'success'}

    def __list_uarts(self):
        res = self.__send(LIST_UART_REQ)
        if res['result'] == 'error':
            return res
        self.__resolv_msg[TYPE_LIST_UART_RES] = None
        timer = time()
        while self.__resolv_msg[TYPE_LIST_UART_RES] is None:
            sleep(0.01)
            if time()-timer > TIMEOUT_LAG:
                return {'result': 'error', 'detail': 'List serial devies timeout'}
        return self.__resolv_msg[TYPE_LIST_UART_RES]

    def __open_uart(self, port):
        res = self.__send(OPEN_UART_REQ(port))
        if res['result'] == 'error':
            return res
        self.__resolv_msg[TYPE_OPEN_UART_RES] = None
        timer = time()
        while self.__resolv_msg[TYPE_OPEN_UART_RES] is None:
            sleep(0.01)
            if time()-timer > TIMEOUT_LAG:
                return {'result': 'error', 'detail': 'Open serial devies "%s" timeout' %port}
        return self.__resolv_msg[TYPE_OPEN_UART_RES]

    def __list_captures(self):
        res = self.__send(LIST_CAP_REQ)
        if res['result'] == 'error':
            return res
        self.__resolv_msg[TYPE_LIST_CAP_RES] = None
        timer = time()
        while self.__resolv_msg[TYPE_LIST_CAP_RES] is None:
            sleep(0.01)
            if time()-timer > TIMEOUT_LAG:
                return {'result': 'error', 'detail': 'List video captures timeout'}
        return self.__resolv_msg[TYPE_LIST_CAP_RES]

    def __start_mjpg(self, device, resolution, fps, port):
        res = self.__send(RUN_MJPG_REQ(device, resolution, fps, port))
        if res['result'] == 'error':
            return res
        self.__resolv_msg[TYPE_RUN_MJPG_RES] = None
        timer = time()
        while self.__resolv_msg[TYPE_RUN_MJPG_RES] is None:
            sleep(0.01)
            if time()-timer > TIMEOUT_LAG:
                return {'result': 'error',
                        'detail': 'Start mjpg-streamer with video capture "%s" on port "%s" timeout' %(device, port,)}
        return self.__resolv_msg[TYPE_RUN_MJPG_RES]

    def __capture_select(self, device=None, resolution=None, fps=None):
        ## List available video captures
        res = self.__list_captures()
        if res['result'] == 'error':
            return res
        caps = res['detail']
        if not caps:
            return {'result': 'error', 'detail': 'No available video capture'}

        ## Determine what video capture for using
        cap_name = device if device else self.cap_name
        if cap_name:
            cap = list(filter(lambda cap: cap_name in cap[0], caps))
            if not cap:
                return {'result': 'error',
                        'detail': 'No available video capture "%s"' %cap_name}
            cap_no = caps.index(cap[0])
            self.cap_name = caps[cap_no][0]
        else:
            self.cap_name = cap_name = caps[0][0]
            cap_no = 0

        ## Determine what resolution for using
        all_resolution = list(map(lambda attr: attr[0], caps[cap_no][1]))
        fun = max if self.cap_quality == 'best' else min
        if resolution is None:
            # find resolution that the scale is satisfied with cap_scale
            target = list(filter(lambda res: res_scale(*res)==self.cap_scale, all_resolution))
            target = target if target else all_resolution
            area = tuple(map(lambda res: res[0]*res[1], target))
            i = area.index(fun(area)) # find index satisfy policy
            resolution = target[i]

        ## Determine what frame rate for using
        if fps is None:
            # find the fps satisfied with cap_quality
            i = all_resolution.index(resolution) if resolution in all_resolution else 0 # find index satisfy policy
            fps = fun(caps[cap_no][1][i][1])

        ## Start ikvm mjpg-streamer
        return self.__start_mjpg(cap_name, resolution, fps, self.mjpg_port)

    def list_serial_devices(self):
        if not self.__run:
            return {'result': 'error', 'detail': 'Kvm instance not started'}

        return self.__list_uarts()

    def __uart_select(self, port=None):
        uart_port = port if port else self.uart_port
        ## List available serial devices if port is not specified
        if not uart_port:
            res = self.__list_uarts()
            if res['result'] == 'error':
                return res
            uarts = res['detail']
            if not uarts:
                return {'result': 'error', 'detail': 'No serial device on iKVM'}
            if self.usbid:
                target = list(filter(lambda usb: self.usbid==(usb[1], usb[2]), uarts))
                uart_port = target[0][0] if target else None
            else:
                uart_port = uarts[0][0]
            if uart_port is None:
                return {'result': 'error',
                        'detail': 'No such serial device with USB-ID "{:04X}:{:04X}" on iKVM'.format(*self.usbid)}
            self.uart_port = uart_port

        ## Open ikvm serial device with port
        return self.__open_uart(uart_port)

    def open_serial_device(self, port=None):
        """ Open serial device according to self.uart_port or self.usbid if port is None
        """
        if not self.__run:
            return {'result': 'error', 'detail': 'Kvm instance not started'}
        return self.__uart_select(port)

    def list_captures(self):
        if not self.__run:
            return {'result': 'error', 'detail': 'Kvm instance not started'}

        return self.__list_captures()

    def alt_capture(self, device=None, resolution=None, fps=None):
        """ Choose capture with name self.cap_name or first found capture if device is None
            Choose resolution according to self.cap_scale and self.cap_quality if resolution is None
                     e.g. (1920, 1080) or '1920x1080'
            Choose frame rate according to self.cap_scale and self.cap_quality if fps is None
        """
        ## Accept valid arguments
        assert isinstance(device, (str, type(None)))
        if isinstance(resolution, tuple):
            assert len(resolution) == 2
            assert all([x in range(1, 0x10000) for x in resolution])
        elif isinstance(resolution, str):
            if re.match(r'^\d+x\d+$', resolution):
                resolution = tuple(map(int, resolution.split('x')))
                assert all([x in range(1, 0x10000) for x in resolution])
            else:
                raise TypeError("resolution string should be like '1920x1080'")
        elif resolution is not None:
            raise TypeError('resolution not valid')
        if isinstance(fps, int):
            if fps not in range(1, 0x100):
                raise TypeError('fps value should between 0 and 255')
        elif fps is not None:
            raise TypeError('fps not valid')

        if not self.__run:
            return {'result': 'error', 'detail': 'Kvm instance not started'}

        return self.__capture_select(device, resolution, fps)

    def send_key(self, act, key): # send a single key with press or release
        if not self.__run:
            return {'result': 'error', 'detail': 'Kvm instance not started'}

        ## Arguments Validity Check
        if act in ('press', 'release'):
            act = KEY_PRESS if act == 'press' else KEY_RELEASE
        elif act not in (KEY_PRESS, KEY_RELEASE):
            raise TypeError('Argument act should be "press", "release", %d or %d' %(KEY_PRESS, KEY_RELEASE))
        assert key in range(ARDUINO_MAX_KEY+1)

        return self.__send(SEND_KEY_REQ_K(act, key))

    def send_text(self, text): # send text as keyboard input
        if not self.__run:
            return {'result': 'error', 'detail': 'Kvm instance not started'}

        ## Arguments Validity Check
        #assert isinstance(text, str)
        assert all([ord(char) in range(0x80) for char in text]) # ASCII only
        #assert len(text) < 0x10000

        return self.__send(SEND_KEY_REQ_C(text))

    def release_keys(self): # send release all keys command to iKVM
        if not self.__run:
            return {'result': 'error', 'detail': 'Kvm instance not started'}

        return self.__send(SEND_KEY_REQ_R)

    def click_mouse(self, act, button):
        if not self.__run:
            return {'result': 'error', 'detail': 'Kvm instance not started'}

        ## Arguments Validity Check
        if act in ('press', 'release'):
            act = MOUSE_PRESS if act == 'press' else MOUSE_RELEASE
        elif act not in (MOUSE_PRESS, MOUSE_RELEASE):
            raise TypeError('Argument act should be "press", "release", %d or %d' %(MOUSE_PRESS, MOUSE_RELEASE))
        assert button in ARDUINO_MOUSE_BUTTONS

        return self.__send(SEND_MOUSE_REQ_K(act, button))

    def move_mouse(self, x, y):
        if not self.__run:
            return {'result': 'error', 'detail': 'Kvm instance not started'}

        return self.__send(SEND_MOUSE_REQ_M(x, y))

    def scroll_mouse_wheel_up(self):
        if not self.__run:
            return {'result': 'error', 'detail': 'Kvm instance not started'}

        return self.__send(SEND_MOUSE_REQ_S(MOUSE_WHEEL_UP))

    def scroll_mouse_wheel_down(self):
        if not self.__run:
            return {'result': 'error', 'detail': 'Kvm instance not started'}

        return self.__send(SEND_MOUSE_REQ_S(MOUSE_WHEEL_DOWN))

    def release_mouse_buttons(self):
        if not self.__run:
            return {'result': 'error', 'detail': 'Kvm instance not started'}

        return self.__send(SEND_MOUSE_REQ_S(MOUSE_CLEAR))

    def send_atx(self, sig):
        if not self.__run:
            return {'result': 'error', 'detail': 'Kvm instance not started'}

        ## Arguments Validity Check
        if sig in ATX_SIGNAL:
            sig = ATX_SIGNAL[sig]
        elif sig not in ATX_SIGNAL.values():
            raise TypeError('Argument sig should be "short power", "reset", "long power", 0xFD, 0xFE or 0xFF')

        return self.__send(SEND_ATX_REQ(sig))

    def read_last_send_key_result(self):
        if not self.__run:
            return {'result': 'error', 'detail': 'Kvm instance not started'}

        with self.__lock:
            res = self.__resolv_msg[TYPE_SEND_KEY_RES]
            self.__resolv_msg[TYPE_SEND_KEY_RES] = None
        return res

    def read_last_send_mouse_result(self):
        if not self.__run:
            return {'result': 'error', 'detail': 'Kvm instance not started'}

        with self.__lock:
            res = self.__resolv_msg[TYPE_SEND_MOUSE_RES]
            self.__resolv_msg[TYPE_SEND_MOUSE_RES] = None
        return res

    def read_last_send_atx_result(self):
        if not self.__run:
            return {'result': 'error', 'detail': 'Kvm instance not started'}

        with self.__lock:
            res = self.__resolv_msg[TYPE_SEND_ATX_RES]
            self.__resolv_msg[TYPE_SEND_ATX_RES] = None
        return res

    def is_run(self):
        return self.__run
