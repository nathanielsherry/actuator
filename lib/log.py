#!/usr/bin/python3

LEVEL_ERROR = 100
LEVEL_WARN = 300
LEVEL_INFO = 500
LEVEL_DEBUG = 700
LEVEL_TRACE = 900

LEVEL_NAMES = {
    'error': LEVEL_ERROR,
    'warn': LEVEL_WARN,
    'info': LEVEL_INFO,
    'debug': LEVEL_DEBUG,
    'trace': LEVEL_TRACE,
}

__level = LEVEL_WARN
def set_level(l):
    global __level
    if isinstance(l, str):
        __level = LEVEL_NAMES[l]
    else:
        __level = l

def error(msg):
    if __level < LEVEL_ERROR: return
    print(msg, flush=True)

def warn(msg):
    if __level < LEVEL_WARN: return
    print(msg, flush=True)

def info(msg):
    if __level < LEVEL_INFO: return
    print(msg, flush=True)
    
def debug(msg):
    if __level < LEVEL_DEBUG: return
    print(msg, flush=True)
