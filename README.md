# Dataloaders for Raw Electrophysiological Datasets

This repository contains several dataloaders intended for the easy processing and acquisition of data from several sources.

## Current Compatible Datasets
- [HC-11](https://pubmed.ncbi.nlm.nih.gov/27013730/)
- [Human iEEG](https://www.science.org/doi/10.1126/sciadv.aav3687)

## Installation
Installation may be done simply using a combination of `conda` and `pip`. First, initialize a conda environment:
```bash
# Python 3.9 tested, but likely to work with other versions as well
conda env -n ephys python=3.9
```

Then, install requirements using `pip`:
```bash
python -m pip install -r requirements.txt
```