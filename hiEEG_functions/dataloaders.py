import os
import warnings

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
    session_string = f'Data_Subject_{subject:02d}_Session_{session:02d}'
    file_string = session_string + '.h5'

    # Load file
    f = h5py.File(os.path.join(folder, file_string), 'r')

    # Extract data
    data, meta = [], []
    data_arrays = f['data'][session_string]['data_arrays']
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
            'response_time': response_time,
        })

    # Return
    return data, meta, file_string


def load_iEEG_micro(subject, session, folder='data/hiEEG', format='old'):
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
    # Arguments
    format_types = ('old', 'new')
    assert format in format_types, f'Unknown format type "{format}", expected one of {format_types}'

    # Formatting
    file_string = f'sub-{subject:02d}/'
    file_string = os.path.join(
        file_string,
        os.listdir(os.path.join(folder, file_string))[session-1]
    )

    # Load file
    nwbfile = pynwb.NWBHDF5IO(os.path.join(folder, file_string), mode='r').read()

    # Extract data
    if format == 'old':
        micro_data = nwbfile.processing['ecephys'].data_interfaces['LFP'].electrical_series['ecephys.lfp'].data[:]
        micro_time = nwbfile.processing['ecephys'].data_interfaces['LFP'].electrical_series['ecephys.lfp'].timestamps[:]
        micro_electrodes = nwbfile.processing['ecephys'].data_interfaces['LFP'].electrical_series['ecephys.lfp'].electrodes[:]
    elif format == 'new':
        micro_data = nwbfile.acquisition['ecephys.lfp'].data[:]
        micro_time = nwbfile.acquisition['ecephys.lfp'].timestamps[:]
        micro_electrodes = nwbfile.acquisition['ecephys.lfp'].electrodes[:]
    reg_translation = {
        'Amyg': 'Amygdala',
        'FuG': 'Fusiform Gyrus',
        'Hipp': 'Hippocampus',
        'INS': 'Insular Gyrus',
        'IPL': 'Inferior Parietal Lobule',
        'ITG': 'Inferior Temporal Gyrus',
        'MTG': 'Middle Temporal Gyrus',
        'PhG': 'Parahippocampal Gyrus',
        'STG': 'Superior Temporal Gyrus',
        'pSTS': 'posterior Superior Temporal Sulcus',
    }
    electrode_major_regions = np.array([
        reg_translation[loc.split(', ')[0]]
        if loc.split(', ')[0] in reg_translation
        else loc.split(', ')[0]
        for loc in micro_electrodes['location'].to_numpy()])
    lateral = np.array([
        loc.split(', ')[1].split(' ')[0]
        if len(loc.split(', ')) > 1 else None
        for loc in micro_electrodes['location'].to_numpy()])
    electrode_major_lateral_regions = np.array([
        ' '.join([s for s in (lat, loc) if s is not None])
        for lat, loc in zip(lateral, electrode_major_regions)])
    data = {
        'time': micro_time,
        'waveform': micro_data,
        'electrodes': micro_electrodes['label'].to_numpy(),
        'electrode_positions': micro_electrodes[['x', 'y', 'z']].to_numpy(),
        'electrode_regions': micro_electrodes['location'].to_numpy(),
        'electrode_major_regions': electrode_major_regions,
        'electrode_major_lateral_regions': electrode_major_lateral_regions,
    }

    # Extract meta
    # NOTE: Is `micro_answers` correct?  For 1-1 it is all false
    micro_trials = nwbfile.trials[:]
    if format == 'old':
        micro_answers = nwbfile.processing['behavior'].data_interfaces['BehavioralEvents.response'].time_series['response'].data[:]
        micro_correct = micro_answers == micro_trials['solution'].to_numpy()
        micro_answers_time = nwbfile.processing['behavior'].data_interfaces['BehavioralEvents.response'].time_series['response'].timestamps[:]
    elif format == 'new':
        micro_correct = nwbfile.trials[:]['correct'].to_numpy().astype(bool)
        micro_answers_time = nwbfile.trials[:]['response_time'].to_numpy()
    meta = {
        'trial': micro_trials[['start_time', 'stop_time']].to_numpy(),
        'set_size': micro_trials['set_size'].to_numpy(),
        'correct': micro_correct,
        'response_time': micro_answers_time - (micro_trials['start_time'].to_numpy() + 6),
        'fname': file_string,
    }

    return data, meta


def detect_trials(time, waveform, eps=1e-5):
    assert time.shape[0] == waveform.shape[0], 'Time and waveform length must match.'

    # Detect gaps
    gaps = time[1:] - time[:-1]
    gaps = np.argwhere(gaps > np.min(gaps) + eps).flatten() + 1  # +1 to indicate the start of each segment, inclusive

    # Detect if evenly spaced
    segment_timesteps = gaps[0]
    if (segment_timesteps * (np.arange(gaps.shape[0])+1) == gaps).all() and gaps[-1] + segment_timesteps == time.shape[0]:
        new_time = time.reshape((-1, segment_timesteps))
        new_waveform = waveform.reshape((-1, segment_timesteps, waveform.shape[-1]))
    # If not, return list
    else:
        warnings.warn('Irregularly spaced input waveform, outputting list.')
        start_idx, end_idx = [0] + gaps.tolist(), gaps.tolist() + [time.shape[0]]
        new_time = [time[sidx:eidx]  for sidx, eidx in zip(start_idx, end_idx)]
        new_waveform = [waveform[sidx:eidx]  for sidx, eidx in zip(start_idx, end_idx)]
    return {'time': new_time, 'waveform': new_waveform}
