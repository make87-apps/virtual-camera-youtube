import logging
import time

from make87_messages.image.compressed.image_jpeg_pb2 import ImageJPEG
from make87_messages.text.text_plain_pb2 import PlainText
from make87 import get_topic, PublisherTopic, topic_names

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


def read_frames_from_stream(stream_url, start_time=0):
    # Open the video stream
    container = av.open(stream_url)

    # Seek to the desired start time (in microseconds)
    start_time_microseconds = int(start_time * 1e6)
    stream = container.streams.video[0]
    container.seek(start_time_microseconds, any_frame=False, backward=True, stream=stream)

    for frame in container.decode(video=0):
        # Convert the frame to a NumPy array
        img = frame.to_ndarray(format="bgr24")
        yield img

    container.close()


def main():
    topic = get_topic(name=topic_names.IMAGE_DATA)

    youtube_url = "https://www.youtube.com/watch?v=faUNhaRLpMc"  # Replace with the actual video URL
    stream_url = get_stream_url(youtube_url, resolution="1920x1080")

    if stream_url is None:
        print("Desired resolution not available.")
        exit()

    for frame in read_frames_from_stream(stream_url, start_time=180):
        ret, frame_jpeg = cv2.imencode(".jpeg", frame)
        if not ret:
            logging.error("Error: Could not encode frame to JPEG.")
            break

        frame_jpeg_bytes = frame_jpeg.tobytes()

        message = ImageJPEG(data=frame_jpeg_bytes)
        topic.publish(message)


if __name__ == "__main__":
    main()
