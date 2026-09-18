# GenBank file cache

`pydna_utils.genbank.genbank()` keeps the existing pydna-style calling interface
and returns a fresh `Dseqrecord` with its NCBI accession and source coordinates.
It requires an accession **including its version**.

```python
from pydna_utils.genbank import genbank

record = genbank("CS570233.1")
fragment = genbank("CS570233.1", seq_start=3, seq_stop=7)
reverse = genbank("CS570233.1 REGION: complement(3..7)")
# Positional coordinates and colon syntax also work:
fragment = genbank("CS570233.1", 3, 7)
reverse = genbank("CS570233.1:c7-3")
```

Set `pydna_email` and `pydna_ncbi_cache_dir` in the existing `pydna_config.toml`.
The `email=` argument overrides the email used on a cache miss. Downloads use
Biopython Entrez, including its retries and request throttling. Cache hits make
no network requests and do not require email validation.

## Files and coverage

Files are stored directly in the configured cache directory:

```text
CS570233.1.gb          # complete record
CS570233.1_3-7.gb      # fragment, accession positions 3 through 7 inclusive
CS570233.1.lock        # persistent process-coordination file
```

The underscore separator is compatible with Windows, macOS, and Linux. All
records are downloaded in the forward orientation; reverse-strand results are
produced locally. Coordinates in filenames are one-based and inclusive;
Biopython locations in returned objects use zero-based, half-open coordinates.

An exact fragment is preferred, followed by the smallest containing fragment,
then a complete record. Only one cached file is used to answer a request.
Overlapping fragments are not merged, and missing gaps are not fetched
separately. On a miss, only the requested region is downloaded. Locally derived
subsequences are not written back as additional files.

An omitted start means position 1. An omitted stop means the accession's end,
not just the end of any cached fragment. For downloads with an omitted stop, a
small `.json` sidecar records the known endpoint and a SHA-256 digest tying it
to the GenBank file. A bounded fragment without endpoint metadata cannot prove
that it reaches the accession's end. A full-record request uses a complete
record file. A request exceeding the available sequence is rejected if the
server's response does not have the requested length.

After a larger fragment is validated and atomically saved, wholly contained
fragments for the same accession version are removed. A complete record replaces
its contained fragments. Partially overlapping fragments and other versions
remain. Cleanup failures leave redundant files rather than failing the request.

Downloads and cleanup are coordinated by thread and OS file locks. Lock files
remain in place deliberately; their existence does not mean a lock is held.
Temporary files are never candidates for cache reads. Invalid, truncated,
wrong-version, or wrong-length records are treated as misses; invalid downloads
are never published. Replacement failures leave existing fragments intact.

## Permanent snapshots

**There is no expiration, periodic refresh, or freshness check.**

Cached files preserve the downloaded sequence and annotations indefinitely.
Annotation changes at NCBI are not tracked, even when the accession version is
unchanged. To refresh a record deliberately, remove its `.gb` file and associated
`.json` file while no downloads are running, then request it again. Removing a
fragment may still allow reuse of a larger cached record.

## Annotation behavior

Files are parsed with Biopython `SeqIO`. Local slicing preserves fully contained
features, including compound locations, and adjusts their coordinates. Features
crossing either boundary are omitted according to Biopython's slicing rules;
features are not clipped and their qualifiers are not reconstructed. Organism,
taxonomy, and source annotations are retained for derived fragments; other
parent-level annotations and database cross-references are not copied blindly.

Whole circular records remain circular; requested fragments are linear. Reverse
complements transform feature positions and strands. The returned source always
refers to the requested accession region, not the parent cache interval.

An exact downloaded fragment retains the annotations supplied by NCBI. A local
slice can differ from an NCBI-generated fragment, particularly at feature
boundaries. After replacement by a larger record, the same region may therefore
have different boundary annotations. Results are independent objects, so caller
modifications do not affect later reads.

## Tests

Install pytest in a development environment and run:

```sh
python -m pytest tests/test_genbank.py
```

Tests use local GenBank fixtures and mocked downloads, not live NCBI access.
