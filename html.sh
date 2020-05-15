#!/bin/bash

fname="$HOME/mostlysecurity/finals/mostlysecurity${1}.mp3"

#echo $fname

./pullmetadata.py -i $fname -o HTML -s


