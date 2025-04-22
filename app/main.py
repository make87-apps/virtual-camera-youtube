import datetime
import make87
from typing import Tuple
import logging

import av
import cv2
import numpy as np
import yt_dlp
from make87 import initialize, get_publisher
from make87_messages.image.compressed.image_jpeg_pb2 import ImageJPEG


def get_stream_url(youtube_url, resolution="1920x1080"):
    ydl_opts = {
        "format": f'bestvideo[height<={resolution.split("x")[1]}]+bestaudio/best',
        "quiet": True,
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        formats = info.get("formats", [info])

        # Find the format that matches the desired resolution
        for f in formats:
            if f.get("height") == int(resolution.split("x")[1]) and f.get("vcodec") != "none":
                return f["url"]

        # If exact resolution not found, get the best available below desired resolution
        for f in formats:
            if f.get("height") <= int(resolution.split("x")[1]) and f.get("vcodec") != "none":
                return f["url"]

        # If no suitable format is found, return None
        return None


def read_frames_from_stream(stream_url, start_time=0) -> Tuple[float, np.ndarray]:
    # Open the video stream
    container = av.open(stream_url)

    # Seek to the desired start time (in microseconds)
    start_time_microseconds = int(start_time * 1e6)
    stream = container.streams.video[0]
    container.seek(start_time_microseconds, any_frame=False, backward=True, stream=stream)

    for frame in container.decode(video=0):
        yield frame.time, frame.to_ndarray(format="bgr24")

    container.close()


def main():
    initialize()
    topic = get_publisher(name="IMAGE_DATA", message_type=ImageJPEG)

    youtube_url = make87.get_config_value("YOUTUBE_URL", "https://www.youtube.com/live/s2nVwrJMSUQ")
    stream_url = get_stream_url(youtube_url, resolution="1920x1080")

    if stream_url is None:
        print("Desired resolution not available.")
        exit()

    start_world_datetime = datetime.datetime.now(datetime.UTC)
    start_video_time = None

    for time, frame in read_frames_from_stream(stream_url, start_time=0):
        if start_video_time is None:
            start_video_time = time

        delta_time = datetime.timedelta(seconds=time - start_video_time)
        _, frame_jpeg = cv2.imencode(".jpeg", frame)
        message = ImageJPEG(data=frame_jpeg.tobytes())
        message.header.timestamp.FromDatetime(start_world_datetime + delta_time)
        topic.publish(message)
    else:
        logging.info("Finished receiving frames from stream.")


if __name__ == "__main__":
    main()
