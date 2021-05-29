from __future__ import annotations

import datetime
import logging
from pathlib import Path
from typing import List, Set

import attr
from tabulate import tabulate

from gpy.cli.report_uploaded import fetch_uploaded_media_info_between_dates
from gpy.cli.scan import scan_date
from gpy.config import (
    AGGREGATED_MEDIA_INFO_DIR,
    DEFAULT_TZ,
    LOCAL_MEDIA_INFO_DIR,
    MEDIA_DIR,
    TABLE_AS_STRING_PATH,
    UPLOADED_MEDIA_INFO_DIR,
    USE_LAST_REPORT_ON_REFRESH,
)
from gpy.exiftool import client as exiftool_client
from gpy.filenames import build_file_id
from gpy.filenames import parse_datetime as datetime_parser
from gpy.filesystem import read_reports, save_table, write_json, write_reports
from gpy.google_sheet import FileId, FileReport
from gpy.gphotos import MediaItem, read_media_items
from gpy.log import get_log_format, get_logs_output_path
from gpy.types import FileDateReport, unstructure

logger = logging.getLogger(__name__)

IsUploaded = bool


def read_uploaded_media_report(path: Path) -> List[MediaItem]:
    items = read_media_items(path)
    return items


def get_uploaded_file_ids(media_items: List[MediaItem]) -> Set[FileId]:
    file_ids: Set[FileId] = set()

    for media_item in media_items:
        file_id = build_file_id(
            file_name=media_item.filename,
            timestamp=media_item.media_metadata.creation_time,
        )

        if file_id in file_ids:
            logger.error(f"{file_id!r} file ID is duplicated, find a better key")
            breakpoint()

        file_ids.add(file_id)

    return file_ids


def get_updated_state(
    local_files: List[FileDateReport],
) -> List[FileReport]:
    # NOTE: simply mapping between FileDateReport to FileReport
    file_report = []
    for date_report in local_files:
        timestamp = date_report.metadata_date or date_report.filename_date
        file_id = build_file_id(date_report.path.name, timestamp)

        row = FileReport(
            file_id=file_id,
            path=date_report.path,
            filename_date=date_report.filename_date,
            metadata_date=date_report.metadata_date,
            dates_match=date_report.dates_match,
            gphotos_compatible_metadata=date_report.google_date,
            ready_to_upload=date_report.is_ready_to_upload,
            uploaded=False,
            add_google_timestamp=False,
            convert_to_mp4=False,
            upload_in_next_reconcile=False,
        )
        file_report.append(row)

    return file_report


@attr.s(auto_attribs=True, frozen=True)
class LocalMediaReportPath:
    path: Path
    created_on: datetime.datetime

    @classmethod
    def from_path(cls, path: Path) -> LocalMediaReportPath:
        _, timestamp_as_str = path.stem.split("__")

        created_on = datetime.datetime.fromisoformat(timestamp_as_str)

        return cls(path=path, created_on=created_on)


def get_last_local_report_path() -> Path:
    json_paths = LOCAL_MEDIA_INFO_DIR.glob("*.json")
    parsed_paths = map(LocalMediaReportPath.from_path, json_paths)

    most_recent_report: LocalMediaReportPath = next(parsed_paths)
    for report in parsed_paths:
        if most_recent_report.created_on < report.created_on:
            most_recent_report = report

    return most_recent_report.path


def build_local_file_report_path() -> Path:
    now = datetime.datetime.now().isoformat()
    return LOCAL_MEDIA_INFO_DIR / f"local_media_date_info__{now}.json"


def build_local_file_report() -> Path:
    # Equivalent to:
    # python -m gpy --debug scan date --report foo.json to_backup_in_gphotos
    logger.info(f"Scanning file datetimes in {MEDIA_DIR}")
    reports = scan_date(exiftool_client, datetime_parser, MEDIA_DIR)
    logger.info("Scan completed")

    # Do not add tz
    # GSheet should show what you have locally, with or without timezone
    # When you reconcile, you can add the right timezone
    # logger.info("Adding timezone data if required")
    # reports_with_tz = list(map(add_timezone, reports))

    report_path = build_local_file_report_path()
    write_reports(path=report_path, reports=reports)
    return report_path


def build_file_report_path() -> Path:
    now = datetime.datetime.now().isoformat()
    return AGGREGATED_MEDIA_INFO_DIR / f"local_media_info__{now}.json"


def save_file_aggregated_reports(reports: List[FileReport]) -> None:
    path = build_file_report_path()
    data = unstructure(reports)

    logger.info(f"Storing file aggregated reports at {path}")
    write_json(path=path, content=data)

    return path


TableAsStr = str


def convert_to_local_plain_text_spreadsheet(reports: List[FileReport]) -> TableAsStr:
    # >>> print(tabulate([["Name","Age"],["Alice",24],["Bob",19]],
    # ...                headers="firstrow"))
    headers = FileReport.table_headers()
    body_data = [report.to_tabular() for report in reports]
    tabular_data = [headers, *body_data]
    table_as_str = tabulate(tabular_data=tabular_data, headers="firstrow")
    return table_as_str


def refresh_google_spreadsheet_to_latest_state() -> None:
    if USE_LAST_REPORT_ON_REFRESH:
        local_files_report_path = get_last_local_report_path()
    else:
        local_files_report_path = build_local_file_report()
    current_local_files = read_reports(local_files_report_path)

    # rebuild new GSheet state
    file_aggregated_reports = get_updated_state(current_local_files)

    # store new GSheet state localy with timestamp
    save_file_aggregated_reports(file_aggregated_reports)

    # Pushing new state to local table
    table_as_str = convert_to_local_plain_text_spreadsheet(file_aggregated_reports)
    logger.info(f"Refreshing table at {TABLE_AS_STRING_PATH}")
    save_table(path=TABLE_AS_STRING_PATH, data=table_as_str)


if __name__ == "__main__":
    logger = logging.getLogger(__name__)

    logs_path = get_logs_output_path()
    log_format = get_log_format()
    logging.basicConfig(filename=logs_path, format=log_format, level=logging.DEBUG)

    logger.info("Refreshing Google Spreadsheet to show latest state")
    refresh_google_spreadsheet_to_latest_state()
    logger.info("Finished refreshing Google Spreadsheet to show latest state")
