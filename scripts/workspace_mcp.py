#!/usr/bin/env python3
import argparse
import json
import os
import sys
import tomllib
from pathlib import Path

CATALOG = {
    "gmail": [
        "search_gmail_messages",
        "get_gmail_message_content",
        "get_gmail_messages_content_batch",
        "get_gmail_thread_content",
        "get_gmail_threads_content_batch",
        "get_gmail_attachment_content",
        "draft_gmail_message",
        "list_gmail_labels",
        "manage_gmail_label",
        "modify_gmail_message_labels",
        "batch_modify_gmail_message_labels",
        "list_gmail_filters",
    ],
    "drive": [
        "search_drive_files",
        "list_drive_items",
        "get_drive_file_content",
        "get_drive_file_download_url",
        "get_drive_file_permissions",
        "get_drive_shareable_link",
        "check_drive_file_public_access",
        "create_drive_file",
        "create_drive_folder",
        "copy_drive_file",
        "move_drive_file",
        "update_drive_file",
        "export_drive_file",
        "trash_drive_file",
        "delete_drive_file",
        "list_revisions",
        "get_revision",
    ],
    "docs": [
        "get_doc_content",
        "search_docs",
        "list_docs_in_folder",
        "create_doc",
        "modify_doc_text",
        "find_and_replace_doc",
        "export_doc_to_pdf",
        "batch_update_doc",
        "inspect_doc_structure",
        "insert_table",
        "create_table_with_data",
        "debug_table_structure",
        "manage_table_structure",
        "insert_list",
        "insert_doc_image",
        "insert_page_break",
        "insert_section_break",
        "insert_footnote",
        "update_doc_headers_footers",
        "update_document_style",
        "update_paragraph_style",
        "manage_named_range",
        "read_document_comments",
        "create_document_comment",
        "reply_to_document_comment",
        "resolve_document_comment",
        "edit_document_comment",
        "delete_document_comment",
        "edit_document_comment_reply",
        "delete_document_comment_reply",
    ],
    "sheets": [
        "create_spreadsheet",
        "list_spreadsheets",
        "get_spreadsheet_info",
        "get_sheet_cells",
        "update_sheet_cells",
        "transform_sheet_cells",
        "read_sheet_values",
        "modify_sheet_values",
        "format_sheet_range",
        "batch_read_values",
        "find_replace_sheet",
        "sort_range",
        "set_data_validation",
        "add_conditional_formatting",
        "update_conditional_formatting",
        "delete_conditional_formatting",
        "create_sheet",
        "delete_sheet",
        "duplicate_sheet",
        "update_sheet_properties",
        "freeze_dimensions",
        "merge_cells",
        "insert_dimension",
        "delete_dimension",
        "auto_resize_dimensions",
        "manage_named_ranges",
        "manage_filter_view",
        "manage_protected_range",
        "update_borders",
        "read_spreadsheet_comments",
        "create_spreadsheet_comment",
        "reply_to_spreadsheet_comment",
        "resolve_spreadsheet_comment",
        "edit_spreadsheet_comment",
        "delete_spreadsheet_comment",
        "edit_spreadsheet_comment_reply",
        "delete_spreadsheet_comment_reply",
    ],
    "slides": [
        "create_presentation",
        "get_presentation",
        "get_page",
        "get_page_thumbnail",
        "batch_update_presentation",
        "read_presentation_comments",
        "create_presentation_comment",
        "reply_to_presentation_comment",
        "resolve_presentation_comment",
        "edit_presentation_comment",
        "delete_presentation_comment",
        "edit_presentation_comment_reply",
        "delete_presentation_comment_reply",
    ],
    "calendar": [
        "list_calendars",
        "get_events",
        "create_event",
        "modify_event",
        "delete_event",
    ],
    "forms": [
        "create_form",
        "get_form",
        "list_form_responses",
        "get_form_response",
        "set_publish_settings",
    ],
}

DEFAULT_CONFIG_PATH = Path.home() / ".codex" / "config.toml"


def hex_to_color(color: str) -> dict:
    value = color.strip()
    if value.startswith("#"):
        value = value[1:]
    if len(value) != 6:
        raise ValueError(f"Invalid hex color: {color}")
    return {
        "red": int(value[0:2], 16) / 255,
        "green": int(value[2:4], 16) / 255,
        "blue": int(value[4:6], 16) / 255,
    }


