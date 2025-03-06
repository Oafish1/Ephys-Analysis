# %%
%load_ext autoreload
%autoreload 2

# %%
from itertools import product
import os

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats
import seaborn as sns

from hiEEG_functions import *

# Style
sns.set_theme(context='talk', style='white', palette='Set2')
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42

# %% [markdown]
# # iEEG Macroelectrode Data (4kHz)

# %%
# folder='./data/hiEEG'
# folder = "D:/DaifengWangLab/ePhys/dandiset_000574/000574"  # Windows
folder = "/mnt/d/DaifengWangLab/data/dandiset_000574/000574"  # WSL

# Load file manually
# file_string = f'Data_Subject_{1:02d}_Session_{1:02d}'
# f = h5py.File(os.path.join(folder, file_string) + '.h5', 'r')

# Load file automatically
data, meta = load_iEEG_macro(1, 1, folder=folder)

# %% [markdown]
# ## Visualize

# %%
# TODO: Plot brain coordinates
# Set variables
trial_num = 0
time, waveform, electrode_names = data[trial_num]['time'], data[trial_num]['waveform'], data[trial_num]['electrodes']
set_size, correct, response_time = meta[trial_num]['set_size'], meta[trial_num]['correct'], meta[trial_num]['response_time']
df = (
    pd.DataFrame(waveform, index=electrode_names, columns=time)
        .reset_index(names='Electrode')
        .melt(id_vars='Electrode', var_name='Time (s)', value_name='Voltage (μV)')
)

# Make figure
scale = 4
split = int(48/8)  # How many sections?
fig, axs = plt.subplot_mosaic([4*[i] + 2*[i+1] for i in range(0, split*2, 2)], figsize=(scale*4, scale*split))  # sharex=True
# Share x across all vertically stacked plots
[axs[i].sharex(axs[i+2]) for i in range(0, (split*2)-2, 2)]
[axs[(i+1)].sharex(axs[(i+1)+2]) for i in range(0, (split*2)-2, 2)]

# Plot
for i in range(0, split*2, 2):
    # Variables
    last = i == split*2-2

    # Filter to electrodes
    df_filtered = df.loc[df['Electrode'].map(lambda x: x in electrode_names[int(i/2*electrode_names.shape[0]/split):int((i/2+1)*electrode_names.shape[0]/split)])]

    # Regular plot
    plt.sca(axs[i])
    sns.lineplot(
        data=df_filtered,
        x='Time (s)',
        y='Voltage (μV)',
        hue='Electrode',
        ax=axs[i])
    if not last: axs[i].set_xlabel(None)

    # Zoomed plot
    sns.lineplot(
        data=df_filtered.loc[(df_filtered['Time (s)'] >= 0) * (df_filtered['Time (s)'] <= 1)],
        x='Time (s)',
        y='Voltage (μV)',
        hue='Electrode',
        legend=False,
        ax=axs[i+1])
    if not last: axs[i+1].set_xlabel(None)
    axs[i+1].set_ylabel(None)
    axs[i+1].set_yticks([])

    # Share y axis
    axs[i].sharey(axs[i+1])

    # Title based on meta
    if i == 0:
        axs[i].set_title(f'Set Size ({int(set_size):d}); Correct ({int(correct):d}); Response Time ({response_time:.3f})')
        axs[i+1].set_title('Zoomed')

# Formatting
plt.tight_layout()

# %% [markdown]
# # iEEG Microelectrode Data (32kHz)

# %%
# folder='./data/hiEEG/000574'
# folder = "D:/DaifengWangLab/ePhys/dandiset_000574/000574"  # Windows
folder = "/mnt/d/DaifengWangLab/data/dandiset_000574/000574"  # WSL

# Load file manually
# file_string = f'sub-01/sub-01_ses-20161214T173600_behavior+ecephys.nwb'
# nwbfile = pynwb.NWBHDF5IO(os.path.join(folder, file_string), mode='r').read()

# Load file automatically
micro_data, micro_meta = load_iEEG_micro(1, 2, folder=folder)

# %%
# # Check regions across all subjects and trials
# i = 1
# regions = []
# while True:
#     j = 1
#     while True:
#         try: micro_data, micro_meta = load_iEEG_micro(i, j, folder=folder)
#         except: break
#         if i + j > 2: print('; ', end='')
#         print(f'Processing {i}-{j}', end='')
#         regions += list(micro_data['electrode_regions'])
#         j += 1

#     if j == 1: break
#     i += 1

# # Print counts
# unique, counts = np.unique([s.split(', ')[0] for s in regions], return_counts=True)
# for un, co in zip(unique, counts):
#     print(f'{un}: {co}')

# TODO: Noah: please rerun and update the counts, especially missing Amyg
# # FuG: 127
# # Hipp: 355
# # INS: 11
# # IPL: 5
# # ITG: 135
# # MTG: 695
# # PhG: 89
# # STG: 111
# # pSTS: 5
# # unspecific: 831


# summary
reg_translation = {
    'Amyg': 'Amygdala',   # ??
    'FuG': 'Fusiform Gyrus',  # 127
    'Hipp': 'Hippocampus',  # 355
    'INS': 'Insular Gyrus',  # 11
    'IPL': 'Inferior Parietal Lobule',  # 5
    'ITG': 'Inferior Temporal Gyrus',  # 135
    'MTG': 'Middle Temporal Gyrus',  # 695
    'PhG': 'Parahippocampal Gyrus',  # 89
    'STG': 'Superior Temporal Gyrus',  # 111
    'pSTS': 'posterior Superior Temporal Sulcus',  # 5
}

