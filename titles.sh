#!/bin/sh

fname="/Users/jking/mostlysecurity/finals/mostlysecurity${1}.mp3"

./pullmetadata.py -i $fname -o MD -s | grep -i Title | sed -e "s/Title: //"


