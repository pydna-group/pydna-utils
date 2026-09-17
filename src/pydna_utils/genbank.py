"""Permanent, interval-aware GenBank file cache (no HTTP monkeypatching).

Coordinates in filenames and requests are one-based and inclusive. Files are
forward-strand snapshots; only fully contained features survive local slicing.
The legacy ``pydna_ncbi_expiration`` setting does not apply to this cache.
"""

from contextlib import contextmanager
from copy import deepcopy
import hashlib
from io import StringIO
import json
import os
from pathlib import Path
import re
import tempfile
import threading
import warnings

from Bio import Entrez, SeqIO, BiopythonParserWarning
from Bio.SeqFeature import SimpleLocation
from pydna.dseqrecord import Dseqrecord
from pydna.genbank import Genbank
from pydna.opencloning_models import NCBISequenceSource

from pydna_utils.settings import load_settings

cfg = load_settings()
os.environ["pydna_email"] = cfg.pydna_email

# Also protects Entrez's process-global email/tool and request throttling between
# calls through this wrapper. OS locks below coordinate separate processes.
_THREAD_LOCK = threading.RLock()


@contextmanager
def _cache_lock(directory, accession):
    """Hold a persistent lock file; never unlink it (that would race waiters)."""
    with _THREAD_LOCK:
        directory.mkdir(parents=True, exist_ok=True)
        with (directory / f"{accession}.lock").open("a+b") as handle:
            if os.name == "nt":
                import msvcrt
                import time

                handle.seek(0, os.SEEK_END)
                if not handle.tell():
                    handle.write(b"\0")
                    handle.flush()
                handle.seek(0)
                while True:
                    try:
                        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                        break
                    except OSError as exc:
                        if exc.errno not in (13, 11, 36):
                            raise
                        time.sleep(0.05)
            else:
                import fcntl

                fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                yield
            finally:
                if os.name == "nt":
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle, fcntl.LOCK_UN)


def _normalize(accession, start, stop, strand):
    accession = accession.strip()
    match = re.fullmatch(
        r"(?P<id>[A-Za-z][A-Za-z0-9_]*\.[0-9]+)"
        r"(?:\s+REGION:\s*(?:(?P<rc>complement)\()?"
        r"(?P<a>\d+)\.\.(?P<b>\d+)(?(rc)\))"
        r"|[:\s]+(?P<c>c)?(?P<x>\d+)-(?P<y>\d+))?",
        accession,
    )
    if not match:
        raise ValueError("Expected a versioned accession and an optional region")
    accession = match["id"]
    if match["a"] is not None:
        start, stop = match["a"], match["b"]
        strand = 2 if match["rc"] else 1
    elif match["x"] is not None:
        start, stop = int(match["x"]), int(match["y"])
        strand = 2 if match["c"] else 1
        if match["c"] and start > stop:
            start, stop = stop, start
    if strand not in (1, 2):
        strand = (
            2
            if str(strand).lower() in ("c", "crick", "antisense", "2", "-", "-1")
            else 1
        )
    for value in (start, stop):
        if value is not None and (
            not re.fullmatch(r"[0-9]+", str(value)) or int(value) < 1
        ):
            raise ValueError("Coordinates must be positive integers")
    start = int(start) if start is not None else None
    stop = int(stop) if stop is not None else None
    if start is not None and stop is not None and start > stop:
        raise ValueError("seq_start must not exceed seq_stop")
    return accession, start, stop, strand


def _parse(text, accession, length=None):
    # SeqIO tolerates a missing terminator; a cache must not accept torn files.
    if not text.rstrip().endswith("//"):
        raise ValueError("Incomplete GenBank record")
    with warnings.catch_warnings():
        warnings.simplefilter("error", BiopythonParserWarning)
        record = SeqIO.read(StringIO(text), "genbank")
    if record.id.split(":", 1)[0] != accession:
        raise ValueError("GenBank accession/version does not match the request")
    if not len(record) or not record.seq.defined:
        raise ValueError("GenBank record has no complete sequence")
    if length is not None and len(record) != length:
        raise ValueError("GenBank sequence length does not match its interval")
    return record


def _entries(directory, accession):
    pattern = re.compile(re.escape(accession) + r"(?:_(\d+)-(\d+))?\.gb")
    for path in directory.glob(f"{accession}*.gb"):
        match = pattern.fullmatch(path.name)
        if match:
            start, stop = match.groups()
            if start is None:
                yield path, 1, None
            elif 1 <= int(start) <= int(stop):
                yield path, int(start), int(stop)


def _digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _reaches_end(path, text, stop):
    # Only downloads with an omitted stop prove the accession's endpoint.
    # The digest makes a stale/partially replaced sidecar harmless.
    try:
        metadata = json.loads(path.with_suffix(".json").read_text())
        return metadata == {"source_end": stop, "sha256": _digest(text)}
    except (OSError, ValueError):
        return False


