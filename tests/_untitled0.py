#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 11 13:52:54 2026

@author: bjorn
"""

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from pydna.parsers import parse_primers
from importlib import reload
from pydna_utils import myprimers
from unittest import mock
import textwrap

from pydna_utils import settings
# from tempfile import TemporaryDirectory


# Path(TemporaryDirectory())
# settings.CONFIG_FILE_NAME = "pydna_config.toml"
# settings.CONFIG_PATH = Path(user_config_dir(APP_NAME)) / CONFIG_FILE_NAME


monkeypatch = pytest.MonkeyPatch()

def test_PrimerList_init(monkeypatch, capsys):

    monkeypatch.setenv("pydna_primers", "primers_linux_line_endings.txt")

    primer_source = parse_primers("primers_linux_line_endings.txt")[::-1]

    reload(myprimers)

    pl1 = myprimers.PrimerList()

    assert pl1 == primer_source

    assert len(pl1) == 4

    primer_source = parse_primers("primers_linux_line_endings.txt")[::-1]

    pl2 = myprimers.PrimerList(primer_source)

    pl3 = myprimers.PrimerList(path="primers_linux_line_endings.txt")

    assert len(pl2) == len(pl3) == 4

    assert pl1 == pl2 == pl3

    newlist = parse_primers(
        """
                            >abc
                            aaa
                            >efg
                            ttt
                            """
    )

    np = pl2.assign_numbers(newlist)

    assert [s.name for s in parse_primers(np)] == ["5_abc", "4_efg"]

    newlist = parse_primers(
        """
                            >abc
                            aaa
                            >efg
                            tttttttt
                            """
    )

    np = pl2.assign_numbers(newlist)

    assert [s.name for s in parse_primers(np)] == ["4_abc", "0_primer"]

    with pytest.raises(ValueError):
        pl2.pydna_code_from_list(newlist)
    captured = capsys.readouterr()
    assert captured.out == ">abc 3-mer\naaa\n\n"



    code = textwrap.dedent(
        """\
    from pydna.parsers import parse_primers

    p = {}

    p[0], p[1], p[2], p[3] = parse_primers('''

    >0_primer 8-mer
    tttttttt

    >1_primer 8-mer
    gggggggg

    >2_primer 8-mer
    cccccccc

    >3_primer 8-mer
    aaaaaaaa

    ''')"""
    )

    assert pl1.pydna_code_from_list(pl1) == code

    pl4 = myprimers.PrimerList(path="primers_linux_line_endings.txt")

    assert pl4.accessed_indices == []
    pl4[1] = primer_source[1]
    assert pl4.accessed == primer_source[1:2]

    assert pl4.accessed_indices == [1]

    pl4.accessed_indices == []
    assert pl4[2:4] == primer_source[2:4]
    assert pl4.accessed_indices == [1, 2, 3]

    with pytest.raises(ValueError):
        myprimers.PrimerList(identifier="/")

    with pytest.raises(ValueError):
        pl3[2] = primer_source[1]

    with pytest.raises(IndexError):
        pl3[999] = primer_source[1]

    with pytest.raises(ValueError):
        pl2.open_folder()



    subp = mock.MagicMock()

    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.setattr("subprocess.run", subp)

    pl4.open_folder()

    subp.assert_called_with(["xdg-open", pl3.path.parent])


def test_check_primer_numbers(monkeypatch):

    pl = myprimers.PrimerList(path="primers_linux_line_endings_not_unique.txt")
    assert myprimers.check_primer_numbers(pl) == [pl[5]]


def test_undefined_sequence(monkeypatch):

    pl = myprimers.PrimerList(path="primers_linux_line_endings_not_unique.txt")
    assert myprimers.undefined_sequence(pl) == [pl[2]]


def test_find_duplicate_primers(monkeypatch):

    pl = myprimers.PrimerList(path="primers_linux_line_endings_not_unique.txt")
    assert myprimers.find_duplicate_primers(pl) == [[pl[1], pl[3]]]




import pytest
from importlib import reload
from pathlib import Path
from pydna.parsers import parse_primers
from unittest import mock
import textwrap

import pydna_utils.settings as settings
import pydna_utils.myprimers as myprimers


def write_config(tmp_path, primers_file):
    cfg = f"""
pydna_primers = "{primers_file}"
"""
    cfg_path = tmp_path / "pydna_config.toml"
    cfg_path.write_text(cfg)
    return cfg_path


def test_PrimerList_init(tmp_path, monkeypatch, capsys):
    primers = tmp_path / "primers_linux_line_endings.txt"
    primers.write_text(
        """>3_primer
aaaaaaaa

>2_primer
cccccccc

>1_primer
gggggggg

>0_primer
tttttttt
"""
    )

    # write config
    cfg_path = write_config(tmp_path, primers)

    # patch CONFIG_PATH before reload
    monkeypatch.setattr(settings, "CONFIG_PATH", cfg_path)

    # reload settings + module that uses it
    reload(settings)
    reload(myprimers)

    primer_source = parse_primers(primers.read_text())[::-1]

    pl1 = myprimers.PrimerList()
    assert pl1 == primer_source
    assert len(pl1) == 4

    pl2 = myprimers.PrimerList(primer_source)
    pl3 = myprimers.PrimerList(path=primers)

    assert pl1 == pl2 == pl3

    newlist = parse_primers(
        """
        >abc
        aaa
        >efg
        ttt
        """
    )

    np = pl2.assign_numbers(newlist)
    assert [s.name for s in parse_primers(np)] == ["5_abc", "4_efg"]

    newlist = parse_primers(
        """
        >abc
        aaa
        >efg
        tttttttt
        """
    )

    np = pl2.assign_numbers(newlist)
    assert [s.name for s in parse_primers(np)] == ["4_abc", "0_primer"]

    with pytest.raises(ValueError):
        pl2.pydna_code_from_list(newlist)

    captured = capsys.readouterr()
    assert captured.out == ">abc 3-mer\naaa\n\n"

    code = textwrap.dedent(
        """\
        from pydna.parsers import parse_primers

        p = {}

        p[0], p[1], p[2], p[3] = parse_primers('''

        >0_primer 8-mer
        tttttttt

        >1_primer 8-mer
        gggggggg

        >2_primer 8-mer
        cccccccc

        >3_primer 8-mer
        aaaaaaaa

        ''')"""
    )

    assert pl1.pydna_code_from_list(pl1) == code

    subp = mock.MagicMock()
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.setattr("subprocess.run", subp)

    pl3.open_folder()
    subp.assert_called_with(["xdg-open", primers.parent])
