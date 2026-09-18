# pydna-utils

Utilities for interactive work with [pydna](https://github.com/pydna-group/pydna):

- Open DNA sequences in ApE or SnapGene.
- Use a shared PCR primer list and restriction enzyme list.
- Download and cache GenBank records and sequence regions.

## Installation

Requires Python 3.12.7 or later, below 4.0.

```bash
pip install pydna-utils
```

## Settings

Settings are stored in `pydna_config.toml` in the user configuration directory
chosen by `platformdirs` (normally `~/.config/pydna_utils/` on Linux).
Create the file and set the paths for the features you use:

```python
from pydna_utils import load_settings, save_settings, open_config_file

settings = load_settings()
settings.pydna_email = "you@example.com"
settings.pydna_primers = "/path/to/primers.fasta"
settings.pydna_enzymes = "/path/to/enzymes.txt"
save_settings(settings)
open_config_file()
```

Set `pydna_ape_cmd` and `pydna_snapgene_cmd` to the commands that launch your
installed editors. The defaults contain machine-specific paths, so adjust them
before use. Restart your Python session after changing settings.

To display settings or open the default cache directory:

```python
from pydna_utils import tabulate_settings, open_cache_folder

print(tabulate_settings())
open_cache_folder()
```

## Open a sequence in an editor

```python
from pydna.dseqrecord import Dseqrecord
from pydna_utils.editor import ape, snapgene

sequence = Dseqrecord("GGATCC")
ape(sequence)
# snapgene(sequence)
```

## Shared primer list

Set `pydna_primers` to a text file containing primers in a format pydna can
read, such as FASTA. Primers are loaded in reverse file order, so new primers
can be added at the top. List indices start at zero.

```python
from pydna_utils.myprimers import PrimerList

primers = PrimerList()
primer = primers[0]
print(primer.format("fasta"))

# Generate code containing only the primers accessed in this session.
print(primers.code(primers.accessed))
```

## Shared restriction enzyme list

Set `pydna_enzymes` to a text file containing enzyme names recognized by
Biopython, separated by whitespace, for example `BamHI EcoRI HindIII`.

```python
from pydna_utils.myenzymes import myenzymes

print(myenzymes)
```

## Cached GenBank access

Set `pydna_email` to your email address before downloading. Use an accession
including its version. Each call returns a fresh `Dseqrecord`.

```python
from pydna_utils.genbank import genbank

record = genbank("CS570233.1")
fragment = genbank("CS570233.1", seq_start=3, seq_stop=7)
reverse = genbank("CS570233.1", seq_start=3, seq_stop=7, strand=2)
```

Coordinates are one-based and inclusive. Records are stored as GenBank files
in `pydna_ncbi_cache_dir`, normally `~/.cache/pydna_utils/` on Linux. Cached
records can serve requests for contained regions without another download.
Local slicing retains only features fully contained in the requested region.

Cached files do not expire or refresh automatically. The legacy
`pydna_ncbi_expiration` setting has no effect on this cache.

See [GenBank cache details](docs/genbank-cache.md) for cache behavior and how
to refresh a record.
