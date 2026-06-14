# Flex Drive Setup (Zram Writeback)

Flex Drive allows zram devices to exceed physical RAM limits by using a physical backing store on the NVMe. This is ideal for heavy builds (Kodi) that need high-speed IO but occasionally spike in storage/memory usage.

## Setup Utility
A utility script `setup_flex_zram.sh` is provided to automate this.

### Configuration for llmadmin01 (Primary Heavy)
**Status:** ✅ Applied
- **Mount Point:** `/mnt/largedata/github_runners/work`
- **Backing File:** `/mnt/largedata/github_runners/workflex/zram_back`
- **RAM Limit:** 8G
- **Total Size:** 64G

### Configuration for T430 (Auxiliary Medium)
**Status:** ⏳ Pending (Action Required on Node)
- **Mount Point:** `/mnt/data/github_runners/work`
- **Backing File:** `/mnt/data/github_runners/workflex/zram_back`
- **RAM Limit:** 4G
- **Total Size:** 32G

#### Deployment on T430:
Run the following commands on the T430 host:

```bash
cd github_runners
# Stop runners to release mounts
cd T430 && docker-compose stop && cd ..

# Execute Flex Drive setup
sudo ./setup_flex_zram.sh \
  /mnt/data/github_runners/work \
  /mnt/data/github_runners/workflex/zram_back \
  4G \
  32G

# Restart runners
cd T430 && docker-compose up -d
```

## How it works
1. **RAM-First**: Data is compressed in RAM (up to the `RAM Limit`).
2. **Disk-Spill**: When the limit is reached or data is cold, zram moves pages to the sparse backing file on the physical disk via a loop device.
3. **Transparent**: The system sees a single large block device (e.g. 64G) with the performance of RAM for the most active data.
