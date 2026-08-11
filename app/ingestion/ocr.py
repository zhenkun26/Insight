from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


class OCRError(RuntimeError):
    error_code = "ocr_error"


class OCRUnavailableError(OCRError):
    error_code = "ocr_unavailable"


class OCRTimeoutError(OCRError):
    error_code = "ocr_timeout"


class OCRExecutionError(OCRError):
    error_code = "ocr_failed"


def runtime_status() -> dict[str, object]:
    missing = [name for name in ("pdftoppm", "tesseract") if shutil.which(name) is None]
    return {
        "status": "ready" if not missing else "unavailable",
        "missing": missing,
    }


def _tool_path(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise OCRUnavailableError(
            f"{name} is required for OCR; install Poppler and Tesseract or set OCR_ENABLED=false"
        )
    return path


def _run(
    command: list[str], timeout_seconds: float, label: str
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise OCRTimeoutError(f"{label} exceeded OCR_TIMEOUT_SECONDS") from exc
    except OSError as exc:
        raise OCRExecutionError(f"{label} could not start") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "command failed").strip()
        raise OCRExecutionError(f"{label} failed: {detail[:300]}")
    return result


def ocr_pdf_pages(
    data: bytes,
    page_numbers: list[int],
    *,
    language: str,
    timeout_seconds: float,
    temp_dir: str | None = None,
) -> dict[int, str]:
    """OCR selected 1-based PDF pages and return cleaned text by page number."""
    if not page_numbers:
        return {}
    pdftoppm = _tool_path("pdftoppm")
    tesseract = _tool_path("tesseract")
    try:
        with tempfile.TemporaryDirectory(prefix="insight-ocr-", dir=temp_dir) as work_dir:
            root = Path(work_dir)
            source = root / "source.pdf"
            source.write_bytes(data)
            texts: dict[int, str] = {}
            for page_number in page_numbers:
                prefix = root / f"page-{page_number}"
                _run(
                    [
                        pdftoppm,
                        "-png",
                        "-r",
                        "150",
                        "-f",
                        str(page_number),
                        "-l",
                        str(page_number),
                        str(source),
                        str(prefix),
                    ],
                    timeout_seconds,
                    f"PDF render page {page_number}",
                )
                images = sorted(root.glob(f"page-{page_number}-*.png"))
                if not images:
                    raise OCRExecutionError(f"PDF render produced no image for page {page_number}")
                image = images[0]
                try:
                    result = _run(
                        [tesseract, str(image), "stdout", "-l", language],
                        timeout_seconds,
                        f"OCR page {page_number}",
                    )
                    texts[page_number] = result.stdout.strip()
                finally:
                    image.unlink(missing_ok=True)
            return texts
    except OCRError:
        raise
    except OSError as exc:
        raise OCRExecutionError(f"OCR temporary workspace failed: {exc}") from exc
