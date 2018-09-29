#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import time
import traceback
import json
import mutagen

try:
    from argparse import ArgumentParser as ArgParser
except ImportError:
    from optparse import OptionParser as ArgParser

#Global variables.  Don't judge me.
debug = False
inputfile = None

__version__ = '1.0.0'


def extractMetadata():
    print("Inputfile: {}".format(inputfile))
    mp3 = mutagen.File(inputfile)
#    print(mp3.pprint())
    print(mp3.keys())

    for key in mp3.keys():
        print(mp3.tags.getall(key))
        print("-------")



def version():
    print("Version: {}".format(__version__))


def parseCommandLine():
    global debug, inputfile
    description = (
            'Script to pull the metadata out of a Podcast '
            'and format it.\n'
            '---------------------------------------------'
            '-----------------------------\n'
            )
    parser = ArgParser(description=description)
    # If we're using optparse.OptionParser, creat 'add_argument' method
    # for argparse.ArgumentParser compatibility
    try:
        parser.add_argument = parser.add_option
    except AttributeError:
        pass
    parser.add_argument('-v', '--version', action='store_true', help='Show version numbers and exit')
    parser.add_argument('-i', '--inputfile', help='Specify the podcast file to extract')
    parser.add_argument('-d', '--debug', action='store_true', help='Prints extra stuff to stdout')
    
    options = parser.parse_args()
    if isinstance(options, tuple):
        args = options[0]
    else:
        args = options
    del options

    if args.version:
        version()
    
    if args.debug:
        debug = args.debug

    if args.inputfile:
        inputfile = args.inputfile

    if inputfile == None or inputfile == '':
        print("inputfile cannot be empty")
        raise SystemExit()

    extractMetadata()
        

def main():
    try:
        parseCommandLine()
    except KeyboardInterrupt:
        print("\nCancelling...\n")


if __name__ == '__main__':
    main()


