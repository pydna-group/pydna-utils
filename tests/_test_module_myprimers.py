#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from textwrap import dedent
from pydna_utils import load_settings

cfg = load_settings()
cfg.pydna_primers = "primers_linux_line_endings.txt"

@pytest.fixture(scope="module")
def settings_file(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("settings")
    p = tmp / settings.
    p.write_text(dedent("""\
                        pydna_ape_cmd = "/usr/bin/tclsh /home/bjorn/.ApE/ApE.tcl"
                        pydna_snapgene_cmd = "/opt/gslbiotech/snapgene/snapgene.sh"
                        pydna_enzymes = "/home/bjorn/.ApE/Enzymes/LGM_group.txt"
                        pydna_primers = "/home/bjorn/myvault/PRIMERS.md"
                        pydna_email = "bjornjobb@gmail.com"
                        pydna_ncbi_cache_dir = "/home/bjorn/.cache/pydna_utils"
                        pydna_ncbi_expiration = "604800" # seconds
                        """))
    return p



@pytest.fixture(scope="module")
def primers_file(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("primers")
    p = tmp / "primers_linux_line_endings.txt"
    p.write_text(dedent("""\
                 >3_primer
                 aaaaaaaa

                 >2_primer
                 cccccccc

                 >1_primer
                 gggggggg

                 >0_primer
                 tttttttt
                 """))
    return p

def test_b(primers_file):
    breakpoint()
    assert primers_file.read_text().count(">") == 4
