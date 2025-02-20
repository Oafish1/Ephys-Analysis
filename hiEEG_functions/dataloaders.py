import os

import h5py
import numpy as np
import pynwb


def load_iEEG_macro(subject, session, folder='data/hiEEG'):
    """
    Load data for `subject` and `session` from `folder`
    Data is INDEXED BY TRIAL

    NOTES
    -----
    Data is split into three categories:
    EEG Scalp Recordings (256Hz)
    *iEEG Macroelectrodes (Filtered to single-neuron) (4kHz)
    iEEG Microelectrodes/Depth electrodes (Filtered to single-neuron) (32kHz)
    """
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
        data.append({
            'time': time,
            'waveform': waveform,
            'electrodes': electrode_names
        })
        meta.append({
            'trial': None,
            'set_size': set_size,
            'correct': correct,
            'response_time': response_time
        })

    # Return
    return data, meta


def load_iEEG_micro(subject, session, folder='data/hiEEG'):
    """
    Load data for `subject` and `session` from `folder` for microelectrode data
    Data is CONTINUOUS

    NOTES
    -----
    Data is split into three categories:
    EEG Scalp Recordings (256Hz)
    iEEG Macroelectrodes (Filtered to single-neuron) (4kHz)
    *iEEG Microelectrodes/Depth electrodes (Filtered to single-neuron) (32kHz)

    It seems as if electrode locations are approximate, as they are the same across all sessions
    """
    # Formatting
    file_string = f'sub-{subject:02d}/'
    file_string = os.path.join(
        file_string,
        os.listdir(os.path.join(folder, file_string))[session-1]
    )

    # Load file
    nwbfile = pynwb.NWBHDF5IO(os.path.join(folder, file_string), mode='r').read()

    # Extract data
    micro_data = nwbfile.processing['ecephys'].data_interfaces['LFP'].electrical_series['ecephys.lfp'].data[:]
    micro_time = nwbfile.processing['ecephys'].data_interfaces['LFP'].electrical_series['ecephys.lfp'].timestamps[:]
    micro_electrodes = nwbfile.processing['ecephys'].data_interfaces['LFP'].electrical_series['ecephys.lfp'].electrodes[:]
    loc_translation = {
        'Hipp': 'Hippocampus',
        'STG': 'Superior Temporal Gyrus',
        'MTG': 'Middle Temporal Gyrus',
        'ITG': 'Inferior Temporal Gyrus',
        'INS': 'Insular Gyrus',
        'Amyg': 'Amygdala',
        'FuG': 'Fusiform Gyrus',
        'PhG': 'Parahippocampal Gyrus',
    }
    data = {
        'time': micro_time,
        'waveform': micro_data,
        'electrodes': micro_electrodes['label'].to_numpy(),
        'electrode_positions': micro_electrodes[['x', 'y', 'z']].to_numpy(),
        'electrode_regions': micro_electrodes['location'].to_numpy(),
        'electrode_major_regions': np.array([
            loc_translation[loc.split(', ')[0]]
            if loc.split(', ')[0] in loc_translation
            else loc.split(', ')[0]
            for loc in micro_electrodes['location'].to_numpy()]),
    }

    # Extract meta
    # NOTE: Is `micro_answers` correct?  For 1-1 it is all false
    micro_answers = nwbfile.processing['behavior'].data_interfaces['BehavioralEvents.response'].time_series['response'].data[:]
    micro_answers_time = nwbfile.processing['behavior'].data_interfaces['BehavioralEvents.response'].time_series['response'].timestamps[:]
    micro_trials = nwbfile.trials[:]
    meta = {
        'trial': micro_trials[['start_time', 'stop_time']].to_numpy(),
        'set_size': micro_trials['set_size'].to_numpy(),
        'correct': micro_answers == micro_trials['solution'].to_numpy(),
        'response_time': micro_answers_time - (micro_trials['start_time'].to_numpy() + 6)
    }

    return data, meta
