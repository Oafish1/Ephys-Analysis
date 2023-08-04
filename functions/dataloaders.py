from collections import Iterable
from collections.abc import Sequence
import os
import re
import tarfile

from kkpandas import kkio
import mat73
import numpy as np
import pandas as pd


# Tarfile loader
class Tarloader(Sequence):
    """
    Loader for ephys files providing on-the-fly extraction.  crcns/hc-11 formatting
    Data is extracted on-the-fly, so the first call to __getitem__ will take a while.
    .tar.gz is expected to include the following file formats:
        .clu
        .fet
        .res
        .spk
        _sessioninfo.mat
    Data formarts refer to:
        https://crcns.org/data-sets/hc/hc-11/about-hc-11

    HC-11:
    Per spike, there are 32 samples recorded for 7-9 channels.  Samples appear to
    just be a way of characterizing the spikes.  The channels are per-group, as
    indicated by the file names.  The variance in time between spikes is a product of
    the preprocessing to get the raw data into spike format.  The EEG tar seems to
    contain the raw waveforms downsampled to 1250 Hz.  Don't use the 0 or 1 clusters,
    as those are noise and unclusterable units (wide spikes)
    """
    def __init__(self, directory, ext='.tar.gz', eeg=False, spk=True, samples=32, channels=-1, use_disk=True):
        # eeg does nothing right now
        """
        Args:
            directory (str): Directory containing tar.gz files
            eeg (bool): Extract eeg files
            spk (bool): Extract spk files
            samples (int): Number of samples to extract from spk files ?? XH: I guess this is the number of samples per spike
            chunksize (int): Number of rows of csv to load from the .kkp file at a time
        Usage:

        """
        assert not eeg, 'eeg is not working at the moment.'

        self.directory = directory
        self.ext = ext
        self.eeg = eeg
        self.spk = spk
        self.samples = samples
        self.channels = channels
        self.use_disk = use_disk  # Saves around 5/6 of time loading

        # Crawl directory
        self.files = os.listdir(self.directory)
        self.files = [f for f in self.files if re.search(r'[a-zA-Z]+_\d+(.tar.gz)?', f)]
        self.files = [f.replace(self.ext, '').replace('_eeg', '').replace('_spk', '') for f in self.files]
        self.files = list(np.unique(self.files))

    def extract(self, index):
        # Return early if extracted
        if self.files[index] in os.listdir(self.directory):
            return

        # Extract clu, fet
        with tarfile.open(os.path.join(self.directory, self.files[index] + self.ext), 'r:gz') as f:
            f.extractall(self.directory)

        # Extract eeg  # Unzip always errors out
        if self.eeg:
            with tarfile.open(os.path.join(self.directory, self.files[index] + '_eeg' + self.ext), 'r:gz') as f:
                f.extractall(self.directory)

        # Extract spk
        if self.spk:
            with tarfile.open(os.path.join(self.directory, self.files[index] + '_spk' + self.ext), 'r:gz') as f:
                f.extractall(self.directory)

    def __getitem__(self, index):
        # Index by session name
        if not isinstance(index, int):
            idx = np.argwhere(np.array(self.files) == index)
            if len(idx) < 1:
                raise IndexError(f'Index {index} not found')
            index = idx[0][0]

        # Preliminary
        self.extract(index)

        # Novel spatial info
        novel = mat73.loadmat(os.path.join(self.directory, self.files[index], self.files[index] + '_sessInfo.mat'))

        # Return dl
        return Dataloader(
            os.path.join(self.directory, self.files[index]),
            novel=novel,
            eeg=self.eeg,
            spk=self.spk,
            samples=self.samples,
            channels=self.channels,
            use_disk=self.use_disk,
        )

    def __len__(self):
        return len(self.files)


# Individual ephys loader
class Dataloader(Sequence):
    def __init__(self, directory, *, novel, eeg, spk, samples, channels, use_disk):
        self.directory = directory
        self.novel = novel
        self.eeg = eeg
        self.spk = spk
        self.samples = samples
        self.channels = channels
        self.use_disk = use_disk

        # Crawl directory
        files = os.listdir(directory)
        fnums = np.unique([int(f.split('.')[2]) for f in files if re.search(r'[a-zA-Z]+_\d+.(clu|res|fet|spk).\d+', f)])
        self.num_files = len(fnums)

    def __getitem__(self, index):
        # Get existing file if possible
        fname = os.path.join(self.directory, f'COMPILED_{index+1}.csv')
        if self.use_disk and os.path.isfile(fname):
            data = pd.read_csv(fname)

        # Process data
        else:
            data = kkio.from_KK(
                self.directory,
                groups_to_get=index+1,
                verify_unique_clusters=False,
                also_get_features=True,
                also_get_waveforms=self.spk,
                n_samples=self.samples,
                n_channels=self.channels,
                fs=20_000,  # in seconds
                load_memoized=False,
                save_memoized=False,
            )

            # Save file
            if self.use_disk:
                data.to_csv(fname)

        return self.novel, data

    def __len__(self):
        return self.num_files
