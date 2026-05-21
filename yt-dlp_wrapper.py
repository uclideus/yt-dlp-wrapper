#!/usr/bin/env python3

# Simple wrapper to use ease the use of yt-dlp (https://github.com/yt-dlp/yt-dlp)

# It handles multiple inputs and tidies up the output files in different
# directories.  To get the complete help message, please invoke the following
# command from a shell:

# $ ./yt-dlp_wrapper.py -h

import sys
import shutil
import subprocess
import re
import os
import glob
import math
import requests
from enum import *

class Log_Level(Enum):
    info  = 0
    warn  = 1
    error = 2
    debug = 3

    def __le__(self, other):
        if self.__class__ == other.__class__:
            return self.value <= other.value
        return NotImplemented

def trace_log(log_level, *args):
    if log_level == Log_Level.info    \
       and SCRIPT_DATA.max_log_level >= Log_Level.info:
        print("[INFO]\t", *args)
    elif log_level == Log_Level.warn  \
         and SCRIPT_DATA.max_log_level >= Log_Level.warn:
        print("[WARN]\t", *args)
    elif log_level == Log_Level.error \
         and SCRIPT_DATA.max_log_level >= Log_Level.error:
        print("[ERR]\t", *args, file=sys.stderr)
    elif log_level == Log_Level.debug \
         and SCRIPT_DATA.max_log_level >= Log_Level.debug:
        print("[DEB]\t", *args, file=sys.stderr)


class Script_State:
    passed_arguments = ""
    js_engine        = None
    current_format   = None

state = Script_State()

class Media_Target :
    media_format = ""
    cmd          = ""
    def __init__(self, media_format, cmd):
        self.media_format = media_format
        self.cmd = cmd

class JS_Engine:
    canonical_name = ""
    program_name   = ""

    def __init__(self, canonical_name, program_name):
        self.canonical_name = canonical_name
        self.program_name   = program_name

class Script_Data:
    format_list  = [
        # audio
        Media_Target("mp3",
            "yt-dlp %js_engine% -x --audio-format mp3 -f ba --embed-metadata --embed-thumbnail %current_link% %passed_arguments%  -o %(title)s.%(ext)s"),
        Media_Target("m4a",
            "yt-dlp %js_engine% -x --audio-format m4a -f ba --embed-metadata --embed-thumbnail %current_link% %passed_arguments%  -o %(title)s.%(ext)s"),
        # video
        Media_Target("mp4",
            "yt-dlp %js_engine% --embed-metadata --embed-thumbnail -f bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best %current_link% %passed_arguments% -o %(title)s.%(ext)s")
    ]
    help_header  = [
        "usage: ./script.py -format FORMAT [-x XXX] [-X] [LINK ...] [[-format FORMAT [-x XXX] [-X] [LINK ...]] ...]",
        "usage: ./script.py --help | -h"
    ]
    dependencies_js_engines = [
        JS_Engine("node", "node"),
        JS_Engine("deno", "deno"),
        JS_Engine("bun", "bun"),
        JS_Engine("quickjs", "qjs")
    ]
    dependencies_programs = [
        "yt-dlp", "ffmpeg"
    ]
    max_log_level   = Log_Level.debug
    max_salt_level  = 100

SCRIPT_DATA = Script_Data()


def check_dependencies():
    is_a_dep_missing = False
    for dep in SCRIPT_DATA.dependencies_programs:
        if not shutil.which(dep):
            trace_log(Log_Level.error, f"Dependency failure :: {dep} is not found")
            is_a_dep_missing = True
        else:
            trace_log(Log_Level.debug, f"Dependency success :: {dep}")
    if is_a_dep_missing:
        trace_log(Log_Level.error, ">>> Abort")
        exit(1)


def print_presentation_message():
    message = r'''
       _                _  _
      | |_             | || |
 _   _|  _| ______  _ _| || | _ _ _
| | | | |  |______||  _  || ||  _  |
| |_| | |_         | |_| || || |_| |
 \__  |\__|        |_ _ _||_||  _ _|
 ___| |                      | |
 \___/                       |_|
'''
    print(message)


