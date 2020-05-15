#!/bin/bash

fname="/Users/jking/mostlysecurity/finals/mostlysecurity${1}.mp3"

#echo $fname

./pullmetadata.py -i $fname -o HTML -s

#echo '\n\n\n\n'

#./pullmetadata.py -i ~/mostlysecurity/finals/mostlysecurity106.mp3 -o MD -s


