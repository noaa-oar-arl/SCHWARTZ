# Instructions

- To use first edit any of the files with the correct username

- Edit email address in bash_profile to your NOAA email address

- Use machine-specific configurations through one of two methods:

## 1. Using install_config.py (Recommended)

```bash
# From the main dotfiles directory:
./install_config.py -m machine
```

## 2. Directly using install_bash.sh

```bash
# From the bash directory:
./install_bash.sh machine
```

Here `machine` can be:
- `hera` - for NOAA Hera system
- `orion` - for MSU Orion system
- `gaea` - for NOAA Gaea system
- `ursa` - for NOAA Ursa system
- `mac` - for macOS systems
- (others as found in the machines directory)

The machine-specific configuration will be copied to your home directory as `.bash_site` and will be automatically sourced by your `.bash_profile`.

