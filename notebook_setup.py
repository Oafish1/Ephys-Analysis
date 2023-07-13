from functions import Tarloader


# Make loader
tl = Tarloader('./data/hc-11/data/')

# Extract all
for i in range(len(tl)):
    print(f'Extracting {tl.files[i]}')
    tl.extract(i)

# Process all and produce memo files
print(f'Processing {tl.files[0]}')
for i, (novel, data) in enumerate(tl):
    if i+1 != len(tl): print(f'Processing {tl.files[i+1]}')
    del novel, data
