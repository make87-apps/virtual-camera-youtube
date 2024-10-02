import logging
import time

from make87_messages.text.PlainText_pb2 import PlainText
from make87 import get_topic, PublisherTopic, topic_names


def main():
    topic = get_topic(name=topic_names.HELLO_WORLD_MESSAGE)

    while True:
        message = PlainText(body=f"Hello, World!")
        topic.publish(message)
        logging.info(f"Published: {message}")
        time.sleep(1)


if __name__ == "__main__":
    main()
