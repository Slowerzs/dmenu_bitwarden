"""Manages bitwarden vault"""

import json
import os
import subprocess


class BitWarden:
    """
    Class with methods wrapping bitwarden cli interface
    """

    def __init__(self):
        self._is_unlocked = False
        self._folders = {}

    @property
    def is_unlocked(self):
        "is_unlocked getter"
        return self._is_unlocked

    @is_unlocked.setter
    def is_unlocked(self, value):
        "is_unlocked setter"
        self._is_unlocked = value

    @property
    def folders(self):
        "folders getter"
        return self._folders

    @folders.setter
    def folders(self, value):
        self._folders = value

    def get_folders(self) -> None:
        """Creates a dict linking foldersId with their names"""

        cmd = ["/usr/bin/bw", "list", "folders"]

        try:
            items = subprocess.run(cmd, capture_output=True, check=True)
        except subprocess.CalledProcessError:
            return

        data = json.loads(items.stdout)

        folders = {}

        for item in data:
            folders[item["id"]] = item["name"]
        self.folders = folders

        return

    def get_items(self) -> list:
        """Get all entries from bw list item"""

        cmd = ["/usr/bin/bw", "list", "items"]

        try:
            items = subprocess.run(cmd, capture_output=True, check=True)
        except subprocess.CalledProcessError:
            return []

        data = json.loads(items.stdout)

        creds = []

        for item in data:

            if item.get('folderId') and item['folderId'] not in self.folders:
                self.get_folders()

            if item.get('folderId') is None:
                group = 'Default'
            else:
                group = self.folders[item.get("folderId")]

            desc = f'{group}/{item["name"]} : {item["login"]["username"]}'

            creds.append((desc, item["login"]["password"]))

        creds = sorted(creds, key=lambda i: i[0].lower())

        return creds

    def unlock(self, password: str) -> bool:
        """wrapper for bw unlock"""

        cmd = ["/usr/bin/bw", "unlock", password, "--raw"]

        try:
            unlock = subprocess.run(cmd, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            print(e)
            print(e.stderr)
            self.is_unlocked = False
            return False

        os.environ["BW_SESSION"] = unlock.stdout.decode()
        self.is_unlocked = True

        return True

    def lock(self) -> bool:
        """wrapper for bw lock"""

        if self.is_unlocked:
            del os.environ["BW_SESSION"]
            cmd = ["/usr/bin/bw", "lock"]
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError:
                return False

            self.is_unlocked = False

        return True
