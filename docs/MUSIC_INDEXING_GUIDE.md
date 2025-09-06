# Music Library Indexing Guide

This guide shows how to use the `music_indexer.py` tool to index your music collection for the Party Memory Wall application.

## Quick Start

To reindex your entire music library:

```bash
cd /home/kdresdell/Documents/DEV/PartyWall
python music_indexer.py
```

This will scan `/mnt/media/MUSIC` and index all your music files (~30 minutes for 3,000+ files).

## Common Commands

### Full Library Reindex
```bash
python music_indexer.py
```
- Scans entire `/mnt/media/MUSIC` directory
- Includes AI embeddings (slow but better search)
- Takes 20-30 minutes for large libraries

### Fast Reindex (Skip AI)
```bash
python music_indexer.py --skip-embeddings
```
- Much faster (5-10 minutes)
- Still enables full search functionality
- Good for testing or quick updates

### Custom Library Path
```bash
python music_indexer.py --library /path/to/your/music
```

### Test With Limited Files
```bash
python music_indexer.py --max-files 100
```
- Only indexes first 100 files
- Good for testing after reorganizing

### Test Search After Indexing
```bash
python music_indexer.py --test-search "pearl jam"
```
- Runs indexing then tests search
- Useful to verify everything works

## When to Reindex

**Always reindex after:**
- Adding new albums/songs
- Cleaning up duplicates
- Reorganizing folder structure
- Moving music files
- Before the party (to ensure everything is fresh)

**You don't need to reindex for:**
- Changing app settings
- Updating other parts of the application

## Monitor Progress

### Check Progress While Running
```bash
tail -f music_indexer.log
```

### Check How Many Songs Indexed
```bash
sqlite3 database/party.db "SELECT COUNT(*) FROM music_library;"
```

### See Recently Indexed Songs
```bash
sqlite3 database/party.db "SELECT artist, title FROM music_library ORDER BY id DESC LIMIT 10;"
```

## Clear and Start Fresh

If you want to completely reindex (clear old data):

```bash
# Stop any running indexer
pkill -f music_indexer.py

# Clear the music database
sqlite3 database/party.db "DELETE FROM music_library;"
sqlite3 database/party.db "DELETE FROM music_search;"

# Start fresh indexing
python music_indexer.py
```

## Troubleshooting

### "ModuleNotFoundError"
Install missing dependencies:
```bash
pip install --break-system-packages mutagen
```

### "Permission Denied"
Make sure you can access your music directory:
```bash
ls /mnt/media/MUSIC
```

### Indexing Too Slow
Use fast mode:
```bash
python music_indexer.py --skip-embeddings
```

### Check If Indexing Is Running
```bash
ps aux | grep music_indexer
```

### Kill Running Indexer
```bash
pkill -f music_indexer.py
```

## File Support

The indexer supports these formats:
- **MP3** (.mp3)
- **M4A** (.m4a) 
- **WAV** (.wav)
- **FLAC** (.flac)
- **OGG** (.ogg)

## Directory Structure

The indexer works best with organized folders like:
```
/mnt/media/MUSIC/
├── Artist Name/
│   ├── Album Name/
│   │   ├── 01 Track Name.mp3
│   │   └── 02 Another Track.mp3
│   └── Another Album/
└── Another Artist/
```

But it also handles loose files and various naming patterns.

---

## Example Workflow

**After cleaning up your music library:**

1. **Clear old index:**
   ```bash
   sqlite3 database/party.db "DELETE FROM music_library;"
   ```

2. **Start fresh indexing:**
   ```bash
   python music_indexer.py --skip-embeddings
   ```

3. **Monitor progress:**
   ```bash
   tail -f music_indexer.log
   ```

4. **Test search:**
   ```bash
   # Go to http://localhost:8000/upload and search for your favorite artist
   ```

5. **Party ready!** 🎉

---

**Note**: The Flask server (`python app.py`) should be running for music search to work in the web interface.