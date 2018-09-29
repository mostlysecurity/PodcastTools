# ID3 Spec
Taken from [WikiPedia ID3](https://en.wikipedia.org/wiki/ID3)

v2.3 | v2.4   | Name
-----|--------|--------
AENC |        | Audio encryption
N/A  | ASPI   | Audio seek point index
APIC |        | Attached picture
COMM |        | Comments
COMR |        | Commercial frame
ENCR |        | Encryption method registration
EQUA | EQU2   | Equalization
ETCO |        | Event timing codes
GEOB |        | General encapsulated object
GRID |        | Group identification registration
IPLS | TIPL   | Involved people list
LINK |        | Linked information
MCDI |        | Music CD identifier
MLLT |        | MPEG location lookup table
OWNE |        | Ownership frame
PRIV |        | Private frame
PCNT |        | Play counter
POPM |        | Popularimeter
POSS |        | Position synchronisation frame
RBUF |        | Recommended buffer size
RVAD | RVA2   | Relative volume adjustment
RVRB |        | Reverb
N/A  | SEEK   | Seek frame
N/A  | SIGN   | Signature frame
SYLT |        | Synchronized lyric/text
SYTC |        | Synchronized tempo codes
TALB |        | Album/Movie/Show title
TBPM |        | Beats per minute (BPM)
TCOM |        | Composer
TCON |        | Content type
TCOP |        | Copyright message
TDAT | TDRC   | Date
N/A  | TDEN   | Encoding time
TDLY |        | Playlist delay
N/A  | TDRC   | Recording time
N/A  | TDRL   | Release time
N/A  | TDTG   | Tagging time
TENC |        | Encoded by
TEXT |        | Lyricist/Text writer
TFLT |        | File type
TIME | TDRC   | Time
TIT1 |        | Content group description
TIT2 |        | Title/songname/content description
TIT3 |        | Subtitle/Description refinement
TKEY |        | Initial key
TLAN |        | Language(s)
TLEN |        | Length
N/A  | TMCL   | Musician credits list
TMED |        | Media type
N/A  | TMOO   | Mood
TOAL |        | Original album/movie/show title
TOFN |        | Original filename
TOLY |        | Original lyricist(s)/text writer(s)
TOPE |        | Original artist(s)/performer(s)
TORY | TDOR   | Original release year
TOWN |        | File owner/licensee
TPE1 |        | Lead performer(s)/Soloist(s)
TPE2 |        | Band/orchestra/accompaniment
TPE3 |        | Conductor/performer refinement
TPE4 |        | Interpreted, remixed, or otherwise modified by
TPOS |        | Part of a set
N/A  | TPRO   | Produced notice
TPUB |        | Publisher
TRCK |        | Track number/Position in set
TRDA | TDRC   | Recording dates
TRSN |        | Internet radio station name
TRSO |        | Internet radio station owner
TSIZ | Dropped| Size
N/A  | TSOA   | Album sort order
N/A  | TSOP   | Performer sort order
N/A  | TSOT   | Title sort order
TSRC |        | International Standard Recording Code (ISRC)
TSSE |        | Software/Hardware and settings used for encoding
N/A  | TSST   | Set subtitle
TYER | TDRC   | Year
TXXX |        | User defined text information frame
UFID |        | Unique file identifier
USER |        | Terms of use
USLT |        | Unsynchronized lyric/text transcription
WCOM |        | Commercial information
WCOP |        | Copyright/Legal information
WOAF |        | Official audio file webpage
WOAR |        | Official artist/performer webpage
WOAS |        | Official audio source webpage
WORS |        | Official internet radio station homepage
WPAY |        | Payment
WPUB |        | Publishers official webpage
WXXX |        | User defined URL link frame

Notes:
* IPLS of ID3v2.3 maps both to TIPL (the "involved people list") and to TMCL (the "musician credits list").
* TDRC (recording time) consolidates TDAT (date), TIME (time), TRDA (recording dates), and TYER (year).
* TCOM, TEXT, TOLY, TOPE, and TPE1 can contain multiple values separated by a foreslash ("/").
