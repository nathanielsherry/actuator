#!/usr/bin/python3

LEVEL_ERROR = 100
LEVEL_WARN = 300
LEVEL_INFO = 500
LEVEL_DEBUG = 700
LEVEL_TRACE = 900


level = LEVEL_INFO

def error(msg):
    if level < LEVEL_ERROR: return
    print(msg, flush=True)

def warn(msg):
    if level < LEVEL_WARN: return
    print(msg, flush=True)

def info(msg):
    if level < LEVEL_INFO: return
    print(msg, flush=True)
    
def debug(msg):
    if level < LEVEL_INFO: return
    print(msg, flush=True)