def print_help_message():
    for usage in SCRIPT_DATA.help_header:
        print(usage)
    help_message = f'''
FORMATs:
The formats currently supported are the following:
  audio:
    mp3  lossy audio format, MPEG-3
    m4a  lossy audio format, MPEG-4
  video:
    mp4  lossy video format, MPEG-4

Miscellaneous Arguments:
  -h, --help    Display this help message
  -f, --format  Select a desired FORMAT to download the media
  -x            Pass argument XXX directly to yt-dlp
  -X            Reset arguments passed directly to yt-dlp

The quality of the final media should be the best yt-dlp can generate.
'''
    print(help_message)


# checks if the first argument is a file format, and skips until it finds a
# valid one
def check_begin_arguments():
    sys.argv.pop(0) # program name
    if len(sys.argv) == 0:
        trace_log(Log_Level.error, "Not enough arguments")
        for usage in SCRIPT_DATA.help_header:
            trace_log(Log_Level.error, f">>> {usage}")
        trace_log(Log_Level.error, f">>> or provide the flag --help to read the instructions")
        exit(1)
    elif sys.argv[0] == "--help" \
    or   sys.argv[0] == "-h"     \
    or   sys.argv[0] == "-help"  \
    or   sys.argv[0] == "help":
        print_help_message()
        exit(0)


# yt-dlp needs an external js runtime to work properly.  I suggest to install a
# minimal one like deno or quickjs from your repo of choice if no one is already
# installed
def check_js_engine():
    js_engines = SCRIPT_DATA.dependencies_js_engines
    is_engine_found = False
    found_js_engine = None
    for engine in js_engines:
        if shutil.which(engine.program_name):
            is_engine_found = True
            found_js_engine = engine
            break
    if is_engine_found == False:
        trace_log(Log_Level.error, f"Dependency failure :: no supported js runtime is found")
        trace_log(Log_Level.error, f">>> the supported engines are: ")
        for engine in js_engines:
            trace_log(Log_Level.error, f">>> {engine.canonical_name} :: {engine.program_name}")
        trace_log(Log_Level.error, "Abort")
        exit(1)
    else:
        state.js_engine = "--js-runtimes " + found_js_engine.canonical_name
        trace_log(Log_Level.info, f"Using js engine :: {found_js_engine.canonical_name}")


# check if the format is supported
def check_format(format):
    is_format_valid = False
    for media_target in SCRIPT_DATA.format_list:
        if format == media_target.media_format:
            state.current_format = format
            trace_log(Log_Level.info, f"Format set to :: {format}")
            is_format_valid = True
    if not is_format_valid:
        trace_log(Log_Level.warn, f"The format provided is not valid :: {format}")
        trace_log(Log_Level.warn, "IGNORING MEDIA LINKS until a valid format is provided")
        state.current_format = None


# remove telemetry part from youtube link
def telemetry_handle_youtube_link(media_link):
    link = media_link
    if media_link.find("youtube") > -1 or \
       media_link.find("youtu.be") > -1:
        link = re.sub("\\?si=[0-9A-Za-z]*", "", link)
    return link


# Salt file if there is a file in the directory with the same name.  This is
# useful in such cases when a series of sequential videos have the same exact
# name but are not the same content (for example instagram stories).  The
# salting is performed in the same sequence as the given input media link.
def media_salt_file(file_name, directory):
    new_file_name = ""
    for salt in range(1, SCRIPT_DATA.max_salt_level):
        salt_str = str(salt).zfill(
            math.floor(math.log10(SCRIPT_DATA.max_salt_level) + 1)
        )
        new_file_name = file_name.replace(f".{state.current_format}",
                                          f" - {salt_str}.{state.current_format}")
        if not os.path.exists(f"{directory}/{new_file_name}"):
            os.rename(file_name, new_file_name)
            return new_file_name
    return None

# Divides all the downloaded media in separate directories based on the media
# target.
def media_move():
    directory = state.current_format
    if directory == None or directory == "":
        return
    if os.path.exists(directory):
        if not os.path.isdir(directory):
            trace_log(Log_Level.warn, f"Cannot create directory {directory} because something is present with the same name")
            trace_log(Log_Level.warn, f">>> Please take care manually")
            return
        else:
            # it is already a directory
            pass
    else:
        trace_log(Log_Level.info, f"Creating directory :: {directory}")
        os.mkdir(directory)
    # Tidying up It needs the for loop to cleanup other cases when the download
    # not completed properly
    for file_name in glob.glob(f"*.{state.current_format}"):
        try:
            trace_log(Log_Level.info, f"Moving file :: '{file_name}' to '{directory}'")
            shutil.move(file_name, directory)
        except OSError as err:
            if os.path.exists(f"{directory}/{file_name}"):
                trace_log(Log_Level.warn, f"Unable to move file :: a file with the same name already exists in '{directory}'")
                trace_log(Log_Level.warn, ">>> Trying salting file")
                new_file_name = media_salt_file(file_name, directory)
                if new_file_name == None:
                    trace_log(Log_Level.error, f">>> Cannot salt file, how many media did you download?")
                else:
                    trace_log(Log_Level.info, f">>> File salted :: '{file_name}' -> '{new_file_name}'")
                    trace_log(Log_Level.info, f">>> Moving file :: '{new_file_name}' to '{directory}'")
                    shutil.move(new_file_name, directory)
                    return
            trace_log(Log_Level.error, "Unable to move file :: UNKNOWN ERROR")


