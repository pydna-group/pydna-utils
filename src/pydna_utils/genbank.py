#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cached access to GenBank.

The pydna_utils works just like the pydna.genbank.genbank function, but
provides a cache.

This cache can be set to expire more or less frequently
by the `pydna_ncbi_expiration` setting in the pydna_primers entry in the settings
file pydna_config.toml.

The cache is located in the directory given by the `pydna_ncbi_cache_dir` entry
in the settings file pydna_config.toml.
"""

import os
import re
from pydna_utils.settings import load_settings
from pydna_utils.entrez_cache import enable_entrez_cache

enable_entrez_cache()

cfg = load_settings()

os.environ["pydna_email"] = cfg.pydna_email

regex = "(^(?:.+?)\.[0-9]+)(?:(?:\s)??(?:REGION: )??(complement)??(?:\()??(\d+)(?:\.\.)(\d+)(?:\))??)?"

def genbank(accession: str = "CS570233.1", *args, **kwargs):

    from pydna.genbank import genbank

    assert re.match(regex, accession.strip()), "accession number must have a version"

    return genbank(accession, *args, **kwargs)