def parse_json_object(raw: str, label: str) -> dict:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON for {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must decode to an object.")
    return value


def coerce_scalar(raw: str):
    lowered = raw.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def parse_run(spec: str) -> dict:
    try:
        start_raw, end_raw, attrs_raw = spec.split(":", 2)
    except ValueError as exc:
        raise ValueError(
            "Run spec must look like START:END:key=value,key2=value"
        ) from exc

    run_format = {}
    for token in filter(None, (part.strip() for part in attrs_raw.split(","))):
        if "=" not in token:
            raise ValueError(f"Invalid run token '{token}'. Use key=value.")
        key, raw_value = token.split("=", 1)
        key = key.strip()
        raw_value = raw_value.strip()

        if key in {"foreground", "foregroundColor", "color"}:
            run_format["foregroundColor"] = hex_to_color(raw_value)
        elif key == "link":
            run_format["link"] = {"uri": raw_value}
        elif key in {"bold", "italic", "underline", "strikethrough"}:
            run_format[key] = str(raw_value).lower() == "true"
        elif key == "fontSize":
            run_format[key] = int(raw_value)
        else:
            run_format[key] = coerce_scalar(raw_value)

    return {
        "from": int(start_raw),
        "to": int(end_raw),
        "format": run_format,
    }


def validate_patch(patch: dict) -> None:
    if not isinstance(patch, dict):
        raise ValueError("Each patch must be an object.")
    if not patch.get("a1"):
        raise ValueError("Each patch must include 'a1'.")
    runs = patch.get("runs") or patch.get("text_runs") or []
    if runs and "text" not in patch and "value" not in patch and "formula" not in patch:
        raise ValueError("Patches with runs must include text/value/formula context.")
    last_start = -1
    for run in runs:
        start = run.get("from", run.get("start", run.get("startIndex")))
        if start is None:
            raise ValueError("Each run requires a start offset.")
        start_int = int(start)
        if start_int < last_start:
            raise ValueError("Runs must be sorted by start offset.")
        last_start = start_int


def load_workspace_modules(server_dir: str):
    if server_dir not in sys.path:
        sys.path.insert(0, server_dir)

    try:
        from auth.google_auth import _find_any_credentials
        from googleapiclient.discovery import build
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Google Workspace dependencies are unavailable in this Python environment. "
            "Run this command via the server environment, e.g. "
            f"uv run --directory {server_dir} python {Path(__file__).resolve()} ..."
        ) from exc

    return _find_any_credentials, build


def server_dir_from_config(config_path: Path) -> str | None:
    if not config_path.exists():
        return None

    data = tomllib.loads(config_path.read_text())
    server = (((data.get("mcp_servers") or {}).get("google-workspace")) or {})
    args = server.get("args") or []
    if not isinstance(args, list):
        return None

    for idx, token in enumerate(args):
        if token == "--directory" and idx + 1 < len(args):
            return str(args[idx + 1])
    return None


def resolve_server_dir(explicit: str | None) -> str:
    if explicit:
        return explicit

    env_value = os.getenv("GOOGLE_WORKSPACE_SERVER_DIR")
    if env_value:
        return env_value

    config_value = server_dir_from_config(DEFAULT_CONFIG_PATH)
    if config_value:
        return config_value

    raise RuntimeError(
        "Could not resolve the Google Workspace server directory. "
        "Provide --server-dir, set GOOGLE_WORKSPACE_SERVER_DIR, or configure "
        "mcp_servers.google-workspace in ~/.codex/config.toml."
    )


def get_sheets_service(server_dir: str):
    find_credentials, build = load_workspace_modules(server_dir)
    credentials = find_credentials()
    if not credentials:
        raise RuntimeError(
            "No Google Workspace credentials were found. Authenticate the server first."
        )
    return build("sheets", "v4", credentials=credentials)


def index_to_column(index: int) -> str:
    value = index + 1
    chars = []
    while value:
        value, remainder = divmod(value - 1, 26)
        chars.append(chr(ord("A") + remainder))
    return "".join(reversed(chars))


def format_a1(sheet_title: str, row_index: int, col_index: int) -> str:
    escaped = sheet_title.replace("'", "''")
    return f"'{escaped}'!{index_to_column(col_index)}{row_index + 1}"


