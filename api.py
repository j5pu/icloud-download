# coding=utf-8
"""
Icloud-download Api Module
"""
import os

import pyicloud
import rich.pretty
import rich.traceback
import sys
from pyicloud import PyiCloudService

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
if api.requires_2fa:
    print("Two-factor authentication required.")
    code = input("Enter the code you received of one of your approved devices: ")
    result = api.validate_2fa_code(code)
    print("Code validation result: %s" % result)

    if not result:
        print("Failed to verify security code")
        sys.exit(1)

    if not api.is_trusted_session:
        print("Session is not trusted. Requesting trust...")
        result = api.trust_session()
        print("Session trust result %s" % result)

        if not result:
            print("Failed to request trust. You will likely be prompted for the code again in the coming weeks")
elif api.requires_2sa:
    import click
    print("Two-step authentication required. Your trusted devices are:")

    devices = api.trusted_devices
    for i, device in enumerate(devices):
        print(
            "  %s: %s" % (i, device.get('deviceName',
            "SMS to %s" % device.get('phoneNumber')))
        )

    device = click.prompt('Which device would you like to use?', default=0)
    device = devices[device]
    if not api.send_verification_code(device):
        print("Failed to send verification code")
        sys.exit(1)

    code = click.prompt('Please enter validation code')
    if not api.validate_verification_code(device, code):
        print("Failed to verify verification code")
        sys.exit(1)


api.files.params["dsid"] = api.account.family[0].dsid  # api.data['dsInfo']['dsid']
