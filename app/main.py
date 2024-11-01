import logging
import datetime
from typing import Tuple

import numpy as np
from google.protobuf.internal.well_known_types import Timestamp
from make87_messages.image.compressed.image_jpeg_pb2 import ImageJPEG
from make87 import initialize, get_publisher_topic, resolve_topic_name

import yt_dlp
import av
import cv2


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
    topic_name = resolve_topic_name(name="IMAGE_DATA")
    topic = get_publisher_topic(name=topic_name, message_type=ImageJPEG)

    youtube_url = "https://www.youtube.com/watch?v=faUNhaRLpMc"
    stream_url = get_stream_url(youtube_url, resolution="1920x1080")

    if stream_url is None:
        print("Desired resolution not available.")
        exit()

    start_world_datetime = datetime.datetime.now(datetime.UTC)
    start_video_time = None

    for time, frame in read_frames_from_stream(stream_url, start_time=180):
        if start_video_time is None:
            start_video_time = time

        delta_time = datetime.timedelta(seconds=time - start_video_time)
        _, frame_jpeg = cv2.imencode(".jpeg", frame)
        message = ImageJPEG(data=frame_jpeg.tobytes())
        message.timestamp.FromDatetime(start_world_datetime + delta_time)
        topic.publish(message)


if __name__ == "__main__":
    main()
