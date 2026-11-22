import logging


def configure_logging() -> None:
    """Configure application logs.

    Submitted messages, screenshots, and recordings must never be written here.
    Log event types and paths only.
    """

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