# %% [markdown]
# ## Visualize

# %% [markdown]
# ### Electrode Location

# %%
# Show electrode positions colored by spike
fig = plt.figure(figsize=(18, 9))
ax = fig.add_subplot(1, 2, 1, projection='3d')
for idx in range(int(micro_data['electrodes'].shape[0] / 8)):
    filtered_data = micro_data['electrode_positions'][idx*8:(idx+1)*8]
    ax.scatter(*filtered_data.T, label=micro_data['electrodes'][idx*8][:-1], s=50)
ax.legend()
ax.set_title('Electrode Positions (Spike)')
ax.set_xlabel('x'); ax.set_ylabel('y'); ax.set_zlabel('z')
ax.set_box_aspect(aspect=None, zoom=1.)
ax.view_init(elev=25, azim=300)

# Show electrode
# TODO: Noah: add unit of coorrinates
ax = fig.add_subplot(1, 2, 2, projection='3d')
labels = micro_data['electrode_major_regions']
for label in np.unique(labels):
    mask = labels == label
    filtered_data = micro_data['electrode_positions'][mask]
    ax.scatter(*filtered_data.T, label=label, s=50)
ax.legend(ncols=2)
ax.set_title('Electrode Positions (Major Region)')
ax.set_xlabel('x'); ax.set_ylabel('y'); ax.set_zlabel('z')
ax.set_box_aspect(aspect=None, zoom=1.)
ax.view_init(elev=10, azim=100)

# %% [markdown]
# ### Waveform

# %%
# Plot individual
idx = list(range(int(.01 * 32_000)))
df = pd.DataFrame(micro_data['waveform'][idx], index=pd.Series(micro_data['time'][idx], name='Time (s)'), columns=micro_data['electrodes'])
df = df.reset_index().melt(id_vars='Time (s)', var_name='Electrode', value_name='Voltage (μV)')
step = 8
for i in range(0, micro_data['waveform'].shape[1], step):
    fig, ax = plt.subplots(1, 1, figsize=(18, 9))
    df_filtered = df.iloc[[s in list(micro_data['electrodes'][i:i+8]) for s in df['Electrode']]]
    sns.lineplot(df_filtered, x='Time (s)', y='Voltage (μV)', hue='Electrode', ax=ax)
    plt.show()
    break  # Remove to show all groups

# Plot average
df = pd.DataFrame({'Time (s)': micro_data['time'], 'Average Voltage (μV)': micro_data['waveform'].mean(axis=1)})
idx = list(range(int(100 * 32_000)))
fig, ax = plt.subplots(1, 1, figsize=(18, 9))
sns.lineplot(df.iloc[idx], x='Time (s)', y='Average Voltage (μV)', ax=ax)
plt.show()

# %% [markdown]
# ### Magnitude Correlation

# %%
# Plot correlation heatmaps between magnitude and behavior
# Format waveforms into df
df = pd.DataFrame(
    micro_data['waveform'],
    index=micro_data['time'],
    columns=[f'{n} ({l})' for n, l in zip(micro_data['electrodes'], micro_data['electrode_regions'])])

# Label by trial
df['Trial'] = (
    np.arange(micro_meta['trial'].shape[0])
    .reshape(-1, 1)
    .repeat(int(df.shape[0] / micro_meta['trial'].shape[0]), axis=1)
    .flatten())

# Compute summary statistic
df = df.abs().groupby('Trial').max()
df = df.abs().groupby('Trial').mean()
# df = df.abs().groupby('Trial').var()

# Add targets
df['Set Size'] = micro_meta['set_size']
df['Correct'] = micro_meta['correct']
df['Response Time'] = micro_meta['response_time']
targets = ['Set Size', 'Correct', 'Response Time']

# Compute correlation
# df_corr = df.corr()
# df_corr = df_corr.loc[~df_corr.index.isin(targets), targets].T
# label = 'corr'

# Compute p-value for pearson
df_corr = pd.DataFrame(index=df.loc[:, ~df.columns.isin(targets)].columns, columns=targets)
for ind, col in product(df_corr.index, df_corr.columns):
    mask = (~df[ind].isna() * ~df[col].isna()).to_numpy()
    if mask.sum() > 1:
        _, p = scipy.stats.pearsonr(df[ind].to_numpy(), df[col].to_numpy())
    else: p = 1
    df_corr.loc[ind, col] = p
label = 'p'
# Use FDR
pd.DataFrame(scipy.stats.false_discovery_control(df_corr.to_numpy().reshape(-1).astype(float)).reshape(df_corr.shape), index=df_corr.index, columns=df_corr.columns)
label = 'FDR'
# Apply -log10(p)
df_corr = df_corr.applymap(lambda x: -np.log10(x))
label = f'-log10({label})'

# Plot correlations
fig, ax = plt.subplots(1, 1, figsize=(27, 9))
# sns.heatmap(df_corr, vmin=-1, vmax=1, cmap=sns.color_palette('icefire', as_cmap=True), ax=ax)
# from matplotlib.colors import LogNorm
sns.heatmap(
    df_corr,
    vmin=0, vmax=3,
    # norm=LogNorm(),
    cmap=sns.color_palette('mako_r', as_cmap=True),
    cbar_kws={'label': label},
    ax=ax)
# plt.title(f'Session {session}')
plt.show()