def scalar_from_extended_value(value: dict | None):
    if not value:
        return None
    for key in ("stringValue", "numberValue", "boolValue", "formulaValue", "errorValue"):
        if key in value:
            return value[key]
    return None


def derive_segments(text: str, text_format_runs: list[dict]) -> list[dict]:
    if not text:
        return []
    if not text_format_runs:
        return [{"start": 0, "end": len(text), "text": text, "format": {}}]

    runs = sorted(text_format_runs, key=lambda run: int(run.get("startIndex", 0)))
    segments = []
    cursor = 0

    for idx, run in enumerate(runs):
        start = int(run.get("startIndex", 0))
        if start > cursor:
            segments.append(
                {
                    "start": cursor,
                    "end": start,
                    "text": text[cursor:start],
                    "format": {},
                }
            )

        end = int(runs[idx + 1].get("startIndex", len(text))) if idx + 1 < len(runs) else len(text)
        segments.append(
            {
                "start": start,
                "end": end,
                "text": text[start:end],
                "format": run.get("format", {}),
            }
        )
        cursor = end

    if cursor < len(text):
        segments.append(
            {
                "start": cursor,
                "end": len(text),
                "text": text[cursor:],
                "format": {},
            }
        )

    return segments


def cell_has_payload(cell: dict) -> bool:
    for key in (
        "userEnteredValue",
        "formattedValue",
        "userEnteredFormat",
        "effectiveFormat",
        "textFormatRuns",
        "hyperlink",
        "note",
    ):
        if key in cell and cell.get(key) not in (None, "", [], {}):
            return True
    return False


def resolve_range_for_gid_and_row(service, file_id: str, gid: int | None, row: int | None, range_name: str | None) -> tuple[str, str]:
    metadata = (
        service.spreadsheets()
        .get(
            spreadsheetId=file_id,
            fields="sheets(properties(sheetId,title))",
        )
        .execute()
    )
    sheets = metadata.get("sheets", []) or []
    if gid is None:
        if not range_name:
            raise ValueError("Provide either --range or --gid.")
        return range_name, ""

    for sheet in sheets:
        props = sheet.get("properties", {})
        if int(props.get("sheetId", -1)) == gid:
            title = props.get("title", "")
            if range_name:
                return range_name, title
            if row is not None:
                escaped = title.replace("'", "''")
                return f"'{escaped}'!{row}:{row}", title
            raise ValueError("When using --gid without --range, provide --row.")
    raise ValueError(f"No sheet found for gid {gid}.")


def cmd_build_read(args: argparse.Namespace) -> int:
    payload = {
        "file_id": args.file_id,
        "range_name": args.range_name,
        "facets": args.facet or ["value", "formatted_value", "format", "text_runs"],
    }
    if args.include_empty:
        payload["include_empty"] = True
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


def cmd_catalog(_: argparse.Namespace) -> int:
    print(json.dumps(CATALOG, ensure_ascii=True, indent=2))
    return 0


def cmd_service_summary(args: argparse.Namespace) -> int:
    service = args.service
    payload = {
        "service": service,
        "tool_count": len(CATALOG[service]),
        "tools": CATALOG[service],
    }
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


def cmd_build_patch(args: argparse.Namespace) -> int:
    patch = {"a1": args.a1}
    if args.text is not None:
        patch["text"] = args.text
    if args.note is not None:
        patch["note"] = args.note
    if args.base_format is not None:
        patch["base_format"] = parse_json_object(args.base_format, "base_format")
    if args.run:
        patch["runs"] = [parse_run(spec) for spec in args.run]
    validate_patch(patch)
    print(json.dumps([patch], ensure_ascii=True, indent=2))
    return 0


def cmd_validate_patches(args: argparse.Namespace) -> int:
    payload = json.loads(Path(args.path).read_text())
    if not isinstance(payload, list):
        raise ValueError("Patch file must contain a JSON list.")
    for patch in payload:
        validate_patch(patch)
    print(json.dumps({"valid": True, "patches": len(payload)}, ensure_ascii=True))
    return 0


