# Storage Configuration - SSD & Drive Mounting

This document describes the storage setup for optimizing performance and managing disk space.

## Current Disk Status

From `df -h` output:
- **C:\ (Windows)**: 195G total, 195G used (100% - FULL!) ⚠️
- **D:\ (Windows)**: 282G total, 3.3G used (2% available) ✅
- **SSD (/dev/sdd)**: 1007G total, 36G used (4% available) ✅ - Used as WSL root

## Configuration Changes Made

### 1. Dashboard App (`app.py`)

**Changes:**
- `BACKUP_DIR`: Changed from `WORKSPACE_ROOT / "backups"` to `Path("/backups")`
  - Backups are now stored on SSD for better performance
- `ARCHIVE_ROOT`: Changed from `/home/manoj/ArchiveWorkspaces` to `/mnt/d/ArchiveWorkspaces`
  - Archived projects now stored on D drive (more space available)

### 2. Docker Compose (`docker-compose.yml`)

**Changes:**
- Web service now mounts:
  - `/mnt/c:/host/c:ro` - Read-only access to C drive
  - `/mnt/d:/host/d` - Read-write access to D drive for new storage
  - `/backups:/host/backups` - SSD backup directory

- Database services now use SSD bind mounts:
  - PostgreSQL: `/data/postgres:/var/lib/postgresql/data`
  - MySQL: `/data/mysql:/var/lib/mysql`
  - MongoDB: `/data/mongodb:/data/db`
  - Redis: `/data/redis:/data`

### 3. Bootstrap Script (`bootstrap.sh`)

**New setup steps:**
- Creates SSD directories: `/data/postgres`, `/data/mysql`, `/data/mongodb`, `/data/redis`, `/backups`
- Creates D drive archive directory: `/mnt/d/ArchiveWorkspaces`
- Sets proper permissions for user access

## Storage Strategy

### SSD (/dev/sdd - Root Filesystem)
- **Purpose**: Performance-critical operations
- **Contents**:
  - Database storage (PostgreSQL, MySQL, MongoDB, Redis)
  - Backups (`/backups`)
  - Current workspace (`/home/manoj/DevWorkspaces`)
  - System logs and temporary files

### D Drive (/mnt/d)
- **Purpose**: New storage for large files and archives
- **Contents**:
  - Archived projects (`/mnt/d/ArchiveWorkspaces`)
  - Large datasets
  - Media files
  - Build artifacts

### C Drive (/mnt/c - Read Only)
- **Purpose**: Access to existing Windows files (read-only for safety)
- **Contents**:
  - Existing projects
  - Documents
  - Configuration files
- **Note**: C drive is FULL - DO NOT write to it!

## Commands to Run After Changes

### 1. Create SSD directories (run once):
```bash
sudo mkdir -p /data/postgres /data/mysql /data/mongodb /data/redis /backups
sudo chown -R $USER:$USER /data /backups
```

### 2. Create D drive archive directory:
```bash
mkdir -p /mnt/d/ArchiveWorkspaces
```

### 3. Recreate Docker containers with new volumes:
```bash
docker-compose down
docker-compose up -d
```

### 4. Run bootstrap to set up environment:
```bash
./bootstrap.sh
```

## Memory Management

The app includes built-in memory management features:

1. **Auto-refresh**: Dashboard refreshes every 30 seconds
2. **Storage Alerts**: Triggers at 80% disk usage
3. **Cleanup Functions**: 
   - `cleanup_old_logs()` - Archives old log files
   - `cleanup_old_backups()` - Removes backups older than 30 days
4. **Health Monitoring**: Tracks CPU, memory, and disk usage

## Recommendations

1. **Immediate**: Clean up C drive - it's at 100%!
2. **Short-term**: Move large files to D drive
3. **Ongoing**: 
   - Use `/backups` for all backup operations
   - Archive old projects to `/mnt/d/ArchiveWorkspaces`
   - Monitor SSD health with `df -h` and `smartctl`

## Verification Commands

Check current storage:
```bash
# Overall disk usage
df -h

# Check specific mounts
df -h /mnt/c
df -h /mnt/d
df -h /

# Directory sizes
du -sh /data/*
du -sh /backups/*
du -sh /mnt/d/ArchiveWorkspaces/*
```

## Troubleshooting

### If D drive not accessible:
```bash
# Check if D drive is mounted
ls -la /mnt/d

# If not mounted, mount it manually
sudo mount -t drvfs D: /mnt/d
```

### If SSD directories don't exist:
```bash
# Create them
sudo mkdir -p /data/postgres /data/mysql /data/mongodb /data/redis /backups
sudo chown -R $USER:$USER /data /backups
```

### If Docker containers fail to start:
```bash
# Check container logs
docker-compose logs postgres
docker-compose logs mysql

# Ensure directories exist and have correct permissions
ls -la /data/
ls -la /backups/
```

