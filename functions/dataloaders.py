from collections.abc import Sequence
import os
import tarfile

from kkpandas import kkio
import mat73


# Tarfile loader
class Tarloader(Sequence):
    """
    Loader for ephys files providing on-the-fly extraction.  crcns/hc-11 formatting
    """
    def __init__(self, directory, eeg=False, spk=True):
        # eeg does nothing right now
        assert not eeg, 'eeg is not working at the moment.'

        self.directory = directory
        self.eeg = eeg
        self.spk = spk

        # Crawl directory
        self.ext = '.tar.gz'
        self.files = os.listdir(self.directory)
        self.files = [
            ''.join(s.split('.')[:-2]) for s in self.files
            if os.path.isfile(os.path.join(self.directory, s))
            and (s.split('.')[-1] not in ['mat', 'xml'])
            and (s.split('.')[0][-4:] not in ['_eeg', '_spk'])
            and (s.split('.')[0] != 'NoveltySessInfoMatFiles')]

        # Set empty items for storage
        self.dataloaders = []

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

        # Get vars
        novel = mat73.loadmat(os.path.join(self.directory, self.files[index], self.files[index] + '_sessInfo.mat'))
        data = kkio.from_KK(
            os.path.join(self.directory, self.files[index]),
            verify_unique_clusters=False,
            also_get_features=True,
            also_get_waveforms=True,
            n_samples=32,
            fs=20_000 / 1_000,  # in ms
            load_memoized=False,
            save_memoized=False)

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
