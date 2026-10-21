from dataclasses import dataclass, field
from enum import IntEnum
from typing import Callable, Optional


class Status(IntEnum):
    OK = 0
    INFO = 1
    WARN = 2
    FAIL = 3


@dataclass
class Fix:
    label: str
    run: Callable[[], str]  # returns a human-readable result message
    command: Optional[str] = None  # shown to the user so nothing is hidden


@dataclass
class Result:
    id: str
    title: str
    status: Status
    detail: str = ""
    fix: Optional[Fix] = None
    hint: str = ""  # manual remedy when no safe auto-fix exists


@dataclass
class Game:
    appid: str
    name: str
    library: str  # path to the steam library root
    installdir: str = ""
    size_on_disk: int = 0
    state_flags: int = 0
    is_tool: bool = False  # Proton / Steam Linux Runtime / Steamworks etc.

    @property
    def prefix(self):
        return f"{self.library}/steamapps/compatdata/{self.appid}"

    @property
    def install_path(self):
        return f"{self.library}/steamapps/common/{self.installdir}"
