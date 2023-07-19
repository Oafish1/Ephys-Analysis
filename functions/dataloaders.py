from collections.abc import Sequence
import glob
import os
import tarfile

from kkpandas import kkio
import mat73
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
    """
    def __init__(self, directory, eeg=False, spk=True, samples=32, chunksize=100_000):
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
        self.eeg = eeg
        self.spk = spk
        self.samples = samples
        self.chunksize = chunksize

        # Crawl directory, extract base filenames as a list of strings in self.files
        # TODO: Check for folders,  .kkp file exist, then , then no need to check for .tar, we only need .k
        self.ext = '.tar.gz'
        self.files = os.listdir(self.directory)
        self.files = [
            ''.join(s.split('.')[:-2]) for s in self.files
            if os.path.isfile(os.path.join(self.directory, s))
            and (s.split('.')[-1] not in ['mat', 'xml'])
            and (s.split('.')[0][-4:] not in ['_eeg', '_spk'])
            and (s.split('.')[0] != 'NoveltySessInfoMatFiles')]

    def extract(self, index):
        # Return early if extracted
        # TODO: Add checks for eeg and spk, as well as incomplete extraction
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
        # Preliminary
        self.extract(index)

        # Novel spatial info
        novel = mat73.loadmat(os.path.join(self.directory, self.files[index], self.files[index] + '_sessInfo.mat'))

        # Get existing file if possible
        basename = os.path.join(self.directory, self.files[index], '*.kkp')
        memofile = glob.glob(basename)
        memofile = memofile[0] if memofile else None
        if not memofile:
            kkio.from_KK(
                os.path.join(self.directory, self.files[index]),
                verify_unique_clusters=False,
                also_get_features=True,
                also_get_waveforms=self.spk,
                n_samples=self.samples,
                fs=20_000,  # in seconds
                load_memoized=True,
                save_memoized=True)
        data = pd.read_csv(memofile, iterator=True, chunksize=self.chunksize)

        return novel, data

    def __len__(self):
        return len(self.files)


# # Individual ephys loader
# class Dataloader(Sequence):
#     def __init__(self, directory, eeg=False, spk=True):
#         self.directory = directory
#         self.basefile = os.path.basename(self.directory)
#         self.eeg = eeg
#         self.spk = spk

#         # Crawl directory
#         self.ftypes = ['clu', 'fet', 'spk']
#         self.files = os.listdir(directory)
#         fnums = [int(s.split('.')[2]) for s in self.files if (s.split('.')[-2] in ['clu'])]
#         self.num_files = len(fnums)

#     def __getitem__(self, index):
#         return kkio.from_KK(self.directory, verify_unique_clusters=False, also_get_features=True, also_get_waveforms=True, n_samples=32)

#     def __len__(self):
#         return len(self.num_files)
