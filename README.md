# Simple wrapper script for yt-dlp


Simple wrapper to use ease the use of [yt-dlp](https://github.com/yt-dlp/yt-dlp).
It handles multiple inputs and tidies up the output files in different
directories.

usage:
```bash
$ ./script.py -format FORMAT [-xXXX] [-X] [LINK ...] [[-format FORMAT [-xXXX] [-X] [LINK ...]] ...]
```

The wrapper requires [yt-dlp](https://github.com/yt-dlp/yt-dlp) and
[ffmpeg](https://git.ffmpeg.org/ffmpeg.git) to be reachable through the **$PATH**
environment variable to function properly.  Before doing any operation, the
script will check if the dependencies are installed and are reachable, and will
*scream* if they are not.

## Usage example
Here is a quick usage example section on how to use this wrapper.

To get the complete help message, you can invoke the following command from a
shell:
```bash
$ ./yt-dlp_wrapper.py -h
```

The following example downloads a youtube video as an mp3 file.  To specify the
format just use the -f flag before providing the media link.
```bash
$ ./yt-dlp_wrapper.py -f mp3 https://youtu.be/dQw4w9WgXcQ?si=DM9jndSpwaDfCk4N
```

The wrapper is not limited on only one input at a time, but can manage different
media links and switching format on the go, audio and video:
```bash
$ ./yt-dlp_wrapper.py -f mp3 https://youtu.be/8Cya2MV_GRI?si=_Mp-8YqhbAvXARrv \
                      -f mp4 https://youtu.be/qjWkNZ0SXfo?si=5RX9GhqpnIy0ZdYq
```

The last feauture of the wrapper is to pass directly to yt-dlp with the -x flag,
and to clean them up with -X:
```bash
$ ./yt-dlp_wrapper.py -f mp3 -x --cookies-from-browser=FIREFOX \
                https://youtu.be/GYlpoteRT6o?si=sQaQuL27QveivScJ
```

## Dependencies
Starting from yt-dlp version **2025.11.12**, it needs an additional JavaScript
runtime present on the machine and reachable via **$PATH**.  The script will
check if one of the following runtimes is installed:
- node
- deno
- bun
- quickjs

To download them properly on Windows, i suggest to do it via the
[scoop.sh](https://www.scoop.sh) package manager.  On other, more reasonable
systems, use whatever package manager is available.
