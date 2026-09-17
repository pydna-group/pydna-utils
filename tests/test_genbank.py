"""Offline behavioral tests for permanent GenBank caching."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from io import StringIO
import importlib
import os
from pathlib import Path
import subprocess
import sys
import time

from Bio import SeqIO
from pydna.dseqrecord import Dseqrecord
import pytest

cache = importlib.import_module("pydna_utils.genbank")
FIXTURE = Path(__file__).parent / "fixtures" / "TEST123.1.gb"


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setattr(cache.cfg, "pydna_ncbi_cache_dir", str(tmp_path))
    monkeypatch.setenv("pydna_email", "test@example.org")
    calls = []
    text = FIXTURE.read_text()
    parent = SeqIO.read(StringIO(text), "genbank")

    def fetch(**kwargs):
        calls.append(kwargs)
        assert kwargs["strand"] == 1
        if kwargs["seq_start"] is None and kwargs["seq_stop"] is None:
            record = deepcopy(parent)
        else:
            start, stop = (kwargs["seq_start"] or 1) - 1, kwargs["seq_stop"]
            record = parent[start:stop]
            record.annotations["topology"] = "linear"
        record.id = kwargs["id"]
        return StringIO(record.format("genbank"))

    monkeypatch.setattr(cache.Entrez, "efetch", fetch)
    return tmp_path, calls, parent


def test_full_reuse_features_and_independent_results(setup):
    directory, calls, parent = setup
    full = cache.genbank("TEST123.1")
    assert isinstance(full, Dseqrecord) and full.circular
    assert full.source.repository_id == "TEST123.1"
    assert full.source.coordinates is None
    fragment = cache.genbank("TEST123.1", 3, 9)
    assert str(fragment.seq) == str(parent.seq[2:9])
    assert not fragment.circular
    assert fragment.annotations["topology"] == "linear"
    labels = {f.qualifiers["label"][0]: f for f in fragment.features}
    assert set(labels) == {"inside", "joined"}
    assert int(labels["inside"].location.start) == 1
    assert len(labels["joined"].location.parts) == 2
    assert fragment.source.coordinates.start == 2  # Biopython uses zero-based starts
    assert fragment.source.coordinates.end == 9
    labels["inside"].qualifiers["label"][0] = "changed"
    assert cache.genbank("TEST123.1", 3, 9).features[0].qualifiers["label"] == [
        "inside"
    ]
    assert len(calls) == 1
    assert list(directory.glob("*.gb")) == [directory / "TEST123.1.gb"]


def test_containment_replacement_and_partial_overlap(setup):
    directory, calls, parent = setup
    cache.genbank("TEST123.1", 3, 7)
    cache.genbank("TEST123.1", 2, 8)
    assert not (directory / "TEST123.1_3-7.gb").exists()
    assert (directory / "TEST123.1_2-8.gb").exists()
    assert str(cache.genbank("TEST123.1", 3, 7).seq) == str(parent.seq[2:7])
    assert len(calls) == 2
    cache.genbank("TEST123.1", 7, 10)
    assert len(list(directory.glob("*.gb"))) == 2
    cache.genbank("TEST123.1")
    assert len(list(directory.glob("*.gb"))) == 1
    assert len(calls) == 4


@pytest.mark.parametrize(
    "accession_text",
    [
        "TEST123.1 REGION: complement(3..7)",
        "TEST123.1:c7-3",
        "TEST123.1 c3-7",
    ],
)
def test_reverse_syntax(setup, accession_text):
    directory, calls, parent = setup
    result = cache.genbank(accession_text)
    assert str(result.seq) == str(parent.seq[2:7].reverse_complement())
    assert result.source.coordinates.strand == -1
    assert result.features[0].location.strand == -1
    cache.genbank("TEST123.1", 3, 7)
    assert len(calls) == 1
    stored = SeqIO.read(directory / "TEST123.1_3-7.gb", "genbank")
    assert str(stored.seq) == str(parent.seq[2:7])


@pytest.mark.parametrize("strand", [2, "c", "C", "crick", "Antisense", "2", "-", "-1"])
def test_strand_aliases(setup, strand):
    _, _, parent = setup
    assert str(cache.genbank("TEST123.1", 3, 7, strand).seq) == str(
        parent.seq[2:7].reverse_complement()
    )


def test_omitted_bounds(setup):
    directory, calls, parent = setup
    cache.genbank("TEST123.1", seq_start=5)
    assert (directory / "TEST123.1_5-20.json").exists()
    assert str(cache.genbank("TEST123.1", seq_start=10).seq) == str(parent.seq[9:])
    assert len(calls) == 1
    cache.genbank("TEST123.1", seq_stop=7)
    assert calls[-1]["seq_start"] is None
    cache.genbank("TEST123.1")
    assert len(calls) == 3
    assert not list(directory.glob("*.json"))
    cache.genbank("TEST123.1", seq_start=2)
    cache.genbank("TEST123.1", seq_stop=2)
    assert len(calls) == 3


def test_bounded_fragment_cannot_answer_open_end(setup):
    _, calls, _ = setup
    cache.genbank("TEST123.1", 5, 10)
    assert len(cache.genbank("TEST123.1", seq_start=7)) == 14
    assert len(calls) == 2


def test_timestamps_and_versions(setup):
    directory, calls, _ = setup
    cache.genbank("TEST123.1")
    os.utime(directory / "TEST123.1.gb", (1, 1))
    cache.genbank("TEST123.1", 1, 1)
    assert len(calls) == 1
    cache.genbank("TEST123.2", 3, 7)
    assert (directory / "TEST123.1.gb").exists()
    assert (directory / "TEST123.2_3-7.gb").exists()
    assert len(calls) == 2


@pytest.mark.parametrize(
    "corruption", ["truncated", "wrong_version", "wrong_length", "garbage"]
)
def test_corrupt_cache_recovery(setup, corruption):
    directory, calls, _ = setup
    cache.genbank("TEST123.1", 3, 7)
    path = directory / "TEST123.1_3-7.gb"
    text = path.read_text()
    if corruption == "truncated":
        text = text.rsplit("//", 1)[0]
    elif corruption == "wrong_version":
        text = text.replace("TEST123.1", "TEST123.2")
    elif corruption == "wrong_length":
        text = FIXTURE.read_text()
    else:
        text = "garbage\n//\n"
    path.write_text(text)
    assert len(cache.genbank("TEST123.1", 3, 7)) == 5
    assert len(calls) == 2


@pytest.mark.parametrize("failure", ["network", "invalid_response", "write"])
def test_failed_replacement_preserves_fragment(setup, monkeypatch, failure):
    directory, _, _ = setup
    cache.genbank("TEST123.1", 3, 7)
    old = (directory / "TEST123.1_3-7.gb").read_bytes()

    def fail(*args, **kwargs):
        raise OSError("simulated failure")

    if failure == "network":
        monkeypatch.setattr(cache.Entrez, "efetch", fail)
    elif failure == "invalid_response":
        monkeypatch.setattr(cache.Entrez, "efetch", lambda **kw: StringIO("broken"))
    else:
        monkeypatch.setattr(cache.os, "replace", fail)
    with pytest.raises((OSError, ValueError)):
        cache.genbank("TEST123.1", 2, 8)
    assert (directory / "TEST123.1_3-7.gb").read_bytes() == old
    assert not (directory / "TEST123.1_2-8.gb").exists()
    assert not list(directory.glob("*.tmp"))


def test_threads_share_one_download(setup, monkeypatch):
    _, calls, _ = setup
    fetch = cache.Entrez.efetch

    def slow(**kwargs):
        time.sleep(0.03)
        return fetch(**kwargs)

    monkeypatch.setattr(cache.Entrez, "efetch", slow)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: cache.genbank("TEST123.1", 3, 7), range(4)))
    assert [len(r) for r in results] == [5] * 4
    assert len(calls) == 1


@pytest.mark.parametrize(
    "args,kwargs",
    [
        (("TEST123",), {}),
        (("../TEST123.1",), {}),
        (("TEST123.1", 0, 7), {}),
        (("TEST123.1", 7, 3), {}),
        (("TEST123.1", 1.5, 7), {}),
        (("TEST123.1",), {"unknown": 1}),
        (("TEST123.1", 3), {"seq_start": 2}),
    ],
)
def test_invalid_arguments_do_not_download(setup, args, kwargs):
    _, calls, _ = setup
    with pytest.raises((ValueError, TypeError)):
        cache.genbank(*args, **kwargs)
    assert not calls


def test_import_does_not_patch_http():
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import urllib.request; from Bio import Entrez; "
            "u, e = urllib.request.urlopen, Entrez.urlopen; "
            "import pydna_utils.genbank; "
            "assert u is urllib.request.urlopen and e is Entrez.urlopen",
        ],
        check=True,
    )


def test_tail_endpoint_survives_replacement(setup):
    directory, calls, _ = setup
    cache.genbank("TEST123.1", seq_start=5)
    cache.genbank("TEST123.1", 2, 20)
    assert not (directory / "TEST123.1_5-20.gb").exists()
    assert (directory / "TEST123.1_2-20.json").exists()
    assert len(cache.genbank("TEST123.1", seq_start=10)) == 11
    assert len(calls) == 2


def test_stale_tail_metadata_does_not_prove_coverage(setup):
    directory, calls, _ = setup
    cache.genbank("TEST123.1", seq_start=5)
    (directory / "TEST123.1_5-20.json").write_text(
        '{"source_end": 20, "sha256": "stale"}'
    )
    cache.genbank("TEST123.1", seq_start=10)
    assert len(calls) == 2


def test_select_smallest_fragment_then_full(setup, monkeypatch):
    directory, calls, _ = setup
    # Seed externally supplied files to exercise precedence even though normal
    # cache replacement would remove these redundant fragments.
    cache.genbank("TEST123.1")
    full = SeqIO.read(directory / "TEST123.1.gb", "genbank")
    large = full[1:10]
    small = full[2:8]
    large.description, small.description = "large", "small"
    SeqIO.write(large, directory / "TEST123.1_2-10.gb", "genbank")
    SeqIO.write(small, directory / "TEST123.1_3-8.gb", "genbank")
    assert cache.genbank("TEST123.1", 3, 8).description == "small"
    seen = []
    original = cache._parse

    def parse(text, *args):
        seen.append(text)
        return original(text, *args)

    monkeypatch.setattr(cache, "_parse", parse)
    cache.genbank("TEST123.1", 4, 7)
    assert len(seen) == 1 and "small" in seen[0]
    assert len(calls) == 1


def test_email_and_embedded_region_override(setup):
    _, calls, parent = setup
    result = cache.genbank(
        "TEST123.1 REGION: 3..7", 1, 2, strand=2, email="override@example.org"
    )
    assert str(result.seq) == str(parent.seq[2:7])
    assert cache.Entrez.email == "override@example.org"
    assert (calls[0]["seq_start"], calls[0]["seq_stop"]) == (3, 7)


def test_processes_share_one_download(setup):
    directory, _, _ = setup
    script = r"""
import importlib, sys, time
from pathlib import Path
from io import StringIO
c = importlib.import_module("pydna_utils.genbank")
c.cfg.pydna_ncbi_cache_dir = sys.argv[1]
root = Path(sys.argv[1])
def fetch(**kwargs):
    with (root / "downloads").open("a") as log:
        log.write("download\n")
    time.sleep(0.15)
    return StringIO(Path(sys.argv[2]).read_text())
c.Entrez.efetch = fetch
(root / (sys.argv[3] + ".ready")).touch()
while not (root / "go").exists():
    time.sleep(0.01)
assert len(c.genbank("TEST123.1", email="test@example.org")) == 20
"""
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", script, str(directory), str(FIXTURE), str(i)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for i in range(2)
    ]
    try:
        deadline = time.monotonic() + 20
        while len(list(directory.glob("*.ready"))) < 2:
            if time.monotonic() > deadline or any(
                p.poll() is not None for p in processes
            ):
                pytest.fail("Workers did not reach the start barrier")
            time.sleep(0.02)
        (directory / "go").touch()
        for process in processes:
            out, err = process.communicate(timeout=20)
            assert process.returncode == 0, out + err
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
            process.wait()
    assert (directory / "downloads").read_text().splitlines() == ["download"]
