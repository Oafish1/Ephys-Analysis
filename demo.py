from functions import Tarloader
from tqdm import tqdm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
# %%

# Make Dataloader
# tl = Tarloader('./data/hc-11/data/')
# tl = Tarloader('G:/My Drive/DaifengWangLab/data/hc-11/data', spk=False)
# tl = Tarloader('G:/My Drive/DaifengWangLab/data/hc-11/data')
tl = Tarloader('G:/My Drive/DaifengWangLab/data/hc-11_Buddy_06272013/data')
# Show available files
print(tl.files)
# Extract session 0 (Will extract files if required, then process.  Can take up to 15 minutes)
novel, data = tl[0]  # e.g., tl[0] is loading for the whole session Buddy_06272013

# %%
# Create df
df = pd.DataFrame(columns=['time', 'feature', 'position'])

# Append data
subsample = 10_000
timestamps = novel['sessInfo']['Position']['TimeStamps']
timestamps = np.repeat(np.expand_dims(timestamps, axis=-1), tl.chunksize / subsample, axis=1).T

# each row of data has 289=4+29+256 columns for Buddy_06272013, which includes time, feature0, ..., feature28, wf0, ..., wf255
# need to understand how many neurons are corresponding to the wf001 and wf255.
for i, chunk in tqdm(enumerate(data)):
    time = chunk['time'][::subsample]  # if  / 1000, then time is in seconds
    feature = chunk['feature0'][::subsample]
    # Get index of closest time
    idx = np.argmin(np.abs(timestamps - np.expand_dims(time, axis=-1)), axis=-1)
    position = novel['sessInfo']['Position']['OneDLocation'][idx]
    # Append
    # List append really isn't any faster
    add = pd.DataFrame({
        'time': time,
        'feature': feature,
        'position': position,
    })
    df = pd.concat([df, add])

# %%
print(f'{df.shape=}')  # (1616, 3)
print(f'{chunk.shape=}')
df
chunk

# %% [markdown]
# ### Plot Series

# %%
df.to_csv('./temp.csv')
# df = pd.read_csv('./temp.csv')

sns.set_theme(context='paper', style='white', palette='Set2')

# Plot subsampled series
fig = plt.figure(figsize=(16, 4))
axs = fig.subplot_mosaic('AAA.;BBBC')
axs['A'].get_shared_x_axes().join(axs['A'], axs['B'])
sns.lineplot(data=df, x='time', y='feature', ax=axs['A'])
sns.despine(ax=axs['A'])
axs['A'].set_xlabel(None)
sns.lineplot(data=df, x='time', y='position', color=sns.color_palette()[1], ax=axs['B'])
sns.despine(ax=axs['B'])
sns.lineplot(data=df.loc[~pd.isna(df['time'])], x='time', y='position', color=sns.color_palette()[1], ax=axs['C'])
sns.despine(ax=axs['C'])

# %%
