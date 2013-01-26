"""
Module debug: various debugging utilities.  Set DEBUG=False to disable them.

trap(message, breakOn) -- used to set code coverage breakpoints in the code.
bugprint(message) -- same as print, but only works in DEBUG mode.
printrap(message, breakOn) -- print a message (always), then call trap.
bugprintrap(message, breakOn) -- print a message and call trap (in DEBUG mode).

Created on Dec 4, 2011

@author: malcolmm

No copyright claimed - do anything you want with this code.
"""

from __future__ import print_function
import time

#To turn off these utilities set this to False
DEBUG = True

def startTime():
    return time.clock()

def timeElapsed(since):
    return time.clock() - since

class Trap(UserWarning):
    pass

def trap(message="IT'S A TRAP!", breakOn=True):
    '''Break into the debugger if breakOn evaluates to True. 
    
    Raise (and catch) an instance of the Trap exception.
    With optional error message, pass that message into Trap's constructor.
    With optional breakOn, raise the exception only if breakOn evaluates to True.
    
    **Be sure that your IDE is set to break on caught (Trap or UserWarning) 
    exceptions.**
    
    '''
    if DEBUG and breakOn: 
        try:
            raise Trap(message)
        except Trap:
            pass

def bugprint(*args, **kwargs):
    '''Same as built-in print, but only works in DEBUG mode.'''
    if DEBUG:
        print(*args, **kwargs)
        
def printrap(message, breakOn=True):
    '''Print a message to the console (always), and call trap in DEBUG mode.
    
    If DEBUG is set to True, call trap with message and the optional breakOn 
    argument.
    '''
    print(message)
    if DEBUG:
        trap(message, breakOn)
    
def bugprintrap(message, breakOn=True):
    '''Print a message to the console and call trap (in DEBUG mode only).
    
    If DEBUG is set to True, print message and call trap with that message 
    and the optional breakOn argument.
    '''
    if DEBUG:
        print(message)
        trap(message, breakOn)
    
