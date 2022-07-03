# coding=utf-8
"""
Icloud-download Api Module
"""
import os

import pyicloud
import rich
import rich.pretty
import rich.traceback

from pyicloud import PyiCloudService
from rich import print

setattr(rich.console.Console, "is_terminal", lambda self: True)
Console = rich.console.Console
console: Console = rich.console.Console()

rich.pretty.install(expand_all=True)
rich.traceback.install(show_locals=True, suppress=["click", "_pytest", "rich"])
# %load_ext autoreload
# %autoreload 2

def _driveservice_repr(self):
    return f"{self.__class__.__name__}({self.get_children()})"

def _driveservice_str(self):
    return self.__repr__

def _drive_repr(self):
    return f"{self.__class__.__name__}(name={self.name}, type={self.type})"

def _drive_str(self):
    return self.name


pyicloud.services.drive.DriveService.__repr__ = _driveservice_repr
pyicloud.services.drive.DriveService.__str__ = _drive_str

pyicloud.services.drive.DriveNode.__repr__ = _drive_repr
pyicloud.services.drive.DriveNode.__str__ = _drive_str

email = os.environ['EMAIL']
password = os.environ['INTERNET']
api = PyiCloudService(email)
api.files.params["dsid"] = api.account.family[0].dsid # api.data['dsInfo']['dsid']


