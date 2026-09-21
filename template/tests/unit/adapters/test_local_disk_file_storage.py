from pathlib import Path

import pytest

from {{ package_name }}.adapters.outbound.external.local_disk_file_storage import (
    LocalDiskFileStorageService,
)


def test_save_then_get_url_and_read_back(tmp_path: Path) -> None:
    storage = LocalDiskFileStorageService(tmp_path)

    storage.save("avatars/jane.png", b"fake-image-bytes")

    assert (tmp_path / "avatars" / "jane.png").read_bytes() == b"fake-image-bytes"
    assert storage.get_url("avatars/jane.png") == (tmp_path / "avatars" / "jane.png").as_uri()


def test_delete_removes_file(tmp_path: Path) -> None:
    storage = LocalDiskFileStorageService(tmp_path)
    storage.save("doc.txt", b"content")

    storage.delete("doc.txt")

    assert not (tmp_path / "doc.txt").exists()


def test_delete_missing_file_is_a_no_op(tmp_path: Path) -> None:
    storage = LocalDiskFileStorageService(tmp_path)
    storage.delete("never-existed.txt")


def test_rejects_path_traversal_key(tmp_path: Path) -> None:
    storage = LocalDiskFileStorageService(tmp_path)

    with pytest.raises(ValueError):
        storage.save("../outside.txt", b"nope")
