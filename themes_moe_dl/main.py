"""
Copyright 2016 Hermann Krumrey

This file is part of themes.moe-dl.

    themes.moe-dl offers functionality to download anime openings
    listed on themes.moe and converting them into audio files

    themes.moe-dl is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    themes.moe-dl is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with themes.moe-dl.  If not, see <http://www.gnu.org/licenses/>.
"""

# imports
import os
import shutil
import urllib.request
from themes_moe_dl.parsers.HtmlParser import HtmlParser
from themes_moe_dl.parsers.ArgumentParser import ArgumentParser
from themes_moe_dl.converters.WebmConverter import WebmConverter
from themes_moe_dl.userinterfaces.InteractiveCli import InteractiveCli
from themes_moe_dl.ffmpeg_installation.FfmpegInstaller import FfmpegInstaller


# noinspection PyUnresolvedReferences
def main():
    """
    The main method of the program

    :return: None
    """
    if not FfmpegInstaller.is_installed():
        FfmpegInstaller.install()

    arguments = ArgumentParser.parse()

    if not arguments.userinterface:
        process(arguments.username, arguments.destination, arguments.format, arguments.keepsource, print)
    elif arguments.userinterface == "cli":
        InteractiveCli.run()
    else:
        from themes_moe_dl.userinterfaces.Gui import Gui
        Gui().start()


def process(user_name: str, destination: str, destination_format: str, keep_source: bool, progress_callback: callable)\
        -> None:
    """
    Processes the download request of the user

    :param user_name: the myanimelist.net username of the user
    :param destination: the destination directory of the downloads
    :param destination_format: the format that should be saved
    :param keep_source: can be set to determine if the source files should be kept or not
    :param progress_callback: Callback method to display the progress of the method
    :return: None
    """
    root_dir = os.path.join(destination, "themes.moe")
    validate_directory(root_dir)

    formats = ["webm"]

    if destination_format == "all":
        formats += WebmConverter.supported_formats
    elif destination_format not in WebmConverter.supported_formats:
        progress_callback("Format not supported")
        return
    else:
        formats.append(destination_format)

    for file_format in formats:
        validate_directory(os.path.join(root_dir, file_format))
    source_directory = os.path.join(root_dir, "webm")
    formats.pop(0)

    shows = HtmlParser(user_name).parse()

    for show in shows:
        show_source_directory = os.path.join(source_directory, show.show_name)
        validate_directory(show_source_directory)
        destination_directories = {}

        for file_format in formats:
            file_format_directory = os.path.join(root_dir, file_format, show.show_name)
            validate_directory(file_format_directory)
            destination_directories[file_format] = file_format_directory

        for song in show.songs:
            try:  # Pokemon Exception handling
                song_file = os.path.join(show_source_directory, song.song_name + ".webm")

                if not os.path.isfile(song_file):
                    print("Downloading " + song.song_link)
                    progress_callback("DL: " + show.show_name + " - " + song.song_name + ".webm")

                    def report_dl_progress(count, block_size, total_size):
                        percentage = str(int(count*block_size * (100 / total_size)))
                        progress_callback("\r" + percentage + "%", end="")

                    urllib.request.urlretrieve(song.song_link, song_file, reporthook=report_dl_progress)
                    progress_callback("")

                else:
                    progress_callback("skipping downloading existing file " + song_file)

                for destination_format in destination_directories:
                    converted_file = os.path.join(destination_directories[destination_format],
                                                  song.song_name + "." + destination_format)

                    if not os.path.isfile(converted_file):
                        progress_callback("converting to " + destination_format)
                        WebmConverter.convert(song_file, converted_file, destination_format)
                    else:
                        progress_callback("skipping converting existing file " + converted_file)
            except Exception as e:
                print(str(e))

    if not keep_source and "webm" not in formats:
        shutil.rmtree(source_directory)


def validate_directory(directory: str) -> None:
    """
    Checks if a directory exists and creates it if that is not the case

    :param directory: The directory to check
    :return: None
    """
    if not os.path.isdir(directory):
        os.makedirs(directory)


if __name__ == '__main__':
    main()
