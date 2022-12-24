# coding: utf-8

from urllib.request import urlopen
from socket import timeout as socket_timeout
import urllib.error

TIMEOUT = 0.4 # second(s), used in open()
MAX_READABLE = 1048576 # Read data 1MiB timeout

class MjpgClient:
    def __init__(self):
        self.__streamer = None

    def open(self, url, timeout=TIMEOUT):
        self.url = url
        try:
            if self.__streamer and not self.__streamer.closed:
                self.__streamer.close()
            self.__streamer = urlopen(url, timeout=timeout)
        except urllib.error.HTTPError as e:
            return {'result': 'error', 'detail': 'HTTPError: {} {}'.format(e.code, e.reason)}
        except urllib.error.URLError as e:
            return {'result': 'error', 'detail': 'URLError: {}'.format(e.reason)}
        except TimeoutError:
            return {'result': 'error', 'detail': 'TimeoutError'}
        else:
            return {'result': 'success'}

    def close(self):
        if self.__streamer and not self.__streamer.closed:
            self.__streamer.close()

    def __check_boundarydonotcross(self):
        counter = 0
        reg = b''
        while True:
            res = self.__streamer.read(1)
            if res == b'':
                return
            elif counter > MAX_READABLE:
                raise TimeoutError('MjpgClient __check_boundarydonotcross Timeout')
            elif res == b'-' and reg == b'':
                reg += res
            elif res == b'-' and reg == b'-':
                reg += res
            elif res == b'b' and reg == b'--':
                reg += res + self.__streamer.read(17)
            elif res == b'\r' and reg == b'--boundarydonotcross':
                return
            else:
                reg = b''
                counter += 1

    def __read_content_type(self):
        counter = 0
        reg = b''
        content_type = b''
        while True:
            res = self.__streamer.read(1)
            if res == b'':
                return res
            elif counter > MAX_READABLE:
                raise TimeoutError('MjpgClient __read_content_type Timeout')
            elif res == b'C' and reg == b'':
                reg += res
            elif res == b'o' and reg == b'C':
                reg += res
            elif res == b'n' and reg == b'Co':
                reg += res + self.__streamer.read(11)
            elif res == b'\r' and reg == b'Content-Type: ':
                try:
                    return content_type.decode('utf-8')
                except UnicodeDecodeError:
                    return None
            elif reg == b'Content-Type: ':
                content_type += res
            else:
                reg = b''
                counter += 1

    def __read_content_length(self):
        counter = 0
        reg = b''
        content_length = b''
        while True:
            res = self.__streamer.read(1)
            if res == b'':
                return res
            elif counter > MAX_READABLE:
                raise TimeoutError('MjpgClient __read_content_length Timeout')
            elif res == b'C' and reg == b'':
                reg += res
            elif res == b'o' and reg == b'C':
                reg += res
            elif res == b'n' and reg == b'Co':
                reg += res + self.__streamer.read(13)
            elif res == b'\r' and reg == b'Content-Length: ':
                try:
                    return int(content_length)
                except ValueError:
                    return None
            elif reg == b'Content-Length: ':
                content_length += res
            else:
                reg = b''
                counter += 1

    def __skip_header(self):
        counter = 0
        reg = b''
        while True:
            res = self.__streamer.read(1)
            if res == b'':
                return res
            elif counter > MAX_READABLE:
                raise TimeoutError('MjpgClient __skip_header Timeout.')
            elif res == b'\r' and reg == b'':
                reg += res
            elif res == b'\n' and reg == b'\r':
                reg += res
            elif res == b'\r' and reg == b'\r\n':
                reg += res
            elif res == b'\n' and reg == b'\r\n\r':
                return
            else:
                reg = b''
                counter += 1

    def next_frame(self):
        if self.__streamer is None or self.__streamer.closed:
            return {'result': 'error', 'detail': 'URL not opened'}
        ## Skip to HTTP Header
        try:
            self.__check_boundarydonotcross()
            ## Read Content-Type
            cnt_type = self.__read_content_type()
            if cnt_type == b'':
                return {'result': 'lost'}
            elif cnt_type != 'image/jpeg':
                return {'result': 'error', 'detail': 'Protocol Error: Content-Type is not image/jpeg'}
            ## Read Content-Length
            cnt_len = self.__read_content_length()
            if cnt_len is None:
                return {'result': 'error', 'detail': 'Protocol Error: Content-Length invalid'}
            elif cnt_len == b'':
                return {'result': 'lost'}
            ## Skip to HTTP Body
            self.__skip_header()
            ## Get Jpeg Body
            body = self.__streamer.read(cnt_len)
        except socket_timeout:
            raise TimeoutError('MjpgClient Read Timeout.')
        else:
            if body == b'':
                return {'result': 'lost'}
            elif body[:2] != b'\xff\xd8' or body[-2:] != b'\xff\xd9':
                return {'result': 'error', 'detail': 'Format Error: Received non-Jpeg file'}
            else:
                return {'result': 'success', 'detail': body}
