#!/usr/bin/env python3
# coding=utf-8
"""
Icloud-download Judicial Module
"""
import errno
import time
from dataclasses import dataclass
from dataclasses import field
from dataclasses import InitVar
from pathlib import Path
from shutil import copyfileobj
from typing import NamedTuple

from loguru import logger
from pyicloud.services.drive import DriveNode

from api import *

DEST = {True: "/tmp", False: "/Volumes"}
Node = NamedTuple("Node", dest=Path, src=DriveNode)


@dataclass
class Documents:
    path: InitVar[str] = None
    """Path relative to Documents (default: None to download all in Documents)"""
    dry: bool = False
    tmp: bool = False
    dest: Path = field(default=None, init=False)
    """Local download dest absolute path"""
    src: DriveNode = field(default=None, init=False)
    """iCloud Documents src DriveNode instance"""
    node: Node = field(default=None, init=False)
    """Intermediate node to download"""

    def __post_init__(self, path: str = None):
        self.dest = Path(DEST[self.tmp]) / self.__class__.__name__
        self.src = api.drive[self.__class__.__name__]

        if path is not None:
            path = Path(path)
            self.dest /= path
            for part in path.parts:
                self.src = self.src[part]
        self.node = Node(self.dest, self.src)

        if not self.dest.exists():
            directory = self.dest
            if self.is_file():
                directory = self.dest.parent
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)

    def download(self):
        try:
            if self.is_dir():
                self.mkdir()
                node = self.node
                for children in node.src.get_children():
                    self.node = Node(node.dest / children.name, children)
                    self.download()
            elif not self.node.dest.exists() and self.is_file():
                self.mkdir(file=True)
                if not self.dry:
                    with self.node.src.open(stream=True) as response:
                        with open(self.node.dest, 'wb') as file_out:
                            copyfileobj(response.raw, file_out)
                logger.success(self.node.dest)
        except OSError as oserr:
            if oserr.errno == errno.ENAMETOOLONG:
                logger.warning(f"name too long: {self.node.dest}")
            else:
                raise

    def is_dir(self):
        return self.node.src.type == 'folder'

    def is_file(self):
        return self.node.src.type == 'file'

    def mkdir(self, file: bool = False):
        if not self.node.dest.exists():
            directory = self.node.dest.parent if file else self.node.dest
            if not directory.exists():
                if self.dry:
                    print(f"- Directory: {self.node.dest}")
                    return
                directory.mkdir(parents=True, exist_ok=True)

    def size(self):
        return self.node.src.size

    def size_dest(self):
        return self.node.dest.stat().st_size

    def date_last_open(self):
        return time.mktime(self.node.src.date_last_open.timetuple())

    def date_last_open_dest(self):
        return self.node.dest.stat().st_atime

    def date_changed(self):
        return time.mktime(self.node.src.date_changed.timetuple())

    def date_changed_dest(self):
        return self.node.dest.stat().st_ctime

    def date_modified(self):
        return time.mktime(self.node.src.date_modified.timetuple())

    def date_modified_dest(self):
        return self.node.dest.stat().st_mtime


d = Documents(dry=True)

documents = Documents()
judicial = Documents(path='Judicial')
julia = Documents(path='Julia')
backups = Documents(path='Backups iPhone')
personales = Documents(path='Personales')
viejos = Documents(path='Personales - Viejos')
salud = Documents(path='Salud')
test = Documents(path='Judicial/Justicia Gratuita - Viejos', tmp=True)


# judicial.download()
# julia.download()
backups.download()
personales.download()
# viejos.download()
# salud.download()
