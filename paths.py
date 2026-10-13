"""Strict local path hardening; not an OS sandbox or a TOCTOU guarantee."""
import os
from pathlib import Path

def checked_path(value, *, must_exist=False, directory=None):
    path=Path(value).expanduser()
    if not path.is_absolute() or '..' in path.parts:
        raise ValueError('Explicit absolute path without parent traversal required')
    for entry in [path,*path.parents]:
        if entry.is_symlink() or (hasattr(entry,'is_junction') and entry.is_junction()):
            raise ValueError('Symlink/junction ancestor refused')
        try:
            info=entry.lstat()
        except FileNotFoundError:
            continue
        if os.name=='nt' and getattr(info,'st_file_attributes',0)&0x400:
            raise ValueError('Windows reparse ancestor refused')
    if must_exist and not path.exists():
        raise ValueError('Required local path does not exist')
    if path.exists() and directory is True and not path.is_dir():
        raise ValueError('Expected directory')
    if path.exists() and directory is False and not path.is_file():
        raise ValueError('Expected regular file')
    return path.resolve(strict=must_exist)
