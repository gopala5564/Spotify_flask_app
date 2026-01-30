# Spotify API Rate Limiting Solutions

## Problem
You may encounter HTTP 403 errors when fetching audio features for large batches of tracks. This is due to Spotify's API rate limiting.

## Solution
The scraper includes built-in rate limiting controls that can be adjusted based on your usage.

## Configuration Settings

Located in `.env` file:

```env
# Delay between individual API requests (seconds)
API_DELAY_BETWEEN_REQUESTS=1.5

# Delay between batch operations (seconds)
API_DELAY_BETWEEN_BATCHES=2.0

# Tracks per audio features request (max 100)
AUDIO_FEATURES_BATCH_SIZE=50

# Concurrent playlist fetch threads
PLAYLIST_FETCH_MAX_WORKERS=3
```

## Troubleshooting Guide

### If You Get HTTP 403 Errors:

**Step 1: Increase delays** (most effective)
```env
API_DELAY_BETWEEN_REQUESTS=2.5
API_DELAY_BETWEEN_BATCHES=3.0
```

**Step 2: Reduce batch size**
```env
AUDIO_FEATURES_BATCH_SIZE=30  # Reduce from 50
```

**Step 3: Reduce concurrent workers**
```env
PLAYLIST_FETCH_MAX_WORKERS=1  # Reduce from 3
```

**Step 4: Conservative settings** (if still having issues)
```env
API_DELAY_BETWEEN_REQUESTS=3.0
API_DELAY_BETWEEN_BATCHES=4.0
AUDIO_FEATURES_BATCH_SIZE=20
PLAYLIST_FETCH_MAX_WORKERS=1
```

## Script Features to Handle Rate Limiting

1. **Exponential Backoff**: Automatically retries failed requests with increasing delays (2s, 4s, 8s)
2. **Smaller Batch Fallback**: If standard batch size fails, automatically retries with smaller batches
3. **Retry Logic**: Up to 3 retry attempts per batch
4. **Progress Tracking**: Shows which batches succeed/fail
5. **Graceful Degradation**: Continues even if some audio features fail

## Expected Performance

With default settings (500 playlists):
- Time: 50-90 minutes
- Audio features fetched successfully: 95%+

With conservative settings:
- Time: 2-3 hours
- Audio features fetched successfully: 99%+

## Tips for Success

✓ Run during off-peak hours (late night, early morning)
✓ Start with conservative settings if first run fails
✓ Don't restart immediately if you get 403 - wait 15-30 minutes
✓ Use database query tool to explore data while scraping

## Resume Failed Downloads

If the script fails mid-way:
1. Data already fetched is saved to the database
2. You can query existing data while re-running
3. Re-running will skip duplicate playlists
4. Audio features will be fetched for new tracks only

## Alternative: Disable Audio Features

If you want to skip audio features entirely (fastest option):

Edit `.env`:
```env
# Add to .env
FETCH_AUDIO_FEATURES=False
```

Or edit `src/spotify_scraper/config.py`:
```python
FETCH_AUDIO_FEATURES = False
```

This allows you to fetch playlist and track data in ~10-15 minutes!

## Contact Spotify

If you consistently hit rate limits with reasonable delays:
1. Check your quota usage at https://developer.spotify.com/dashboard
2. Consider applying for extended access
3. Join Spotify Developer Community for support

## More Information

- [Spotipy Rate Limiting](https://spotipy.readthedocs.io/)
- [Spotify Web API Rate Limits](https://developer.spotify.com/documentation/web-api/concepts/rate-limits)
- [Best Practices](https://developer.spotify.com/documentation/web-api/concepts/api-limits)
