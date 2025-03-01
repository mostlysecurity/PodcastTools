#!/bin/sh

fname="$HOME/mostlysecurity/finals/mostlysecurity${1}.mp3"

#./posttobsky.py -i ~/Podcast/mostlysecurity377.mp3 
echo -e "./posttobsky.py -i ${fname}"
./posttobsky.py -i ${fname}

# ./posttobsky.py -p http://podcast.mostlysecurity.com/377-competitive-puzzling -t "Competitive Puzzling" -e 377
echo -e "./posttobsky.py -e ${1} -t \"${2}\" -p http://podcast.mostlysecurity.com/${3}"
./posttobsky.py -e ${1} -t "${2}" -p http://podcast.mostlysecurity.com/${3}
