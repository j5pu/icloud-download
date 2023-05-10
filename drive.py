#!/usr/bin/env python3
# coding=utf-8
"""
Icloud-download Judicial Module
"""
import asyncio
import random
from asyncio import to_thread
from typing import Union

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

DEST = {True: "/tmp", False: "/Volumes/USB-2TB/iCloud"}
Node = NamedTuple("Node", dest=Path, src=DriveNode)
ASYNC: bool = True
DRY: bool = False


@dataclass
class Drive:
    path: InitVar[Union[Path, str]] = None
    """Path relative to Documents (default: None to download all in Drive)"""
    dry: bool = False
    tmp: bool = False
    dest: Path = field(default=None, init=False)
    """Local download dest absolute path"""
    src: DriveNode = field(default=None, init=False)
    """iCloud Documents src DriveNode instance"""
    node: Node = field(default=None, init=False)
    """Intermediate node to download"""
    jobs: list = field(default_factory=list, init=False)

    def __post_init__(self, path: str = None):
        self.dest = Path(DEST[self.tmp])
        self.src = api.drive

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

    async def _download(self):
        await to_thread(self.download)

    @property
    def downloadit(self):
        if self.is_file() and (not self.node.dest.exists() or self.size != self.size_dest):
            global jobs
            jobs.append(Drive(dry=self.dry, path=self.node.dest.relative_to(Path(DEST[self.tmp]))))
            return True

    def download(self, sync: bool = True):
        try:
            if self.is_dir():
                self.mkdir()
                node = self.node
                for children in node.src.get_children():
                    self.node = Node(node.dest / children.name, children)
                    self.download(sync=sync)
            elif self.downloadit:
                self.mkdir(file=True)
                if sync:
                    if self.node.dest.exists():
                        logger.warning(f"{self.node.src} [removed] {self.node.dest}")
                        if not self.dry:
                            self.node.dest.unlink()
                    logger.debug(f"{self.node.src} [started] {self.node.dest}")

                    if not self.dry:
                        if self.node.dest.exists():
                            self.node.dest.unlink()
                        with self.node.src.open(stream=True) as response:
                            with open(self.node.dest, 'wb') as file_out:
                                copyfileobj(response.raw, file_out)
                    logger.success(f"{self.node.src} [completed] {self.node.dest}")

        except OSError as oserr:
            if oserr.errno == errno.ENAMETOOLONG:
                logger.warning(f"{self.node.src} [name too long] {self.node.dest}")
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
                    print(f"- Directory: {directory}")
                    return
                directory.mkdir(parents=True, exist_ok=True)

    async def run(self):
        self.download(sync=False)
        tasks = [asyncio.create_task(getattr(item, "_download")(), name=str(item.node.src)) for item in jobs]
        # await asyncio.gather(*(getattr(item, "_download")() for item in jobs))
        await asyncio.gather(*tasks)

    @property
    def size(self):
        return self.node.src.size

    @property
    def size_dest(self):
        return self.node.dest.stat().st_size if self.node.dest.exists() else 0

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


jobs: list[Drive] = list()

Compressed = Drive(dry=DRY, path='Compressed')
if ASYNC:
    asyncio.run(Compressed.run())
else:
    Compressed.download()