def _lookup(directory, accession, start, stop):
    whole = start is None and stop is None
    lower = start or 1
    entries = sorted(
        _entries(directory, accession),
        key=lambda e: (float("inf") if e[2] is None else e[2] - e[1], e[0].name),
    )
    for path, left, right in entries:
        if whole and right is not None:
            continue
        if left > lower or (stop is not None and right is not None and right < stop):
            continue
        try:
            text = path.read_text(encoding="utf-8")
            record = _parse(
                text, accession, None if right is None else right - left + 1
            )
        except (OSError, ValueError, UnicodeError, BiopythonParserWarning):
            continue
        end = left + len(record) - 1
        if stop is None and right is not None and not _reaches_end(path, text, end):
            continue
        if lower > end or (stop is not None and stop > end):
            continue
        return record, left, end, right is None
    return None


def _atomic_write(path, text):
    name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            name = handle.name
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if name is not None:
            Path(name).unlink(missing_ok=True)


def _download(directory, accession, start, stop, email):
    connection = Genbank(email or os.getenv("pydna_email"))
    Entrez.email, Entrez.tool = connection.email, connection.tool
    with Entrez.efetch(
        db="nuccore",
        id=accession,
        rettype="gbwithparts",
        retmode="text",
        seq_start=start,
        seq_stop=stop,
        strand=1,
    ) as handle:
        text = handle.read()
    left = start or 1
    record = _parse(text, accession, None if stop is None else stop - left + 1)
    end = left + len(record) - 1
    whole = start is None and stop is None
    path = directory / (f"{accession}.gb" if whole else f"{accession}_{left}-{end}.gb")
    reaches_end = stop is None
    # Preserve endpoint knowledge when replacing a tail with a larger bounded
    # download. Otherwise cleanup would lose useful coverage information.
    if not whole and not reaches_end:
        for old, old_start, old_stop in _entries(directory, accession):
            if old_stop == end and left <= old_start:
                try:
                    old_text = old.read_text(encoding="utf-8")
                    _parse(old_text, accession, end - old_start + 1)
                    reaches_end = _reaches_end(old, old_text, end)
                except (OSError, ValueError, BiopythonParserWarning):
                    continue
                if reaches_end:
                    break
    # Publish metadata first. An interrupted write cannot make metadata for new
    # contents apply to old contents, because the digest must match.
    if reaches_end and not whole:
        _atomic_write(
            path.with_suffix(".json"),
            json.dumps({"source_end": end, "sha256": _digest(text)}),
        )
    _atomic_write(path, text)
    for old, old_start, old_stop in list(_entries(directory, accession)):
        if (
            old != path
            and old_stop is not None
            and left <= old_start
            and old_stop <= end
        ):
            # Cleanup is optional: permissions must not turn a successful
            # download into a failure, or jeopardize the published replacement.
            try:
                old.unlink(missing_ok=True)
                old.with_suffix(".json").unlink(missing_ok=True)
            except OSError:
                pass
    return record, left, end, whole


def _extract(cached, accession, start, stop, strand):
    record, left, end, whole = cached
    lower, upper = start or 1, stop or end
    if lower == left and upper == end:
        record = deepcopy(record)
    else:
        parent = record
        slice_start, slice_stop = lower - left, upper - left + 1
        record = parent[slice_start:slice_stop]
        # Only organism-level metadata is safe to copy unmodified to a fragment.
        for key in ("organism", "taxonomy", "source"):
            if key in parent.annotations:
                record.annotations[key] = deepcopy(parent.annotations[key])
        record.description = f"{accession} REGION: {lower}..{upper}"
    circular = (
        whole
        and start is None
        and stop is None
        and record.annotations.get("topology") == "circular"
    )
    record.annotations["topology"] = "circular" if circular else "linear"
    if strand == 2:
        record = record.reverse_complement(
            id=True,
            name=True,
            description=True,
            annotations=True,
            dbxrefs=True,
        )
    result = Dseqrecord(record, circular=circular)
    result.source = NCBISequenceSource(
        repository_id=accession,
        coordinates=(
            None
            if start is None and stop is None
            else SimpleLocation(lower - 1, upper, -1 if strand == 2 else 1)
        ),
    )
    return result


def _get(accession, seq_start=None, seq_stop=None, strand=1, *, email=None):
    accession, start, stop, strand = _normalize(accession, seq_start, seq_stop, strand)
    directory = Path(cfg.pydna_ncbi_cache_dir).expanduser()
    with _cache_lock(directory, accession):
        cached = _lookup(directory, accession, start, stop)
        if cached is None:
            cached = _download(directory, accession, start, stop, email)
        return _extract(cached, accession, start, stop, strand)


def genbank(accession: str = "CS570233.1", *args, **kwargs):
    """Return a cached GenBank record or region as a fresh ``Dseqrecord``.

    Accepts pydna's ``seq_start``, ``seq_stop``, ``strand`` and ``email`` arguments,
    as well as embedded REGION/colon interval syntax. Requires accession.version.
    Cached records never expire. Local slicing retains fully contained features;
    boundary-crossing features are omitted, following Biopython's behavior.
    """
    return _get(accession, *args, **kwargs)
