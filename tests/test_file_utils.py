import asyncio
from io import BytesIO
from pathlib import Path

import pytest
from fastapi import UploadFile

from app.utils.file_utils import UploadTooLargeError, save_upload_file


def test_save_upload_file_accepts_file_at_size_limit(tmp_path: Path) -> None:
    content = b"12345"
    upload = UploadFile(filename="support.txt", file=BytesIO(content))

    saved_path = asyncio.run(save_upload_file(upload, tmp_path, len(content)))

    assert saved_path.read_bytes() == content


def test_save_upload_file_removes_partial_oversized_file(
    tmp_path: Path,
) -> None:
    upload = UploadFile(filename="support.txt", file=BytesIO(b"123456"))

    with pytest.raises(
        UploadTooLargeError,
        match="Document exceeds maximum upload size of 5 bytes",
    ):
        asyncio.run(save_upload_file(upload, tmp_path, 5))

    assert not (tmp_path / "support.txt").exists()
