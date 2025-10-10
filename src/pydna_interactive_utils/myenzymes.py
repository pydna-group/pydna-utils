#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2013-2023 by Björn Johansson.  All rights reserved.
# This code is part of the Python-dna distribution and governed by its
# license.  Please see the LICENSE.txt file that should have been included
# as part of this package.
"""This module establish a RestrictionBatch based on enzymes found in a text file specified in the enzymes entry
in the python.ini file or by the environment variable pydna_enzymes.

The text file will be searched for all enzymes in the biopython
AllEnzymes batch which is located in the Bio.Restriction package.

The pydna.myenzymes.myenzymes contains a new restriction batch with the enzymes contained
within the file specified.
"""

import re as _re
from Bio.Restriction import AllEnzymes as _AllEnzymes
from Bio.Restriction import RestrictionBatch as _RestrictionBatch
from .settings import load_settings

cfg = load_settings()

with open(cfg.pydna_enzymes, encoding="utf-8") as _f:
    _text = _f.read()

myenzymes = _RestrictionBatch([e for e in _AllEnzymes if str(e).lower() in _re.split(r"\W+", _text.lower())])
