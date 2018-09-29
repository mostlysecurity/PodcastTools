# PodcastTools
Various tools for the Mostly Security podcast


# Tools we use for the Mostly Security Podcast
Our basic tools for Workflow:
* [Skype](https://www.skype.com/) for our remote comms
* [Piezo](https://rogueamoeba.com/piezo/) for recording the Skype calls (mostly for backup)
* [QuickTime](https://support.apple.com/downloads/quicktime) for recording individual audio feeds
* [Audacity](https://www.audacityteam.org/) for combining the QuickTime audio tracks and editing, exporting to WAV
* [Forecast](https://overcast.fm/forecast) to convert the Audacity WAV to MP3 and add in all the fancy ID3 tags and chapter markers, etc
* [Libsyn](https://www.libsyn.com/) for hosting the podcast as well as the [Mostly Security Podcast Blog](http://podcast.mostlysecurity.net/)
* [GitHub](https://www.github.com/mostlysecurity) for hosting the [Mostly Security](https://mostlysecurity.com) homepage and any tools we build

### pullmetada.py
After we have created the Forecast MP3 with titles, chapter, urls, etc; we were doing a bit of hand editing the Libsyn blog page.  This tools simply extracts the ID3 tags and outputs to JSON, Markdown or HTML.  It is very much a work in progress, and tailored to how we publish stuff into libsyn, but it was a simple optimization to save some time.





