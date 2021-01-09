from pathlib import Path
from typing import Any  # TODO: find namespace type

import click

from gpy.exiftool import client as exiftool_client
from gpy.filenames import parse_datetime
from gpy.filesystem import get_paths_recursive
from gpy.log import log, print_report
from gpy.types import Report


@click.group(name="scan")
def scan_group() -> None:
    """Scan file and directory metadata."""
    pass


@scan_group.command(name="date")
@click.argument("path", type=click.Path(exists=True))
def scan_date_command(path):
    """Scan files and directories.

    Scan files and directories looking and report:
     - Supported files: the metadata of these files can be manipulated.
     - Date tag: the supported file does/doesn't have date tag.
     - GPS tag: the supported file does/doesn't have GPS tag.
    """
    file_paths = get_paths_recursive(root_path=Path(path))
    for file_path in file_paths:
        report = scan_date(exiftool_client, file_path)
        print_report(report)


def scan_date(exiftool: Any, path: Path) -> Report:
    """Scan file date and time metadata."""
    log(f"scanning {path}", fg="bright_black")

    filename_date = parse_datetime(path.name)
    metadata_date = exiftool.read_datetime(path)

    return Report(
        path=path,
        filename_date=filename_date,
        metadata_date=metadata_date,
    )


def scan_gps(exiftool: Any, file_path: Path) -> Report:
    """Scan file geolocation related metadata."""
    log(f"scanning {file_path}", fg="bright_black")
    gps = exiftool.read_gps(file_path)
    return Report(path=file_path, gps=gps)
