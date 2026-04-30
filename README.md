# Simple wrapper script for yt-dlp

Simple wrapper for [yt-dlp](https://github.com/yt-dlp/yt-dlp) written in Powershell.

usage:
```bash
  $ ./script.py -format FORMAT [-xXXX] [-X] [LINK ...] [[-format FORMAT [-xXXX] [-X] [LINK ...]] ...]
```


The script requires [yt-dlp](https://github.com/yt-dlp/yt-dlp) and
[ffmpeg](https://git.ffmpeg.org/ffmpeg.git) to be reachable through the **$PATH**
environment variable to function properly.  Before doing any operation, the
script will check if the dependencies are installed and are reachable, and will
*scream* if they are not.

Starting from yt-dlp version **2025.11.12**, it needs an additional JavaScript
runtime present on the machine and reachable via **$PATH**.  The script will
check if one of the following runtimes is installed:
- node
- deno
- bun
- quickjs

To download them properly on Windows, i suggest to do it via the
[scoop.sh](https://www.scoop.sh) package manager.  On other systems use whatever
package manager is available.