def media_download(media_link):
    found_media_target = None
    command = ""
    for media_target in SCRIPT_DATA.format_list:
        if state.current_format == media_target.media_format:
            found_media_target = media_target
            break
    if found_media_target == None:
        trace_log(Log_Level.warn, f"No valid format given, ignoring media link :: {media_link}")
    else:
        media_link = telemetry_handle_youtube_link(media_link)
        command = found_media_target.cmd.replace("%js_engine%", state.js_engine) \
                                        .replace("%current_link%", media_link)   \
                                        .replace("%passed_arguments%", state.passed_arguments)
        status = None
        try:
            trace_log(Log_Level.info, f"Executing command: {command}")
            # cleaning the string list because subprocess.run does not like
            # empty strings
            command = [it for it in command.split(" ") if it != ""]
            status = subprocess.run(command)
        except Exception as err:
            pass
        # short-circuiting
        if status != None and status.returncode == 0:
            trace_log(Log_Level.info, f">>> Media downloaded successfully")
        else:
            trace_log(Log_Level.warn, f">>> Media NOT downloaded successfully")


# checks if the media_link is a valid and reachable http link, and then calls
# for the download
def media_handle_link(media_link):
    media_link_bak = media_link

    if media_link.startswith("-"):
        trace_log(Log_Level.warn, f"Possible broken link: {media_link}")
        trace_log(Log_Level.warn, ">>> Skipping...")
        return

    if not (media_link.startswith("http://") or media_link.startswith("https://")):
        # http should work in almost every case where there is https
        media_link = "http://" + media_link

    resp = None
    try:
        # throws exception on error with link, i would have preferred it to return None
        resp = requests.get(media_link)
    except Exception as err:
        trace_log(Log_Level.warn, f"Link provided is not link :: {media_link_bak}")
        trace_log(Log_Level.debug, f">>> Response :: {resp}")
        return

    if resp.ok:
        media_download(media_link)
        media_move()
    else:
        trace_log(Log_Level.warn,  f"Link provided is not reachable :: {media_link}")
        trace_log(Log_Level.debug, f">>> Response :: {resp}")
        trace_log(Log_Level.warn,  f">>> Skipping...")


# main loop of the execution, goes one by one on the arguments given by the user
# and does all the necessary checks by the function calls
def eval_arguments():
    while len(sys.argv) > 0:

        if sys.argv[0] == "--format" \
        or sys.argv[0] == "-f":
            sys.argv.pop(0)
            if len(sys.argv) == 0:
                trace_log(Log_Level.error, "You provided -format without specifying the FORMAT, are you dumb?")
                exit(1)
            format = sys.argv[0]
            check_format(format)

        elif sys.argv[0].startswith("-x"):
            sys.argv.pop(0)
            arg = sys.argv[0]
            state.passed_arguments += " " + arg
            trace_log(Log_Level.info,  f"Passthrough argument :: {arg}")
            trace_log(Log_Level.debug, f">>> Cumulative arguments :: {arg}")

        elif sys.argv[0] == "-X":
            state.passed_arguments = ""
            trace_log(Log_Level.info, "-X :: Clearing given arguments")

        else:
            # not a flag, treat it as a possible link
            media_link = sys.argv[0]
            media_handle_link(media_link)

        # removing the first element of the array when it gets evaluated
        sys.argv.pop(0)


def main():
    print_presentation_message()
    check_dependencies()
    check_begin_arguments()
    check_js_engine()

    trace_log(Log_Level.info, f"Starting Program")
    eval_arguments()
    trace_log(Log_Level.info, "Program terminated successfully")


if __name__ == "__main__":
    main()
