#!/bin/bash

if echo "$HOME" | grep -q "wuehler"; then
    echo "Eric's System"
    fname="$HOME/Podcast/mostlysecurity${1}.mp3"
else
    echo "Jon's System"
    fname="$HOME/mostlysecurity/finals/mostlysecurity${1}.mp3"
fi


./pullmetadata.py -i $fname -o HTML -s


