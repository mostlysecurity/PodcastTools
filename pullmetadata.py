#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import time
import traceback
import json
import mutagen
from mutagen import id3
from argparse import ArgumentParser as ArgParser


class PodcastMetadata:
    def __init__(self, inputfile):
        self.inputfile = inputfile

    def extractText(self, d):
        if len(d.text) > 1:
            return d.text
        else:
            return d.text[0]

    def isText(self, d):
        texttypes = [id3.TALB, id3.TPE1, id3.TPE2, id3.TPE3, id3.TIT1, id3.TIT2, id3.TIT3, id3.TENC, id3.TLEN, id3.COMM, id3.USLT]
        is_text = False
        for t in texttypes:
            if isinstance(d, t):
                is_text = True
                break
        return is_text

    def extractTimestamp(self, d):
        return d.text[0].get_text()

    def isTimestamp(self, d):
        tstypes = [id3.TDRC, id3.TYER]
        is_ts = False
        for t in tstypes:
            if isinstance(d, t):
                is_ts = True
                break
        return is_ts

    def extractURL(self, wxxx):
        return wxxx.url

    def extractChapterTOC(self, ctoc):
        return ctoc.child_element_ids

    def appendChapterData(self, chap, chapdata):
        ch = dict()
        ch['start_time'] = chap.start_time
        ch['end_time'] = chap.end_time
        ch['start_offset'] = chap.start_offset
        ch['end_offset'] = chap.end_offset

        for frame in chap.sub_frames:
            if frame == 'TIT2':
                ch['text'] = self.extractText(chap.sub_frames['TIT2'])
            elif frame == 'WXXX:chapter url':
                ch['url'] = self.extractURL(chap.sub_frames['WXXX:chapter url'])
            else:
                ch[frame] = "unknown type: {}".format(type(chap.sub_frames[frame]).__name__)

        chapdata[chap.element_id] = ch
        return chapdata

    def extractMetadata(self):
        mp3 = mutagen.File(self.inputfile)
        metadata = dict()
        metadata['CHAP'] = dict()
        for key in mp3.keys():
            data = mp3.tags.getall(key)
            for d in data:
                if self.isText(d):
                    metadata[type(d).__name__] = self.extractText(d)
                elif self.isTimestamp(d):
                    metadata[type(d).__name__] = self.extractTimestamp(d)
                elif isinstance(d, id3.CTOC):
                    metadata['CTOC'] = self.extractChapterTOC(d)
                elif isinstance(d, id3.CHAP):
                    metadata['CHAP'] = self.appendChapterData(d, metadata['CHAP'])
                elif isinstance(d, id3.APIC):
                    metadata['APIC'] = "Has Image Data"
                else:
                    metadata[type(d).__name__] = "Unknown type, fixme"
        return metadata


debug = False
output = "HTML"
showtime = False

__version__ = '1.0.0'

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
        st = ""
        std = ""
        if showtime:
            st = getStartTime(ch.get('start_time'))
            std = " - "
        if ch.get('url'):
            print("{}{}[{}]({})".format(st,std,ch.get('text'), ch.get('url')))
        else:
            print("{}{}{}".format(st,std,ch.get('text')))
    print("")

def createHTML(metadata):
    print('')
    print('<p>{}</p>'.format(metadata['USLT']))
    print('<ul>')
    for cch in metadata['CTOC']:
        ch = metadata['CHAP'][cch]
        st = ""
        std = ""
        if showtime:
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
    global debug, output, showtime
    inputfile = ""
    description = (
            'Script to pull the metadata out of a Podcast '
            'and format it.\n'
            '---------------------------------------------'
            '-----------------------------\n'
            )
    parser = ArgParser(description=description)
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

    podcast = PodcastMetadata(inputfile)
    metadata = podcast.extractMetadata()

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


