### 2023-08-10
- Add capability to extract to and source from different locations
- Add correlation analysis to example and visualization
- Fix saved file read indexing
- Revise example data aggregation strategy

### 2023-08-02
- Additional testing
- Change example data to include fuller ephys feature
- Revise example loading strategy

### 2023-07-21
- Add detection for folders with no associated tar file
- Add indexing by session name
- Add saving functionality for individual groups
- Re-added sub-dataloader structure
- Revise example to show only one group
- Revise loader behavior to load singular groups
- Use REGEX for file-grabbing

### 2023-07-19 (3)
- Up sample size
- Additional parameters for `Tarloader`

### 2023-07-19 (2)
- Enhanced notebook example

### 2023-07-19 (1)
- Recompilation

### 2023-07-14 (1-2)
- Notebook annotations
- QOL updates

### 2023-07-12 (2)
- Add running Windows script
- Fix `Tarloader` use of `glob`

### 2023-07-12 (1)
- Fix `memoize` functions using `pandas` for `KKPandas`
- QOL dataloader changes
- Revise dataloader to use chunks
- Sample visualization

### 2023-07-11
- Added `KKPandas` library
- Initial commit
- Made `KKPandas` compatible with Python 3 and Windows paths
- Refactor
- Remove subloader in favor of `KKPandas`
- Revise `Tarloader`
