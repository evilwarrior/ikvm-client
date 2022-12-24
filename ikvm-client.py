#!/usr/bin/env python3
# coding: utf-8

import sys

if __name__ != '__main__':
    sys.exit(1)

import ikvm, argparse, os, yaml, re

domain_re = r'^(((?!\-))(xn\-\-)?[a-z0-9\-_]{0,61}[a-z0-9]{1,1}\.)*(xn\-\-)?([a-z0-9\-]{1,61}|[a-z0-9\-]{1,30})\.[a-z]{2,}$'

def is_domain(host):
    return (re.match(domain_re, host) is not None)

def _host(host):
    if is_domain(host):
        return host
    ip = host
    ikvm.address_family(ip)
    return ip

def _port(port):
    if port in (None, 'None'):
        return None
    if int(port) not in range(1, 0x10000):
        raise argparse.ArgumentTypeError('Port value out of range')
    return int(port)

def _str(string):
    if string in (None, 'None'):
        return None
    return str(string)

def _scale(scale):
    if scale in (None, 'None'):
        return None
    w, h = tuple((int(x) for x in scale.split(':')))
    return (w, h)

def _quality(quality):
    if quality in (None, 'None'):
        return None
    quality = quality.lower()
    if quality not in ('best', 'worst'):
        raise argparse.ArgumentTypeError('Video capture device quality should be best or worst')
    return quality

def _usbid(usbid):
    if usbid in (None, 'None'):
        return None
    vid, pid = tuple((int(x, base=16) for x in usbid.split(':')))
    return usbid

def _resolution(reso):
    if reso in (None, 'None'):
        return None
    w, h = tuple((int(x) for x in reso.split('x')))
    return (w, h)

def _logfile(logfile):
    if logfile in (None, 'None'):
        return None
    folder = os.path.dirname(logfile) if os.path.dirname(logfile) else './'
    if not os.path.isdir(folder):
        raise argparse.ArgumentTypeError('Path "{}" does not exist'.format(folder))
    if os.path.isdir(logfile):
        raise argparse.ArgumentTypeError('Log file "{}" should not be a folder'.format(logfile))
    return logfile

def _log_level(log_level):
    if log_level in (None, 'None'):
        return None
    if int(log_level) not in range(6):
        raise argparse.ArgumentTypeError('Log level should be between 0 and 5')
    return int(log_level)

def _config(config):
    if not os.path.exists(config) or os.path.isdir(config):
        raise argparse.ArgumentTypeError('No such config file "{}"'.format(config))
    with open(config, 'r') as f:
        yaml_text = f.read()
    try:
        yaml_dict = yaml.safe_load(yaml_text)
    except yaml.scanner.ScannerError:
        raise argparse.ArgumentTypeError('The file is not valid as a YAML file'.format(config))
    if not isinstance(yaml_dict, dict):
        raise argparse.ArgumentTypeError('The file is not valid as a YAML file'.format(config))
    if not yaml_dict.get('ikvm-server') or not yaml_dict['ikvm-server'].get('host'):
        raise argparse.ArgumentTypeError('The YAML file contains no host option'.format(config))
    return yaml_dict

parser = argparse.ArgumentParser()
# ikvm settings
parser.add_argument('host', type=_host, help='iKVM server ip/domain address')
parser.add_argument('-6', '--ipv6', action='store_true', help='resolve domain as IPv6 first')
parser.add_argument('-4', '--ipv4', action='store_true', help='resolve domain as IPv4 first')
parser.add_argument('port', type=_port, nargs='?', help='iKVM server port, default 7130')
parser.add_argument('-i', '--config', type=_config, help='a YAML file as config file, if other arguments are specific, ignored the specific arguments')
parser.add_argument('-m', '--mjpg-port', type=_port, help='client will open mjpg-streamer service with this port, default 8080')
parser.add_argument('-v', '--capture-device', type=_str, help='MJPG-Streamer will start specific video capture device initially')
parser.add_argument('--capture-scale', type=_scale, help='MJPG-Streamer will start video capture device using specific resolution scale first, e.g. 16:9')
parser.add_argument('--capture-quality', type=_quality, help='MJPG-Streamer will start video capture device as best or worst quality, default best')
parser.add_argument('-u', '--serial-port', type=_str, help='server will start serial device with specific port initially')
parser.add_argument('--serial-usbid', type=_usbid, help='server will start serial device with specific vid:pid, ignored as --serial-port option is specific; value should be taken as 4 bytes hex separated by colon, e.g. 0483:df11')

# ikvm client ui settings
parser.add_argument('-F', '--fullscreen', action='store_true', help='start client as fullscreen initially')
parser.add_argument('--resolution', type=_resolution, help='client window resolution, e.g. 1920x1080, default adaptive the screen')
parser.add_argument('--logfile', type=_logfile, help='iKVM client saved log file path, default SYSOUT and SYSERR')
parser.add_argument('--log-level', type=_log_level, help='log level used, default 3')

