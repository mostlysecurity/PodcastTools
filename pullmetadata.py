#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import time
import traceback
import json
import mutagen
from mutagen import id3

try:
    from argparse import ArgumentParser as ArgParser
except ImportError:
    from optparse import OptionParser as ArgParser

#Global variables.  Don't judge me.
debug = False
inputfile = None
output = "HTML"
showtime = False

__version__ = '1.0.0'

def extractText(d):
    if len(d.text) > 1:
        return d.text
    else:
        return d.text[0]

def isText(d):
    texttypes = [id3.TALB, id3.TPE1, id3.TPE2, id3.TPE3, id3.TIT1, id3.TIT2, id3.TIT3, id3.TENC, id3.TLEN, id3.COMM, id3.USLT]
    is_text = False
    for t in texttypes:
        if isinstance(d, t):
            is_text = True
            break
    return is_text

def extractTimestamp(d):
    return d.text[0].get_text()

def isTimestamp(d):
    tstypes = [id3.TDRC, id3.TYER]
    is_ts = False
    for t in tstypes:
        if isinstance(d, t):
            is_ts = True
            break
    return is_ts

def extractURL(wxxx):
    return wxxx.url

def extractChapterTOC(ctoc):
    return ctoc.child_element_ids

def appendChapterData(chap, chapdata):
    ch = dict()
    ch['start_time'] = chap.start_time
    ch['end_time'] = chap.end_time
    ch['start_offset'] = chap.start_offset
    ch['end_offset'] = chap.end_offset

    for frame in chap.sub_frames:
        if frame == 'TIT2':
            ch['text'] = extractText(chap.sub_frames['TIT2'])
        elif frame == 'WXXX:chapter url':
            ch['url'] = extractURL(chap.sub_frames['WXXX:chapter url'])
        else:
            ch[frame] = "unknown type: {}".format(type(chap.sub_frames[frame]).__name__)

    chapdata[chap.element_id] = ch
    return chapdata

def printd(txt):
    if debug:
        print(txt)

def extractMetadata():
    printd("Inputfile: {}".format(inputfile))
    mp3 = mutagen.File(inputfile)
    metadata = dict()
    metadata['CHAP'] = dict()
    for key in mp3.keys():
        data = mp3.tags.getall(key)
        for d in data:
            if isText(d):
                metadata[type(d).__name__] = extractText(d)
            elif isTimestamp(d):
                metadata[type(d).__name__] = extractTimestamp(d)
            elif isinstance(d, id3.CTOC):
                metadata['CTOC'] = extractChapterTOC(d)
            elif isinstance(d, id3.CHAP):
                metadata['CHAP'] = appendChapterData(d, metadata['CHAP'])
            elif isinstance(d, id3.APIC):
                metadata['APIC'] = "Has Image Data"
            else:
                metadata[type(d).__name__] = "Unknown type, fixme"
    return metadata

def getStartTime(starttime):
    # convert starttime millis into minutes:seconds
    millis = int(starttime)
    seconds=(millis/1000)%60
    seconds = int(seconds)
    minutes=(millis/(1000*60))%60
    minutes = int(minutes)
    hours=(millis/(1000*60*60))%24
    hours = int(hours)
    if hours > 0:
        return "%d:%02d:%02d" % (hours, minutes, seconds)
    else:
        return "%d:%02d" % (minutes, seconds)
    return ""

def createMarkdown(metadata):
    print("")
    print(metadata['USLT'])
    print("")
    for cch in metadata['CTOC']:
        ch = metadata['CHAP'][cch]
        if ch.get('url'):
            print("[{}]({})".format(ch.get('text'), ch.get('url')))
        else:
            print("{}".format(ch.get('text')))
    print("")

def createHTML(metadata):
    print('')
    print('<p>{}</p>'.format(metadata['USLT']))
    print('<ul>')
    for cch in metadata['CTOC']:
        ch = metadata['CHAP'][cch]
        st = ""
        std = ""
        if ch.get('start_time') and showtime:
            st = getStartTime(ch.get('start_time'))
            std = " - "
        if ch.get('url'):
            print('<li>{}{}<a href="{}" target="_blank">{}</a></li>'.format(st, std, ch.get('url'), ch.get('text')))
        else:
            print('<li>{}{}{}</li>'.format(st, std, ch.get('text')))
    print('</ul>')


def version():
    print("Version: {}".format(__version__))


def parseCommandLine():
    global debug, inputfile, output, showtime
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
    parser.add_argument('-s', '--showtime', action='store_true', help='Display the start time of each segment')
    parser.add_argument('-o', '--output', help="Specify format of output: MD, JSON, HTML", default=output)
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

    if args.showtime:
        showtime = args.showtime

    if args.inputfile:
        inputfile = args.inputfile
    
    if args.output:
        output = args.output
        output = output.upper()

    if inputfile == None or inputfile == '':
        print("inputfile cannot be empty")
        raise SystemExit()

    metadata = extractMetadata()

    if output == 'JSON':
        print(json.dumps(metadata, indent=2))
    elif output == 'MD':
        createMarkdown(metadata)
    elif output == 'HTML':
        createHTML(metadata)
    else:
        print("Unknown output type: {}".format(output))

        

def main():
    try:
        parseCommandLine()
    except KeyboardInterrupt:
        print("\nCancelling...\n")


if __name__ == '__main__':
    main()


