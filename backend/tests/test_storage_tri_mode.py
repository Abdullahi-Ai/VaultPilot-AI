import os
import pytest
from app.core.config import settings, Settings, StorageMode
from app.services.ugreen_bridge import (
    ugreen_bridge,
    StorageProviderFactory,
    LocalDevStorageProvider,
    EmulatedNASProvider,
    PhysicalNASStorageProvider,
    FilesystemNASProvider,
    NASStorageUnavailableError,
    NASSecurityViolationError,
    NASResourceExceededError
)

def test_storage_mode_enum_values():
    """Verify that StorageMode supports Mode A, Mode B, and Mode C."""
    assert StorageMode.LOCAL_DEV == "local_dev"
    assert StorageMode.EMULATED_NAS == "emulated_nas"
    assert StorageMode.PHYSICAL_NAS == "physical_nas"

def test_storage_provider_factory_mode_b_emulated():
    """Verify factory returns EmulatedNASProvider for Mode B."""
    provider = StorageProviderFactory.get_provider("emulated")
    assert isinstance(provider, EmulatedNASProvider)

    docs = provider.discover_documents("/volume1/test")
    assert len(docs) == 8
    assert any(d["filename"] == "PO-2026-081.pdf" for d in docs)

def test_storage_provider_factory_mode_a_local_dev(tmp_path):
    """Verify factory returns LocalDevStorageProvider for Mode A."""
    dev_dir = str(tmp_path / "dev_storage")
    provider = StorageProviderFactory.get_provider("local_dev", nas_root=dev_dir)
    assert isinstance(provider, LocalDevStorageProvider)
    assert os.path.exists(dev_dir)

def test_storage_provider_factory_mode_c_physical_nas(tmp_path):
    """Verify factory returns PhysicalNASStorageProvider for Mode C."""
    nas_dir = str(tmp_path / "physical_nas")
    os.makedirs(nas_dir, exist_ok=True)
    provider = StorageProviderFactory.get_provider("real", nas_root=nas_dir)
    assert isinstance(provider, PhysicalNASStorageProvider)
    assert isinstance(provider, FilesystemNASProvider)

    readiness = provider.verify_hardware_readiness()
    assert readiness["hardware_ready"] is True
    assert readiness["status"] == "MOUNTED"

def test_physical_nas_unmounted_hardware_readiness():
    """Verify PhysicalNASStorageProvider accurately detects unmounted physical root."""
    provider = PhysicalNASStorageProvider(nas_root="/nonexistent/physical/ugreen/volume1")
    readiness = provider.verify_hardware_readiness()
    assert readiness["hardware_ready"] is False
    assert readiness["status"] == "UNMOUNTED"
    assert "not mounted" in readiness["error"]

def test_physical_nas_bounded_discovery_file_limit(tmp_path):
    """Verify discovery halts with NASResourceExceededError when max_files is exceeded."""
    scope_dir = tmp_path / "overflow_scope"
    scope_dir.mkdir()

    # Create 10 files
    for i in range(10):
        (scope_dir / f"INV-TEST-{i:03d}.txt").write_text(f"Invoice {i}")

    # Set max_files to 5
    provider = PhysicalNASStorageProvider(nas_root=str(tmp_path), max_files=5)
    with pytest.raises(NASResourceExceededError) as exc_info:
        provider.discover_documents(str(scope_dir))

    assert "Discovery exceeded safety threshold of 5 files" in str(exc_info.value)

def test_physical_nas_bounded_discovery_depth_limit(tmp_path):
    """Verify discovery does not recurse deeper than max_depth."""
    base_dir = tmp_path / "base"
    d1 = base_dir / "depth1"
    d2 = d1 / "depth2"
    d3 = d2 / "depth3"
    d3.mkdir(parents=True)

    (base_dir / "PO-ROOT.txt").write_text("Root file")
    (d1 / "PO-D1.txt").write_text("Depth 1 file")
    (d3 / "PO-D3.txt").write_text("Depth 3 file")

    # Set max_depth to 2 (should find PO-ROOT and PO-D1, but not descend into depth3)
    provider = PhysicalNASStorageProvider(nas_root=str(tmp_path), max_depth=2)
    docs = provider.discover_documents(str(base_dir))

    found_names = [d["filename"] for d in docs]
    assert "PO-ROOT.txt" in found_names
    assert "PO-D1.txt" in found_names
    assert "PO-D3.txt" not in found_names
