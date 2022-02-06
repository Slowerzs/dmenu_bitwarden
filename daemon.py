#! /usr/bin/env python3
"""Server for dmenu_bitwarden"""

import argparse
import os
import socket
import subprocess
from threading import Thread
from time import sleep

from dotenv import load_dotenv
from notification import notify

from bitwarden import BitWarden


SOCK_PATH = "/tmp/bitwarden.sock"


class Server:
    """Background server waiting for messages on unix socket"""

    def __init__(self):
        self.bitwarden = BitWarden()

    @staticmethod
    def copy(text: str) -> None:
        """"Copy to clipboard"""

        cmd_copy = ["xclip", "-selection", "c"]
        with subprocess.Popen(cmd_copy,
                              stdin=subprocess.PIPE,
                              close_fds=True) as proc:

            proc.communicate(input=text.encode('UTF-8'))

    @staticmethod
    def get_password() -> str:
        """Retrieves password using dmenu (input hidden)"""

        cmd = [
            "/usr/local/bin/dmenu",
            '-p', '> ',
            '-nf', BACKGROUND_COLOR,
            '-nb', BACKGROUND_COLOR,
            '-sb', FOREGROUND_COLOR
        ]

        with subprocess.Popen(cmd,
                              universal_newlines=True,
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE) as proc:

            assert proc.stdin is not None
            assert proc.stdout is not None

            with proc.stdin as fd_stdin:
                fd_stdin.write('')

            proc.wait()
            password = proc.stdout.read().rstrip('\n')

        return password

    def copy_password(self) -> None:
        """Choose, then copy the password to clipboard then flush it"""

        items = self.bitwarden.get_items()

        cmd_list = [
            "/usr/local/bin/dmenu",
            '-nb', BACKGROUND_COLOR,
            '-sb', FOREGROUND_COLOR,
            "-l", str(DMENU_LINES),
            "-i"
        ]

        with subprocess.Popen(cmd_list,
                              universal_newlines=True,
                              stderr=subprocess.PIPE,
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE) as proc:

            assert proc.stdin is not None
            assert proc.stdout is not None

            with proc.stdin as fd_stdin:
                for item in items:
                    fd_stdin.write(f'{item[0]}\n')

            proc.wait()

            choice = proc.stdout.read().rstrip('\n')
            password = None

            for item in items:
                if item[0] == choice:
                    password = item[1]

            if password is None:
                return

            with open(LOCK_PATH, 'ab'):
                pass

            self.copy(password)
            sleep(FLUSH_TIME)
            self.copy("")

            os.unlink(LOCK_PATH)

    def run(self):
        """Starts listener on unix socket"""

        if os.path.exists(SOCK_PATH):
            print("Removing existing sock")
            os.unlink(SOCK_PATH)

        server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        server.bind(SOCK_PATH)

        while True:

            data = server.recv(10)

            if data == b"OPEN":
                print("Logging in....")

                if not self.bitwarden.is_unlocked:

                    password = os.environ.get("BW_PASSWORD")
                    if password is None:
                        password = self.get_password()

                    if self.bitwarden.unlock(password):
                        print("Successfully unlocked")
                    else:
                        notify("Bitwarden Dmenu", "Error in password")
                        continue

                Thread(target=self.copy_password).start()

            elif data == b"CLOSE":
                print("Locking...")

                if not self.bitwarden.lock():
                    notify("Bitwarden Dmenu", "Error locking")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--lock-path',
        default='/tmp/clip.lock',
        help='Path of lock file'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=20,
        help='Timeout before flushing clipboard'
    )
    parser.add_argument(
        '--lines',
        type=int,
        default=5,
        help='Number of lines in dmenu'
    )
    parser.add_argument(
        '--bg-color',
        metavar='HEX',
        default='#222222',
        help='Dmenu background color'
    )

    parser.add_argument(
        '--fg-color',
        metavar='HEX',
        default='#d79921',
        help='Dmenu highlight color'
    )

    args = parser.parse_args()

    LOCK_PATH = args.lock_path
    FLUSH_TIME = args.timeout
    BACKGROUND_COLOR = args.bg_color
    FOREGROUND_COLOR = args.fg_color
    DMENU_LINES = args.lines

    load_dotenv(".env")

    s = Server()
    s.run()
