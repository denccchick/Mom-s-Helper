import os
import json
import uuid
import time
import platform
from pathlib import Path
from dotenv import load_dotenv
from typing import Generator, Optional, Dict, Any, List, Callable

load_dotenv()

lock_timeout = 5
lock_retry_delay = 0.1
db_path = os.getenv("db_path", "./data/database")

system = platform.system().lower()


class WindowsFileLock:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.lock_file_path = file_path.with_suffix('.lock')
        self.file_handle = None

    def __enter__(self):
        import msvcrt

        start_time = time.time()

        while True:
            try:
                if not self.lock_file_path.exists():
                    self.file_handle = open(self.lock_file_path, 'w')
                    self.file_handle.close()

                self.file_handle = open(self.lock_file_path, 'r+b')
                msvcrt.locking(self.file_handle.fileno(), msvcrt.LK_NBLCK, 1)
                return self

            except (IOError, OSError):
                if self.file_handle:
                    self.file_handle.close()
                    self.file_handle = None

                if time.time() - start_time > lock_timeout:
                    raise TimeoutError(f"Could not acquire lock for {self.file_path}")

                time.sleep(lock_retry_delay)

    def __exit__(self, exc_type, exc_val, exc_tb):
        import msvcrt

        if self.file_handle:
            try:
                msvcrt.locking(self.file_handle.fileno(), msvcrt.LK_UNLCK, 1)
            except:
                pass

            self.file_handle.close()

            retry_count = 0
            while retry_count < 10:
                try:
                    self.lock_file_path.unlink()
                    break
                except (PermissionError, OSError):
                    retry_count += 1
                    time.sleep(0.05)


class UnixFileLock:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.lock_file_path = file_path.with_suffix('.lock')
        self.lock_fd = None

    def __enter__(self):
        import fcntl

        start_time = time.time()

        while True:
            try:
                self.lock_fd = open(self.lock_file_path, 'w')
                fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self

            except (IOError, OSError):
                if self.lock_fd:
                    self.lock_fd.close()
                    self.lock_fd = None

                if time.time() - start_time > lock_timeout:
                    raise TimeoutError(f"Could not acquire lock for {self.file_path}")

                time.sleep(lock_retry_delay)

    def __exit__(self, exc_type, exc_val, exc_tb):
        import fcntl

        if self.lock_fd:
            fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
            self.lock_fd.close()

            try:
                self.lock_file_path.unlink()
            except FileNotFoundError:
                pass


def FileLock(file_path: Path):
    if system == 'windows':
        return WindowsFileLock(file_path)
    else:
        return UnixFileLock(file_path)


class JSONDatabase:
    def __init__(self, db_path: str):
        self.base_path = Path(db_path) / "tables"
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, collection: str) -> Path:
        return self.base_path / f"{collection}.json"

    def _read(self, collection: str) -> List[Dict[str, Any]]:
        file_path = self._get_file_path(collection)

        if not file_path.exists():
            return []

        retry_count = 0
        max_retries = 5

        while retry_count < max_retries:
            try:
                with FileLock(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()

                        if not content:
                            return []

                        return json.loads(content)

            except (json.JSONDecodeError, FileNotFoundError):
                return []

            except PermissionError:
                retry_count += 1
                time.sleep(0.1)

        return []

    def _write(self, collection: str, data: List[Dict[str, Any]]) -> None:
        file_path = self._get_file_path(collection)
        temp_path = file_path.with_suffix('.tmp')

        retry_count = 0
        max_retries = 5

        while retry_count < max_retries:
            try:
                with FileLock(file_path):
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                        f.flush()

                        if system != 'windows':
                            os.fsync(f.fileno())

                    temp_path.replace(file_path)
                    return

            except PermissionError:
                retry_count += 1
                time.sleep(0.1)

            finally:
                try:
                    temp_path.unlink()
                except FileNotFoundError:
                    pass

    def insert(self, collection: str, document: Dict[str, Any]) -> Dict[str, Any]:
        data = self._read(collection)

        if "id" not in document:
            document["id"] = str(uuid.uuid4())

        data.append(document)
        self._write(collection, data)

        return document

    def find(self, collection: str, filter_func: Optional[Callable] = None) -> List[Dict[str, Any]]:
        data = self._read(collection)

        if filter_func:
            return [doc for doc in data if filter_func(doc)]

        return data

    def find_one(self, collection: str, filter_func: Callable) -> Optional[Dict[str, Any]]:
        data = self._read(collection)

        for doc in data:
            if filter_func(doc):
                return doc

        return None

    def update(self, collection: str, filter_func: Callable, update_func: Callable) -> int:
        data = self._read(collection)
        updated = 0

        for doc in data:
            if filter_func(doc):
                update_func(doc)
                updated += 1

        if updated > 0:
            self._write(collection, data)

        return updated

    def delete(self, collection: str, filter_func: Callable) -> int:
        data = self._read(collection)
        new_data = [doc for doc in data if not filter_func(doc)]
        deleted = len(data) - len(new_data)

        if deleted > 0:
            self._write(collection, new_data)

        return deleted

    def count(self, collection: str, filter_func: Optional[Callable] = None) -> int:
        data = self._read(collection)

        if filter_func:
            return len([doc for doc in data if filter_func(doc)])

        return len(data)


_db_instance = None


def create_engine_instance():
    global _db_instance

    if _db_instance is None:
        _db_instance = JSONDatabase(db_path)

    return _db_instance


def create_session_local():
    return create_engine_instance()


def get_db() -> Generator[JSONDatabase, None, None]:
    db = create_engine_instance()

    try:
        yield db
    finally:
        pass
