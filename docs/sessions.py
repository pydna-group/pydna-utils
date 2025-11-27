#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
%history -p -o -f session.txt
"""

from pydna_utils.editor import ape
from pydna.dseqrecord import Dseqrecord
sequence = Dseqrecord("GGATCC")
sequence.seq
ape(sequence)

from pydna_utils.editor import snapgene
from pydna.dseqrecord import Dseqrecord
sequence = Dseqrecord("GGATCC")
snapgene(sequence)


from pydna_utils.myprimers import PrimerList
pl = PrimerList()
len(pl)
pl[1]
pl[2]
print(pl[1].format("fasta"))
print(pl[2].format("fasta"))
pl.accessed
pl.code(pl.accessed)


from pydna_utils.myenzymes import myenzymes
myenzymes


from pydna_utils.genbank import genbank
gb_sequence = genbank("A23695.1")
gb_sequence
gb_sequence.seq


import pydna_utils
pydna_utils.get_settings()
from pydna_utils import open_config_file
open_config_file()  # opens the config file for editing in system text editor.
from pydna_utils import open_cache_folder
open_cache_folder() # opens the cache folder in system file explorer.
