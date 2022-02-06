"""wrapper for notify-send"""
from subprocess import CalledProcessError, run


def notify(title: str, message: str) -> None:
    """Sends a notification using notify-send"""

    cmd = ["notify-send", title, message]

    try:
        run(cmd, check=True)
    except CalledProcessError:
        print("Error sending notification using notify-send")

    return
