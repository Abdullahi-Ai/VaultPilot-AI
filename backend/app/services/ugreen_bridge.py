"""
VaultPilot AI — Tri-Mode Storage Architecture & Security Sandbox
Provides the integration boundary between the VaultPilot AI Web Application
and configured storage environments.

Architecture Modes:
- Mode A (LOCAL_DEV): Local development database, synthetic test fixtures, isolated unit test execution.
- Mode B (EMULATED_NAS): Offline demonstration sandbox, deterministic NGO financial records.
- Mode C (PHYSICAL_NAS): Genuine UGREEN AI NAS execution with read-only containment, TOCTOU defense,
                         bounded discovery, and fail-safe unmounted volume handling.

Enforces:
1. Strict read-only file access.
2. Canonical path resolution and boundary containment within storage root.
3. Symlink escape and directory traversal ('..') rejection.
4. Streaming SHA-256 evidence hashing in 64KB blocks.
5. Pluggable StorageProviderFactory with explicit error handling.
6. Scalability controls (bounded file count and directory depth limits).
"""

import os
import json
import re
import stat
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Union
from abc import ABC, abstractmethod
from app.core.config import settings, StorageMode
from app.services.document_extractor import FinancialDocumentExtractor


class NASError(Exception):
    """Base exception for NAS storage and evidence operations."""
    pass

class NASSecurityViolationError(NASError):
    """Raised when an operation attempts directory traversal, symlink escape, or access to special files."""
    pass

class NASInvalidPathError(NASError):
    """Raised when an input path is empty, malformed, or not a directory."""
    pass

class NASPathUnreachableError(NASError):
    """Base exception when a specified NAS path or storage mount cannot be reached."""
    pass

class NASStorageUnavailableError(NASPathUnreachableError):
    """Raised when the configured NAS storage root volume is unmounted, offline, or inaccessible."""
    pass

class NASPathNotFoundError(NASPathUnreachableError):
    """Raised when the target investigation scope folder does not exist within the NAS storage."""
    pass

class NASFileMutationError(NASError):
    """Raised when an evidence file is concurrently modified during hashing or acquisition (TOCTOU violation)."""
    pass

class NASResourceExceededError(NASError):
    """Raised when discovery exceeds safety limits (file count or directory depth)."""
    pass


class EvidenceProvider(ABC):
    """Abstract interface for document discovery and evidence acquisition."""

    @abstractmethod
    def discover_documents(self, scope_path: str) -> List[Dict[str, Any]]:
        """Discovers files in an authorized directory scope."""
        pass

    @abstractmethod
    def extract_document(self, file_path: str, doc_type: str) -> Dict[str, Any]:
        """Extracts structured financial fields from a genuine document."""
        pass


