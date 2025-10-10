# ![icon](https://github.com/pydna-group/pydna-utils/blob/main/docs/_static/icon.png?raw=true)

pydna-utils is a package containing utilities for [pydna](https://github.com/pydna-group/pydna?tab=readme-ov-file) facilitating interactive use.

Install:

```bash
pip install pydna-utils
```

pydna_utils creates a settings file where links to useful data can be placed. The platformdirs package is used to decide 
where this file should be located. On my machine this is located at `/home/bjorn/.config/pydna/pydna_config.toml`.




```python
16:16 $ ipython
Python 3.12.7 (main, Nov 18 2024, 08:24:06) [GCC 11.4.0]
Type 'copyright', 'credits' or 'license' for more information
IPython 9.6.0 -- An enhanced Interactive Python. Type '?' for help.
Tip: You can use `files = !ls *.png`

In [1]: import pydna_utils

In [2]: pydna_utils.get_env()
Out[2]: 
+---------------+-----------------------------------------+
| Setting       | Value                                   |
+---------------+-----------------------------------------+
| pydna_ape_url | /usr/bin/tclsh /home/bjorn/.ApE/ApE.tcl |
| pydna_enzymes | /home/bjorn/.ApE/Enzymes/LGM_group.txt  |
| pydna_primers | /home/bjorn/myvault/PRIMERS.md          |
+---------------+-----------------------------------------+

In [3]: !tail -9 /home/bjorn/myvault/PRIMERS.md # This file contain primer sequences in a format that pydna can understand.

>2_3CYC1clon
CGATGTCGACTTAGATCTCACAGGCTTTTTTCAAG

>1_5CYC1clone
GATCGGCCGGATCCAAATGACTGAATTCAAGGCCG

>0_S1 67bp primer for amplification of GFP from pFA6a-GFPS65T-kanMX6. The last 21 bp are specific for the GFP gene in pFA6a-GFPS65T-kanMX6. The rest is homology with the 3'part of ScJEN1. This primer was used for tagging the JEN1 with GFP on the chromosome.
GATTCGAACGTCTCAAAGACATATGAGGAGCATATTGAGACCGTTAGTAAAGGAGAAGAACTTTTC

In [4]: from pydna_utils.myprimers import PrimerList

In [5]: pl = PrimerList()

In [6]: pl[1]
Out[6]: 1_5CYC1clone 35-mer:5'-GATCGGCCGGATCCA..CCG-3'

In [7]: type(pl[1])
Out[7]: pydna.primer.Primer

In [11]: cat /home/bjorn/.ApE/Enzymes/LGM_group.txt  # This text file contain restriction enzymes in an arbitrary format.
LGM {AatII  Acc65I  AflII  AjiI  BamHI  BglI  BglII  Bsp1407I  BspTI  BstXI  BsuRI  CaiI  CciNI  Eco147I  Eco31I  Eco32I  EcoRI  HindIII  KpnI  MluI  MnlI  MssI  NdeI  NotI  PacI  Pfl23II  PstI  PvuII  SacI  SalI  ScaI  SdaI  SgsI  SmaI  SmiI  StuI  XagI  XbaI  XhoI  XmaI  ZraI}

In [12]: from pydna_utils.myenzymes import myenzymes

In [13]: myenzymes
Out[13]: RestrictionBatch(['AatII', 'Acc65I', 'AflII', 'AjiI', 'BamHI', 'BglI', 'BglII', 'Bsp1407I', 'BspTI', 'BstXI', 'BsuRI', 'CaiI', 'CciNI', 'Eco147I', 'Eco31I', 'Eco32I', 'EcoRI', 'HindIII', 'KpnI', 'MluI', 'MnlI', 'MssI', 'NdeI', 'NotI', 'PacI', 'Pfl23II', 'PstI', 'PvuII', 'SacI', 'SalI', 'ScaI', 'SdaI', 'SgsI', 'SmaI', 'SmiI', 'StuI', 'XagI', 'XbaI', 'XhoI', 'XmaI', 'ZraI'])


In [13]: from pydna_utils import open_config_file

In [13]: open_config_file()  # opens the config file for editing in system text editor.

```
