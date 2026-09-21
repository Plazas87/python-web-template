from pathlib import Path

from {{ package_name }}.domain.ports.services import FileStorageService


class LocalDiskFileStorageService(FileStorageService):
    # Default dev adapter — writes to a local directory and returns a file:// URL.
    # For production, implement FileStorageService against an S3-compatible bucket
    # (AWS S3, Cloudflare R2, Backblaze B2 — one implementation covers all of them)
    # and wire it in container.py instead; nothing else in the app changes.
    def __init__(self, base_dir: Path):
        self._base_dir = base_dir
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, key: str, content: bytes) -> None:
        path = self._path_for(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def get_url(self, key: str) -> str:
        return self._path_for(key).as_uri()

    def delete(self, key: str) -> None:
        self._path_for(key).unlink(missing_ok=True)

    def _path_for(self, key: str) -> Path:
        path = (self._base_dir / key).resolve()
        if self._base_dir.resolve() not in path.parents and path != self._base_dir.resolve():
            raise ValueError(f"Invalid file key: {key}")
        return path