if len(sys.argv) == 1:
    # use yaml file
    yaml_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.yaml') # resolve symlink
    args = parser.parse_args(['::', '-i', yaml_path])
elif len(sys.argv) == 3 and sys.argv[1] in ('-i', '--config'):
    # only config option, ignore host option
    args = parser.parse_args(['::', '-i', sys.argv[2]])
else:
    args = parser.parse_args()

# set input arguments
ip = args.host
is_ipv6 = args.ipv6
is_ipv4 = args.ipv4
port = args.port
config = args.config
mjpg_port = args.mjpg_port
cap = args.capture_device
scale = args.capture_scale
quality = args.capture_quality
uart = args.serial_port
usbid = args.serial_usbid
fullscreen = args.fullscreen
resolution = args.resolution
logfile = args.logfile
log_level = args.log_level

if config: # config file specific, use it
    ikvm_server = config.get('ikvm-server')
    mjpg_streamer = config.get('mjpg-streamer')
    serial_device = config.get('serial-device')
    window_option = config.get('window-option')
    log_option = config.get('log-option')
    # set input arguments
    args = []
    args.append(ikvm_server.get('host') if ip == '::' else ip)
    # add options in configure file into argparse for error check as the option is not specific
    args.append(str(ikvm_server.get('port'))) if not port else None
    args.append('-6') if ikvm_server.get('ipv6') == True else None # ipv6 defined as true/false
    args.append('-4') if ikvm_server.get('ipv4') == True else None # ipv4 defined as true/false
    if mjpg_streamer:
        args.extend(['-m', str(mjpg_streamer.get('port'))]) if not mjpg_port else None
        args.extend(['-v', str(mjpg_streamer.get('capture-device'))]) if not cap else None
        args.extend(['--capture-scale', str(mjpg_streamer.get('capture-scale'))]) if not scale else None
        args.extend(['--capture-quality', str(mjpg_streamer.get('capture-quality'))]) if not quality else None
    if serial_device:
        args.extend(['-u', str(serial_device.get('port'))]) if not uart else None
        args.extend(['--serial-usbid', str(serial_device.get('usbid'))]) if not usbid else None
    if window_option:
        args.append('-F') if window_option.get('fullscreen') == True else None # fullscreen defined as true/false
        args.extend(['--resolution', str(window_option.get('resolution'))]) if not resolution else None
    if log_option:
        args.extend(['--logfile', str(log_option.get('path'))]) if not logfile else None
        args.extend(['--log-level', str(log_option.get('level'))]) if not log_level else None
    args = parser.parse_args(args)

# remap values, not use argument of add_argument "default" since configure file options used in argparse again
ip = args.host
is_ipv6 = True if is_ipv6 else args.ipv6
is_ipv4 = True if is_ipv4 else args.ipv4
# first use explict specific argument, second use configure file value, finnaly use default
port = port if port else (args.port if args.port else 7130)
mjpg_port = mjpg_port if mjpg_port else (args.mjpg_port if args.mjpg_port else 8080)
cap = cap if cap else args.capture_device
scale = scale if scale else args.capture_scale
quality = quality if quality else (args.capture_quality if args.capture_quality else 'best')
uart = uart if uart else args.serial_port
usbid = usbid if usbid else args.serial_usbid
fullscreen = True if fullscreen else args.fullscreen
resolution = resolution if resolution else (args.resolution if args.resolution else (0, 0))
logfile = logfile if logfile else args.logfile
log_level = log_level if log_level else (args.log_level if args.log_level else 3)

import socket
if is_domain(ip):
    try:
        quints = socket.getaddrinfo(ip, None)
    except socket.error:
        parser.print_usage()
        print(f'ikvm-client.py: error: argument host: Domain "{ip}" cannot be resolved')
        sys.exit(1)
    if is_ipv6:
        quints = list(filter(lambda x: x[0] == socket.AF_INET6, quints))
        if not quints:
            parser.print_usage()
            print(f'ikvm-client.py: error: argument host: Domain "{ip}" has no IPv6 address')
            sys.exit(1)
    elif is_ipv4:
        quints = list(filter(lambda x: x[0] == socket.AF_INET, quints))
        if not quints:
            parser.print_usage()
            print(f'ikvm-client.py: error: argument host: Domain "{ip}" has no IPv4 address')
            sys.exit(1)
    ip = quints[0][4][0]

from ikvm_ui import *
kvm = ikvm.Kvm(ip, port, mjpg_port, cap_name=cap, cap_scale=scale, cap_quality=quality, uart_port=uart, usbid=usbid)
mjpg = ikvm.MjpgClient()
window = iKvmClient(kvm, mjpg, fullscreen=fullscreen, cap_res_in_win=resolution, logfile=logfile, log_level=log_level)
window.start()
sys.exit(0)
