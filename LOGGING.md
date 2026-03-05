# Logging System

All application logs are now automatically captured to files for troubleshooting.

## Log Files Location

```
logs/
  ├── app.log          # Current log file
  ├── app.log.1        # Backup 1 (when current exceeds 10MB)
  ├── app.log.2        # Backup 2
  ├── app.log.3        # Backup 3
  ├── app.log.4        # Backup 4
  └── app.log.5        # Backup 5 (oldest)
```

## Log Rotation

- **Max file size:** 10MB per log file
- **Backup files:** 5 rotating backups are kept
- **Total storage:** ~60MB maximum for all logs

## View Logs

### View last 100 lines:
```bash
python view_logs.py
```

### Follow logs in real-time (like tail -f):
```bash
python view_logs.py -f
```

### View directly with terminal commands:
```bash
# View last 50 lines
tail -n 50 logs/app.log

# Follow in real-time
tail -f logs/app.log

# Search for errors
grep ERROR logs/app.log

# Search for specific request
grep "POST /upload" logs/app.log
```

## Log Format

Each log entry includes:
- **Timestamp:** `[2026-03-04 16:46:59]`
- **Log level:** `INFO`, `WARNING`, `ERROR`
- **Module:** Where the log originated
- **Message:** The actual log content

Example:
```
[2026-03-04 16:46:59] INFO in app: Starting Q&A Cleaner Server...
[2026-03-04 16:47:00] WARNING in app: AIBot setup test failed: ...
[2026-03-04 16:47:15] INFO in werkzeug: 127.0.0.1 - - "POST /upload HTTP/1.1" 200 -
```

## What Gets Logged

✅ **Application startup/shutdown**
✅ **HTTP requests** (GET, POST with status codes)
✅ **AIBot API calls** (success and failures)
✅ **File uploads and processing**
✅ **Errors and exceptions**
✅ **LLM processing decisions**
✅ **Configuration warnings**

## Troubleshooting Tips

### Check recent errors:
```bash
grep ERROR logs/app.log | tail -20
```

### Check recent warnings:
```bash
grep WARNING logs/app.log | tail -20
```

### Check AIBot API issues:
```bash
grep "AIBot" logs/app.log
```

### Check file upload issues:
```bash
grep "upload" logs/app.log -i
```

### Monitor live activity:
```bash
tail -f logs/app.log
```

## Log Levels

- **INFO:** Normal operation events
- **WARNING:** Potential issues (API key missing, fallback to rules, etc.)
- **ERROR:** Actual errors that need attention