def parse_a1_cell(a1: str) -> tuple[str, int, int]:
    if "!" not in a1:
        raise ValueError("Cell target must include a sheet title, e.g. 'Sheet 1'!B2")
    sheet_part, cell_part = a1.split("!", 1)
    sheet_title = sheet_part.strip().strip("'").replace("''", "'")
    idx = 0
    while idx < len(cell_part) and cell_part[idx].isalpha():
        idx += 1
    if idx == 0 or idx == len(cell_part):
        raise ValueError(f"Invalid single-cell A1 reference: {a1}")
    col_letters = cell_part[:idx].upper()
    row_number = int(cell_part[idx:])
    col_index = 0
    for char in col_letters:
        col_index = col_index * 26 + (ord(char) - ord("A") + 1)
    return sheet_title, row_number - 1, col_index - 1


def normalize_patch_to_cell_data(patch: dict) -> tuple[str, dict, str]:
    validate_patch(patch)
    a1 = patch["a1"]
    cell = {}
    if "text" in patch:
        cell["userEnteredValue"] = {"stringValue": str(patch["text"])}
    elif "formula" in patch:
        cell["userEnteredValue"] = {"formulaValue": str(patch["formula"])}
    elif "value" in patch:
        value = patch["value"]
        if isinstance(value, bool):
            cell["userEnteredValue"] = {"boolValue": value}
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            cell["userEnteredValue"] = {"numberValue": value}
        else:
            cell["userEnteredValue"] = {"stringValue": str(value)}

    if "base_format" in patch:
        cell["userEnteredFormat"] = patch["base_format"]
    if "note" in patch:
        cell["note"] = patch["note"]

    if patch.get("clear_runs"):
        cell["textFormatRuns"] = []
    elif patch.get("runs") or patch.get("text_runs"):
        runs = patch.get("runs") or patch.get("text_runs") or []
        normalized_runs = []
        for run in runs:
            start = run.get("from", run.get("start", run.get("startIndex")))
            if start is None:
                raise ValueError("Each run requires a start offset.")
            normalized_runs.append(
                {
                    "startIndex": int(start),
                    "format": run.get("format", {}),
                }
            )
        normalized_runs.sort(key=lambda item: item["startIndex"])
        cell["textFormatRuns"] = normalized_runs

    field_order = [
        "userEnteredValue",
        "userEnteredFormat",
        "textFormatRuns",
        "note",
    ]
    field_mask = ",".join(field for field in field_order if field in cell)
    if not field_mask:
        raise ValueError("Patch does not contain any writable fields.")
    return a1, cell, field_mask


