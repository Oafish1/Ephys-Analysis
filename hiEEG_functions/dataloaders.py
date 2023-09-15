import os

import h5py
import numpy as np


def load_hiEEG_data(subject, session, folder='data/hiEEG'):
    "Load data for `subject` and `session` from `folder`"
    # Refer to https://gin.g-node.org/USZ_NCH/Human_MTL_units_scalp_EEG_and_iEEG_verbal_WM/src/master/code_MATLAB/Load_Data_Example_Script.m for structure
    # Formatting
    file_string = f'Data_Subject_{subject:02d}_Session_{session:02d}'

    # Load file
    f = h5py.File(os.path.join(folder, file_string) + '.h5', 'r')

    # Extract data
    data, meta = [], []
    data_arrays = f['data'][file_string]['data_arrays']
    trial_prefix = 'iEEG_Data_'
    trial_keys = [k for k in data_arrays.keys() if trial_prefix in k]
    for trial_key in trial_keys:
        # Setup
        sampling_meta = data_arrays[trial_key]['dimensions']['2'].attrs
        trial_meta = f['metadata']['Session']['sections']['Trial properties']['sections'][trial_key[len(trial_prefix):]]['properties']

        # Get data
        waveform = np.array(data_arrays[trial_key]['data'])
        time = np.arange(waveform.shape[1]) * sampling_meta['sampling_interval'] + sampling_meta['offset']
        electrode_names = np.array(data_arrays[trial_key]['dimensions']['1']['labels']).astype(str)

        # Get meta
        set_size = trial_meta['Set size'][0][0]
        correct = trial_meta['Correct'][0][0]
        response_time = trial_meta['Response time'][0][0]

        # Record
        data.append({'time': time, 'waveform': waveform, 'electrode_names': electrode_names})
        meta.append({'set_size': set_size, 'correct': correct, 'response_time': response_time})

    # Return
    return data, meta