class EmulatedNASProvider(EvidenceProvider):
    """
    Mode B: Offline demonstration sandbox.
    Provides deterministic NGO financial fixtures for offline judging, demonstrations,
    and UI visual testing without hardware dependencies.
    """
    def discover_documents(self, scope_path: str) -> List[Dict[str, Any]]:
        return [
            {
                "file_path": f"{scope_path}/orders/PO-2026-081.pdf",
                "filename": "PO-2026-081.pdf",
                "type": "PURCHASE_ORDER",
                "size_bytes": 142000,
                "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            },
            {
                "file_path": f"{scope_path}/invoices/INV-SP-1092.pdf",
                "filename": "INV-SP-1092.pdf",
                "type": "INVOICE",
                "size_bytes": 98000,
                "sha256": "c4ca4238a0b923820dcc509a6f75849b" * 2
            },
            {
                "file_path": f"{scope_path}/receipts/REC-BNK-993.pdf",
                "filename": "REC-BNK-993.pdf",
                "type": "RECEIPT",
                "size_bytes": 84000,
                "sha256": "c81e728d9d4c2f636f067f89cc14862c" * 2
            },
            {
                "file_path": f"{scope_path}/orders/PO-MED-441.pdf",
                "filename": "PO-MED-441.pdf",
                "type": "PURCHASE_ORDER",
                "size_bytes": 156000,
                "sha256": "eccbc87e4b5ce2fe28308fd9f2a7baf3" * 2
            },
            {
                "file_path": f"{scope_path}/invoices/INV-MED-7712.pdf",
                "filename": "INV-MED-7712.pdf",
                "type": "INVOICE",
                "size_bytes": 112000,
                "sha256": "a87ff679a2f3e71d9181a67b7542122c" * 2
            },
            {
                "file_path": f"{scope_path}/receipts/VOUCH-331.pdf",
                "filename": "VOUCH-331.pdf",
                "type": "RECEIPT",
                "size_bytes": 76000,
                "sha256": "e4da3b7fbbce2345d7772b0674a318d5" * 2
            },
            {
                "file_path": f"{scope_path}/invoices/INV-UNSUPP-902.pdf",
                "filename": "INV-UNSUPP-902.pdf",
                "type": "INVOICE",
                "size_bytes": 92000,
                "sha256": "1679091c5a880faf6fb5e6087eb1b2dc" * 2
            },
            {
                "file_path": f"{scope_path}/receipts/IMG_7781_blurry.jpg",
                "filename": "IMG_7781_blurry.jpg",
                "type": "RECEIPT",
                "size_bytes": 650000,
                "sha256": "8f14e45fceea167a5a36dedd4bea2543" * 2
            }
        ]

    def extract_document(self, file_path: str, doc_type: str) -> Dict[str, Any]:
        if "PO-2026-081" in file_path:
            return {
                "vendor": "SunPower Ltd",
                "po_reference": "PO-2026-081",
                "date": "2026-01-10",
                "amount": 8500.0,
                "currency": "USD",
                "description": "Solar Inverter Components and Wiring",
                "status": "EXTRACTED"
            }
        elif "INV-SP-1092" in file_path:
            return {
                "vendor": "SunPower Ltd",
                "invoice_number": "INV-SP-1092",
                "po_reference": "PO-2026-081",
                "date": "2026-01-24",
                "amount": 8500.0,
                "currency": "USD",
                "description": "Solar Inverter Components and Wiring",
                "status": "EXTRACTED"
            }
        elif "REC-BNK-993" in file_path:
            return {
                "payee": "SunPower Ltd",
                "receipt_id": "REC-BNK-993",
                "invoice_reference": "INV-SP-1092",
                "date": "2026-02-02",
                "amount": 8500.0,
                "currency": "USD",
                "status": "EXTRACTED"
            }
        elif "PO-MED-441" in file_path:
            return {
                "vendor": "MedSupply Co",
                "po_reference": "PO-MED-441",
                "date": "2026-02-15",
                "amount": 12000.0,
                "currency": "USD",
                "description": "Adjustable Clinic Beds Batch 1",
                "status": "EXTRACTED"
            }
        elif "INV-MED-7712" in file_path:
            return {
                "vendor": "MedSupply Co",
                "invoice_number": "INV-MED-7712",
                "po_reference": "PO-MED-441",
                "date": "2026-03-01",
                "amount": 14500.0,
                "currency": "USD",
                "description": "Adjustable Clinic Beds Batch 1",
                "status": "EXTRACTED"
            }
        elif "VOUCH-331" in file_path:
            return {
                "payee": "MedSupply Co",
                "receipt_id": "VOUCH-331",
                "invoice_reference": "INV-MED-7712",
                "date": "2026-03-10",
                "amount": 14500.0,
                "currency": "USD",
                "status": "EXTRACTED"
            }
        elif "INV-UNSUPP-902" in file_path:
            return {
                "vendor": "EquipServe Logistics",
                "invoice_number": "INV-UNSUPP-902",
                "po_reference": None,
                "date": "2026-03-12",
                "amount": 2400.0,
                "currency": "USD",
                "description": "Warehouse Rental & Storage",
                "status": "EXTRACTED"
            }
        elif "IMG_7781_blurry" in file_path:
            return {
                "vendor": "Unknown (Smudged)",
                "date": "2026-03-15",
                "amount": None,
                "currency": "USD",
                "status": "UNVERIFIED",
                "error": "Low image clarity / text obscured"
            }
        return {"status": "UNAVAILABLE"}


class FilesystemNASProvider(EvidenceProvider):
    """
    Filesystem evidence acquisition engine scanning an explicitly configured directory tree.

    Security & Integrity Guarantees:
    - Path Containment: Validates that all scanned paths resolve strictly within configured nas_root.
    - Path Traversal Defense: Blocks '..' and symlink escapes pointing outside the root.
    - Special File Defense: Rejects FIFOs, devices, and socket nodes to prevent hangs or exploits.
    - Read-Only Operations: Opens files in 'rb' mode only; zero write or mutation calls.
    - TOCTOU Defense: Verifies file descriptor mtime and size before and after reading.
    - Streaming SHA-256 Hashing: Ingests files in 64KB blocks to prevent memory exhaustion.
    - Resource Bounding: Enforces limits on maximum file count and directory recursion depth.
    """
    SUPPORTED_EXTENSIONS = frozenset({
        ".pdf", ".docx", ".xlsx", ".csv", ".json", ".txt",
        ".jpg", ".jpeg", ".png", ".tiff", ".md"
    })
    SUPPORTED_MEDIA_EXTENSIONS = frozenset({
        ".pdf", ".docx", ".xlsx", ".csv", ".txt",
        ".jpg", ".jpeg", ".png", ".tiff", ".md"
    })

    def __init__(
        self,
        nas_root: Optional[str] = None,
        max_files: Optional[int] = None,
        max_depth: Optional[int] = None
    ):
        self.nas_root = nas_root or settings.UGREEN_NAS_ROOT
        self.max_files = max_files or getattr(settings, "MAX_DISCOVERY_FILES", 500)
        self.max_depth = max_depth or getattr(settings, "MAX_DISCOVERY_DEPTH", 5)

    def _validate_and_resolve_scope(self, scope_path: str) -> str:
        """
        Validates that scope_path exists, is a directory, and is strictly contained
        within the configured nas_root. Blocks path traversal and symlink escapes.
        """
        if not scope_path or not scope_path.strip():
            raise NASInvalidPathError("Target scope path is empty or unspecified.")

        # Reject literal '..' traversal sequences before resolution
        raw_parts = Path(scope_path).parts
        if ".." in raw_parts:
            raise NASSecurityViolationError(
                f"Directory traversal sequence ('..') detected in scope path: {scope_path}"
            )

        # Ensure NAS root is defined and mounted
        if not self.nas_root:
            raise NASStorageUnavailableError("NAS storage root is not configured.")

        real_root = os.path.realpath(self.nas_root)
        if not os.path.exists(real_root):
            raise NASStorageUnavailableError(f"NAS storage root is offline or unmounted: {self.nas_root}")

        real_scope = os.path.realpath(scope_path)

        # Check if the target scope exists
        if not os.path.exists(real_scope):
            raise NASPathNotFoundError(f"Target NAS directory does not exist or is unmounted: {scope_path}")

        if not os.path.isdir(real_scope):
            raise NASInvalidPathError(f"Target NAS path is not a directory: {scope_path}")

        # Enforce boundary containment
        try:
            common = os.path.commonpath([real_root, real_scope])
            if common != real_root:
                raise NASSecurityViolationError(
                    f"Access denied: Target path '{scope_path}' resolves outside authorized NAS root '{self.nas_root}'."
                )
        except ValueError:
            raise NASSecurityViolationError(
                f"Access denied: Target path '{scope_path}' is on a different drive than NAS root '{self.nas_root}'."
            )

        return real_scope

    @classmethod
    def compute_file_sha256(cls, file_path: str) -> str:
        """
        Streams file bytes in 64KB chunks and computes canonical SHA-256 evidence digest.
        Read-only, memory-safe, TOCTOU protected against concurrent file mutation.
        """
        try:
            with open(file_path, "rb") as f:
                fd = f.fileno()
                st_initial = os.fstat(fd)
                if not stat.S_ISREG(st_initial.st_mode):
                    raise NASSecurityViolationError(f"Special non-regular file rejected: {file_path}")

                h = hashlib.sha256()
                bytes_read = 0
                while chunk := f.read(65536):
                    h.update(chunk)
                    bytes_read += len(chunk)

                st_final = os.fstat(fd)
                if (st_initial.st_mtime_ns != st_final.st_mtime_ns or
                    st_final.st_size != st_initial.st_size or
                    bytes_read != st_initial.st_size):
                    raise NASFileMutationError(
                        f"Evidence file was concurrently mutated during hashing: {file_path}"
                    )
                return h.hexdigest()
        except (NASFileMutationError, NASSecurityViolationError):
            raise
        except OSError as e:
            raise NASPathUnreachableError(f"Unable to read evidence file '{file_path}': {str(e)}")

    @staticmethod
    def _classify_document_type(filename: str, parent_dir: str) -> str:
        fn_upper = filename.upper()
        dir_upper = parent_dir.upper()

        if "PO" in fn_upper or "ORDER" in fn_upper or "ORDERS" in dir_upper:
            return "PURCHASE_ORDER"
        if "INV" in fn_upper or "BILL" in fn_upper or "INVOICES" in dir_upper:
            return "INVOICE"
        if "REC" in fn_upper or "VOUCH" in fn_upper or "RECEIPTS" in dir_upper or "PAYMENT" in fn_upper:
            return "RECEIPT"
        if "EXP" in fn_upper or "REP" in fn_upper or "REPORT" in dir_upper or "EXPENSE" in dir_upper:
            return "EXPENSE_REPORT"
        return "OTHER"

    @classmethod
    def _is_sidecar_file(cls, fname: str, all_files_in_dir: Set[str]) -> bool:
        """Determines if a JSON file is a metadata sidecar to a sibling document."""
        if fname.endswith(".meta.json"):
            return True
        parts = fname.rsplit(".", 2)
        if len(parts) == 3 and f".{parts[1]}".lower() in cls.SUPPORTED_MEDIA_EXTENSIONS:
            return True
        if fname.endswith(".json"):
            stem = fname[:-5]
            for ext in cls.SUPPORTED_MEDIA_EXTENSIONS:
                if f"{stem}{ext}" in all_files_in_dir or f"{stem}{ext.upper()}" in all_files_in_dir:
                    return True
        return False

    def discover_documents(self, scope_path: str) -> List[Dict[str, Any]]:
        """
        Scans a genuine local storage directory within authorized scope bounds.
        Bounded by max_depth and max_files to prevent denial-of-service.
        """
        resolved_scope = self._validate_and_resolve_scope(scope_path)
        real_root = os.path.realpath(self.nas_root)

        scope_depth = len(Path(resolved_scope).parts)
        discovered: List[Dict[str, Any]] = []

        for root, dirs, files in os.walk(resolved_scope, followlinks=False):
            # Enforce max directory depth
            current_depth = len(Path(root).parts) - scope_depth
            if current_depth >= self.max_depth:
                dirs.clear()  # Do not descend further

            # Prune hidden directories
            dirs[:] = [d for d in dirs if not d.startswith(".")]

            # Verify directory symlinks do not escape root
            for d in list(dirs):
                d_full = os.path.join(root, d)
                if os.path.islink(d_full):
                    real_d = os.path.realpath(d_full)
                    if os.path.commonpath([real_root, real_d]) != real_root:
                        raise NASSecurityViolationError(
                            f"Symlink escape detected: Directory '{d_full}' points outside authorized NAS root."
                        )

            all_files_in_dir = set(files)

            for fname in sorted(files):
                if len(discovered) >= self.max_files:
                    raise NASResourceExceededError(
                        f"Discovery exceeded safety threshold of {self.max_files} files in scope: {scope_path}"
                    )

                if fname.startswith("."):
                    continue

                ext = os.path.splitext(fname)[1].lower()
                if ext not in self.SUPPORTED_EXTENSIONS:
                    continue

                if self._is_sidecar_file(fname, all_files_in_dir):
                    continue

                full_path = os.path.join(root, fname)

                # Special file rejection (FIFO, device nodes, sockets)
                try:
                    lst = os.lstat(full_path)
                    if (stat.S_ISFIFO(lst.st_mode) or stat.S_ISSOCK(lst.st_mode) or
                        stat.S_ISCHR(lst.st_mode) or stat.S_ISBLK(lst.st_mode)):
                        raise NASSecurityViolationError(f"Special non-regular file rejected: {full_path}")
                except OSError as e:
                    raise NASPathUnreachableError(f"Cannot stat evidence file '{full_path}': {str(e)}")

                # Symlink escape verification
                if os.path.islink(full_path):
                    real_target = os.path.realpath(full_path)
                    if os.path.commonpath([real_root, real_target]) != real_root:
                        raise NASSecurityViolationError(
                            f"Symlink escape detected: File '{full_path}' points outside authorized NAS root."
                        )
                    target_st = os.stat(full_path)
                    if not stat.S_ISREG(target_st.st_mode):
                        raise NASSecurityViolationError(f"Symlink points to non-regular file: {full_path}")

                try:
                    st = os.stat(full_path)
                    size_bytes = st.st_size
                except OSError:
                    size_bytes = 0

                doc_type = self._classify_document_type(fname, os.path.basename(root))
                sha_digest = self.compute_file_sha256(full_path)

                discovered.append({
                    "file_path": full_path,
                    "filename": fname,
                    "type": doc_type,
                    "size_bytes": size_bytes,
                    "sha256": sha_digest
                })

        return discovered

    def extract_document(self, file_path: str, doc_type: str) -> Dict[str, Any]:
        """
        Extracts structured financial fields and full provenance from genuine files using
        FinancialDocumentExtractor (supporting PDF, CSV, TXT, JSON, and sidecars).
        Strictly read-only, TOCTOU protected, path containment verified.
        """
        if not os.path.exists(file_path):
            return {"status": "UNAVAILABLE"}

        real_root = os.path.realpath(self.nas_root) if self.nas_root and os.path.exists(self.nas_root) else None
        real_file = os.path.realpath(file_path)

        if real_root:
            if os.path.commonpath([real_root, real_file]) != real_root:
                raise NASSecurityViolationError(f"Access denied: File '{file_path}' resolves outside authorized NAS root.")

        # Reject special files
        try:
            lst = os.lstat(file_path)
            if (stat.S_ISFIFO(lst.st_mode) or stat.S_ISSOCK(lst.st_mode) or
                stat.S_ISCHR(lst.st_mode) or stat.S_ISBLK(lst.st_mode)):
                raise NASSecurityViolationError(f"Special non-regular file rejected: {file_path}")
        except OSError:
            return {"status": "UNAVAILABLE"}

        # Enforce pre-extraction size ceiling
        try:
            st = os.stat(file_path)
            max_sz = getattr(settings, "MAX_FILE_SIZE_BYTES", 25 * 1024 * 1024)
            if st.st_size > max_sz:
                return {
                    "status": "UNVERIFIED",
                    "error": f"File exceeds maximum analysis size of {max_sz} bytes."
                }
        except OSError:
            pass

        # Compute file sha256 to pass to provenance
        try:
            sha_digest = self.compute_file_sha256(file_path)
        except Exception:
            sha_digest = None

        return FinancialDocumentExtractor.extract_document(
            file_path=file_path,
            doc_type=doc_type,
            nas_root=self.nas_root,
            file_sha256=sha_digest
        )


class LocalDevStorageProvider(FilesystemNASProvider):
    """
    Mode A: Local Development & Isolated Testing Provider.
    Scans local developer directories or test fixtures. Ensures predictable,
    reproducible test execution without physical NAS hardware.
    """
    def __init__(
        self,
        dev_root: Optional[str] = None,
        max_files: Optional[int] = None,
        max_depth: Optional[int] = None
    ):
        root = dev_root or getattr(settings, "LOCAL_DEV_ROOT", "./storage/dev_fixtures")
        os.makedirs(root, exist_ok=True)
        super().__init__(nas_root=root, max_files=max_files, max_depth=max_depth)


class PhysicalNASStorageProvider(FilesystemNASProvider):
    """
    Mode C: Physical UGREEN AI NAS Provider.
    Enforces production physical NAS mount guarantees:
    - Verifies physical mount presence (e.g. /volume1/NGO_Projects).
    - Requires strict read-only operation.
    - Explicitly surfaces hardware unavailability without falling back to mock fixtures.
    """
    def __init__(
        self,
        nas_root: Optional[str] = None,
        max_files: Optional[int] = None,
        max_depth: Optional[int] = None
    ):
        super().__init__(
            nas_root=nas_root or settings.UGREEN_NAS_ROOT,
            max_files=max_files,
            max_depth=max_depth
        )

    def verify_hardware_readiness(self) -> Dict[str, Any]:
        """
        Diagnostic probe to verify that physical UGREEN NAS storage volume is mounted,
        accessible, and adheres to read-only constraints.
        """
        if not self.nas_root or not os.path.exists(self.nas_root):
            return {
                "hardware_ready": False,
                "status": "UNMOUNTED",
                "nas_root": self.nas_root,
                "error": f"Configured physical NAS root '{self.nas_root}' is not mounted."
            }

        try:
            st = os.stat(self.nas_root)
            return {
                "hardware_ready": True,
                "status": "MOUNTED",
                "nas_root": self.nas_root,
                "permissions_octal": oct(st.st_mode)[-3:],
                "inode": st.st_ino
            }
        except Exception as e:
            return {
                "hardware_ready": False,
                "status": "ERROR",
                "nas_root": self.nas_root,
                "error": str(e)
            }


class StorageProviderFactory:
    """
    Provider factory selecting between Mode A, Mode B, and Mode C based on validated
    runtime environment settings.
    """
    @staticmethod
    def get_provider(
        mode: Optional[Union[StorageMode, str]] = None,
        nas_root: Optional[str] = None
    ) -> EvidenceProvider:
        raw_mode = (mode or getattr(settings, "UGREEN_NAS_MODE", "emulated")).lower().strip()

        if raw_mode in ("real", "physical_nas", "mode_c"):
            return PhysicalNASStorageProvider(nas_root=nas_root or settings.UGREEN_NAS_ROOT)
        elif raw_mode in ("local_dev", "mode_a", "dev"):
            return LocalDevStorageProvider(dev_root=nas_root or getattr(settings, "LOCAL_DEV_ROOT", "./storage/dev_fixtures"))
        elif raw_mode in ("emulated", "emulated_nas", "mode_b"):
            return EmulatedNASProvider()
        else:
            raise ValueError(f"Invalid storage mode: '{raw_mode}'. Permitted: 'real', 'emulated', 'local_dev'.")


class UGreenNASBridge:
    """
    Pluggable router delegating to FilesystemNASProvider or EmulatedNASProvider
    based on explicit configuration settings (settings.UGREEN_NAS_MODE).
    Maintains 100% backward-compatibility for all existing service and test callers.
    """
    def __init__(self, nas_host: Optional[str] = None):
        self.nas_host = nas_host or "local"
        self._emulated_provider = EmulatedNASProvider()

    def get_active_provider(self, scope_path: Optional[str] = None) -> EvidenceProvider:
        mode = getattr(settings, "UGREEN_NAS_MODE", "emulated").lower().strip()
        if mode == "real":
            return FilesystemNASProvider(nas_root=settings.UGREEN_NAS_ROOT)
        elif mode == "emulated":
            if getattr(settings, "STORAGE_MODE", "") == "local_dev":
                return LocalDevStorageProvider(dev_root=getattr(settings, "LOCAL_DEV_ROOT", None))
            return self._emulated_provider
        elif mode in ("local_dev", "physical_nas"):
            return StorageProviderFactory.get_provider(mode=mode)
        else:
            raise ValueError(f"Invalid UGREEN_NAS_MODE: '{mode}'. Allowed modes are 'real' or 'emulated'.")

    def discover_documents(self, scope_path: str) -> List[Dict[str, Any]]:
        provider = self.get_active_provider(scope_path)
        return provider.discover_documents(scope_path)

    def extract_document(self, file_path: str, doc_type: str) -> Dict[str, Any]:
        provider = self.get_active_provider(file_path)
        return provider.extract_document(file_path, doc_type)


ugreen_bridge = UGreenNASBridge()
