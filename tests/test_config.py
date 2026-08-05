import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_max_upload_size_defaults_to_ten_megabytes() -> None:
    settings = Settings(_env_file=None)

    assert settings.max_upload_size_mb == 10
    assert settings.max_upload_size_bytes == 10 * 1024 * 1024


def test_max_upload_size_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        Settings(max_upload_size_mb=0, _env_file=None)
