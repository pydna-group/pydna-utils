#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A RestrictionBatch based on enzyme names in a text file.

The text file is specified in the pydna_enzymes entry in the settings
file pydna_config.toml.

The text file will be searched for all enzymes in the biopython
AllEnzymes batch which is located in the Bio.Restriction package.

No particular formatting is required exept whitespace between enzyme names.
Enzyme names has the be written as they appear in REBASE.

See Biopython :class:`Bio.Restriction.RestrictionBatch`

"""

import re
from Bio.Restriction import AllEnzymes
from Bio.Restriction import RestrictionBatch
from .settings import load_settings

cfg = load_settings()

with open(cfg.pydna_enzymes, encoding="utf-8") as f:
    text = f.read()

myenzymes = RestrictionBatch([e for e in AllEnzymes if str(e).lower() in re.split(r"\W+", text.lower())])