def cmd_sheets_apply_patches(args: argparse.Namespace) -> int:
    server_dir = resolve_server_dir(args.server_dir)
    service = get_sheets_service(server_dir)

    if args.path:
        patches = json.loads(Path(args.path).read_text())
    else:
        if not args.inline:
            raise ValueError("Provide either --path or --inline.")
        patches = json.loads(args.inline)

    if not isinstance(patches, list) or not patches:
        raise ValueError("Patches must be a non-empty JSON list.")

    metadata = (
        service.spreadsheets()
        .get(
            spreadsheetId=args.file_id,
            fields="sheets(properties(sheetId,title))",
        )
        .execute()
    )
    sheets = metadata.get("sheets", []) or []
    sheet_ids = {
        sheet.get("properties", {}).get("title"): sheet.get("properties", {}).get("sheetId")
        for sheet in sheets
    }

    requests = []
    touched = []
    for patch in patches:
        a1, cell, field_mask = normalize_patch_to_cell_data(patch)
        sheet_title, row_index, col_index = parse_a1_cell(a1)
        sheet_id = sheet_ids.get(sheet_title)
        if sheet_id is None:
            raise ValueError(f"Sheet '{sheet_title}' not found in spreadsheet.")
        requests.append(
            {
                "updateCells": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": row_index,
                        "endRowIndex": row_index + 1,
                        "startColumnIndex": col_index,
                        "endColumnIndex": col_index + 1,
                    },
                    "rows": [{"values": [cell]}],
                    "fields": field_mask,
                }
            }
        )
        touched.append(a1)

    service.spreadsheets().batchUpdate(
        spreadsheetId=args.file_id,
        body={"requests": requests},
    ).execute()

    print(
        json.dumps(
            {"updated": len(touched), "cells": touched},
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


def cmd_sheets_inspect_range(args: argparse.Namespace) -> int:
    server_dir = resolve_server_dir(args.server_dir)
    service = get_sheets_service(server_dir)
    gid = int(args.gid) if args.gid is not None else None
    resolved_range, resolved_title = resolve_range_for_gid_and_row(
        service,
        args.file_id,
        gid,
        args.row,
        args.range_name,
    )

    response = (
        service.spreadsheets()
        .get(
            spreadsheetId=args.file_id,
            ranges=[resolved_range],
            includeGridData=True,
            fields=(
                "sheets(properties(title,sheetId),"
                "data(startRow,startColumn,rowData(values("
                "userEnteredValue,formattedValue,userEnteredFormat,effectiveFormat,"
                "textFormatRuns,hyperlink,note))))"
            ),
        )
        .execute()
    )

    payload = {
        "spreadsheetId": args.file_id,
        "requestedRange": resolved_range,
        "sheetTitle": resolved_title or None,
        "cells": [],
    }

    for sheet in response.get("sheets", []) or []:
        sheet_title = sheet.get("properties", {}).get("title") or resolved_title or "Unknown"
        for grid in sheet.get("data", []) or []:
            start_row = int(grid.get("startRow", 0) or 0)
            start_col = int(grid.get("startColumn", 0) or 0)
            for row_offset, row_data in enumerate(grid.get("rowData", []) or []):
                for col_offset, cell in enumerate(row_data.get("values", []) or []):
                    if not args.include_empty and not cell_has_payload(cell):
                        continue
                    text = (
                        ((cell.get("userEnteredValue") or {}).get("stringValue"))
                        or cell.get("formattedValue")
                        or ""
                    )
                    payload["cells"].append(
                        {
                            "a1": format_a1(sheet_title, start_row + row_offset, start_col + col_offset),
                            "value": scalar_from_extended_value(cell.get("userEnteredValue")),
                            "formattedValue": cell.get("formattedValue"),
                            "userEnteredFormat": cell.get("userEnteredFormat"),
                            "effectiveFormat": cell.get("effectiveFormat"),
                            "textFormatRuns": cell.get("textFormatRuns", []),
                            "segments": derive_segments(text, cell.get("textFormatRuns", [])),
                            "hyperlink": cell.get("hyperlink"),
                            "note": cell.get("note"),
                        }
                    )

    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Helpers for the Google Workspace skill."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    catalog_parser = subparsers.add_parser("catalog")
    catalog_parser.set_defaults(func=cmd_catalog)

    summary_parser = subparsers.add_parser("service-summary")
    summary_parser.add_argument("--service", required=True, choices=sorted(CATALOG))
    summary_parser.set_defaults(func=cmd_service_summary)

    read_parser = subparsers.add_parser("sheets-build-read")
    read_parser.add_argument("--file-id", required=True)
    read_parser.add_argument("--range", dest="range_name", required=True)
    read_parser.add_argument("--facet", action="append")
    read_parser.add_argument("--include-empty", action="store_true")
    read_parser.set_defaults(func=cmd_build_read)

    patch_parser = subparsers.add_parser("sheets-build-patch")
    patch_parser.add_argument("--a1", required=True)
    patch_parser.add_argument("--text")
    patch_parser.add_argument("--note")
    patch_parser.add_argument("--base-format")
    patch_parser.add_argument(
        "--run",
        action="append",
        help="Run spec START:END:key=value,key2=value. Example: 0:4:bold=true,foreground=#cc1a1a",
    )
    patch_parser.set_defaults(func=cmd_build_patch)

    validate_parser = subparsers.add_parser("sheets-validate-patches")
    validate_parser.add_argument("path")
    validate_parser.set_defaults(func=cmd_validate_patches)

    apply_parser = subparsers.add_parser("sheets-apply-patches")
    apply_parser.add_argument("--file-id", required=True)
    apply_parser.add_argument("--path")
    apply_parser.add_argument("--inline")
    apply_parser.add_argument("--server-dir")
    apply_parser.set_defaults(func=cmd_sheets_apply_patches)

    inspect_parser = subparsers.add_parser("sheets-inspect-range")
    inspect_parser.add_argument("--file-id", required=True)
    inspect_parser.add_argument("--range", dest="range_name")
    inspect_parser.add_argument("--gid")
    inspect_parser.add_argument("--row", type=int)
    inspect_parser.add_argument("--include-empty", action="store_true")
    inspect_parser.add_argument("--server-dir")
    inspect_parser.set_defaults(func=cmd_sheets_inspect_range)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
