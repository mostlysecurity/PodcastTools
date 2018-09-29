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

def extractText(data_text):
    text = ''
    for t in data_text:
        text+=t

    return text

def extractMetadata():
    print("Inputfile: {}".format(inputfile))
    mp3 = mutagen.File(inputfile)
#    print(mp3.pprint())
    print(mp3.keys())

    for key in mp3.keys():
        data = mp3.tags.getall(key)
        for d in data:
            if isinstance(d, mutagen.id3.TALB):
                print("TALB: {}".format(extractText(d.text)))
            elif isinstance(d, mutagen.id3.TPE1):
                print("TPE1: {}".format(extractText(d.text)))
            elif isinstance(d, mutagen.id3.TPE2):
                print("TPE2: {}".format(extractText(d.text)))
            elif isinstance(d, mutagen.id3.TPE3):
                print("TPE3: {}".format(extractText(d.text)))
            elif isinstance(d, mutagen.id3.TPE4):
                print("TPE4: {}".format(extractText(d.text)))
            elif isinstance(d, mutagen.id3.TIT1):
                print("TIT1: {}".format(extractText(d.text)))
            elif isinstance(d, mutagen.id3.TIT2):
                print("TIT2: {}".format(extractText(d.text)))
            elif isinstance(d, mutagen.id3.TIT3):
                print("TIT3: {}".format(extractText(d.text)))
            elif isinstance(d, mutagen.id3.COMM):
                print("COMM: {}".format(extractText(d.text)))
            elif isinstance(d, mutagen.id3.USLT):
                print("USLT: {}".format(extractText(d.text)))
            elif isinstance(d, mutagen.id3.APIC):
                print("APIC: Image data")
            else:
                print(type(d))
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


