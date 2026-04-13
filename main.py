import argparse
import json
import os
import subprocess
from enum import Enum
from urllib.parse import urlparse

from yt_dlp import YoutubeDL

COOKIE = os.getenv("COOKIE", "")
HOME_DIR = os.getenv("HOME", "")
DATA_PATH = os.getenv("DATA_PATH", "data.json")
OUTPUT_BASE_DIR = os.getenv("OUTPUT_BASE_DIR", f"{HOME_DIR}/Downloads/data")
START = int(os.getenv("START", 1))


class DataType(Enum):
    """
    データの種類.
    """

    IMAGE = 1
    VIDEO = 2
    YOUTUBE = 3


def get_data_type(url: str) -> DataType:
    """
    URL からデータの種類を取得する.
    """
    parsed = urlparse(url)

    if parsed.netloc == "www.youtube.com":
        return DataType.YOUTUBE

    if url.endswith((".png", ".jpg", ".jpeg")):
        return DataType.IMAGE

    if url.endswith((".mp4", ".mov", ".m3u8")):
        return DataType.VIDEO

    raise ValueError(f"Invalid URL: {url}")


def get_command_for_image(url: str, output_path: str) -> str:
    """
    画像をダウンロードするためのコマンドを取得する.
    """
    if COOKIE:
        return f'wget --header "cookie: {COOKIE}" "{url}" -O "{output_path}"'
    else:
        return f'wget "{url}" -O "{output_path}"'


def get_command_for_video(url: str, output_path: str) -> str:
    """
    動画をダウンロードするためのコマンドを取得する.
    """
    if COOKIE:
        return f'ffmpeg -headers "Cookie: {COOKIE}" -i "{url}" -c copy "{output_path}"'
    else:
        return f'ffmpeg -i "{url}" -c copy "{output_path}"'


def download_data(url: str, output_path: str) -> None:
    """
    データをダウンロードする.
    """
    data_type = get_data_type(url)

    if data_type == DataType.IMAGE:
        command = get_command_for_image(url, output_path)
        subprocess.run(command, shell=True, check=True)
        return

    if data_type == DataType.VIDEO:
        command = get_command_for_video(url, output_path)
        subprocess.run(command, shell=True, check=True)
        return

    if data_type == DataType.YOUTUBE:
        output_path_without_ext, ext = output_path.rsplit(os.extsep, 1)
        params = {
            "format": "bestvideo+bestaudio/best",
            "outtmpl": output_path_without_ext,
            "merge_output_format": ext,
        }
        with YoutubeDL(params) as ydl:
            ydl.download([url])
        return


def download_data_list(data_list: list, input_format: str, output_dir: str = OUTPUT_BASE_DIR) -> None:
    """
    データのリストをダウンロードする.
    """
    os.makedirs(output_dir, exist_ok=True)

    if input_format == "simple":
        for i, url in enumerate(data_list):
            data_type = get_data_type(url)
            type_to_ext = {DataType.IMAGE: "png", DataType.VIDEO: "mp4", DataType.YOUTUBE: "mp4"}
            output_path = os.path.join(output_dir, f"{START + i:04}.{type_to_ext[data_type]}")
            download_data(url, output_path)
        return

    if input_format == "standard":
        for url, output_filename in data_list:
            output_path = os.path.join(output_dir, output_filename)
            download_data(url, output_path)
        return

    raise ValueError(f"Invalid input format: {input_format}")


def main() -> None:
    """
    メイン関数.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-format", choices=["simple", "standard"], required=True)

    args = parser.parse_args()
    input_format = args.input_format

    data = json.load(open(DATA_PATH))

    if isinstance(data, list):
        download_data_list(data, input_format)
        return

    if isinstance(data, dict):
        for dir_name, data_list in data.items():
            output_dir = os.path.join(OUTPUT_BASE_DIR, dir_name)
            download_data_list(data_list, input_format, output_dir)
        return


if __name__ == "__main__":
    main()
