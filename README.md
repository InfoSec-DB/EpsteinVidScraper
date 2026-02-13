# 🔓 Epstein Files Scraper

> **Automated archival tool for publicly released Jeffrey Epstein court documents**

A two-stage scraper for downloading PDF documents and associated video files from the U.S. Department of Justice's public release of Jeffrey Epstein-related court documents and depositions.

**Made by: [CBKB] Deadly-Data**

---

## 🎯 Features

- **Resumable Downloads** - Automatic progress tracking via `progress.json`
- **Anti-Block Protection** - Dynamic cookie refresh using Selenium
- **Multi-threaded** - Concurrent downloads with configurable thread count
- **Video Detection** - Automatically finds `.mp4`, `.m4v`, `.mov`, `.webm`, `.avi` companions
- **Validation** - Size checks and content-type verification
- **Stealth Mode** - Undetected ChromeDriver bypasses automation detection

---

## 📋 Prerequisites
```bash
# System packages
sudo apt install curl python3 chromium-driver

# Python dependency
pip install undetected-chromedriver
```

---

## 🚀 Quick Start

### **Option 1: Use Provided JSON (Recommended)**

Download `cleaned_data.json` from this repo and skip to Step 3.

### **Option 2: Extract URLs Yourself**

**Step 1: Extract File Metadata (Browser Console)**

1. Navigate to: `https://www.justice.gov/multimedia-search?keys=no%20images%20produced`
2. Open browser console (`F12` → Console tab)
3. Paste and run this script:
```javascript
(async () => {
  const results = [];
  const totalPages = 380;
  const batchSize = 5;
  for (let i = 1; i <= totalPages; i += batchSize) {
    const batch = Array.from({ length: Math.min(batchSize, totalPages - i + 1) }, (_, j) => {
      const page = i + j;
      return fetch(`https://www.justice.gov/multimedia-search?keys=no%20images%20produced&page=${page}`)
        .then(r => r.json())
        .then(body => ({ page, body }));
    });
    const batchResults = await Promise.all(batch);
    results.push(...batchResults);
    console.log(`Pages ${i}-${i + batchResults.length - 1} done`);
  }
  results.sort((a, b) => a.page - b.page);
  const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'results.json';
  a.click();
})();
```

4. Wait for all 380 pages to download (~2-3 minutes)
5. Save as `cleaned_data.json`

**Step 2: Download Files (Python)**
```bash
# Make executable
chmod +x media_scraper.py

# Run with defaults (3 threads, 1s delay)
./media_scraper.py

# Custom settings
./media_scraper.py --threads 5 --delay 0.5
```

---

## ⚙️ Configuration

| Flag | Default | Description |
|------|---------|-------------|
| `--threads` | `3` | Concurrent download workers |
| `--delay` | `1.0` | Seconds between requests (anti-rate-limit) |

### File Structure
```
.
├── media_scraper.py        # Main Python scraper
├── cleaned_data.json       # Browser-extracted metadata (input)
├── progress.json           # Auto-generated resume tracker
├── results.json            # Download summary report
└── downloads/              # Output directory
    ├── *.pdf              # Court documents
    └── *.mp4              # Deposition videos (if available)
```

---

## 🔧 Technical Details

### Anti-Block Mechanism

Three-layer defense against rate limiting:

1. **Cookie Rotation** - Selenium auto-refreshes QueueIT cookies after 10 blocks
2. **Request Delay** - Configurable sleep between operations  
3. **Header Spoofing** - Custom User-Agent and Referer headers

### Cookie Structure
```python
QueueITAccepted-SDFrts345E-V3_usdojfiles=...
justiceGovAgeVerified=true
```

### Video Detection Algorithm
```
PDF URL: .../document.pdf
  ↓
Strip .pdf extension → .../document
  ↓
Try: .../document.mp4
Try: .../document.m4v
Try: .../document.mov
Try: .../document.webm
Try: .../document.avi
  ↓
Download first match with video/* MIME type
```

---

## 📊 Output

### Terminal
```
   DOJ / Epstein Files AUTO SCRAPER
   Made by: [CBKB] Deadly-Data

[+] Records: 1247
[+] Threads: 3
[+] Delay: 1.0s

[1/1247] epstein_deposition_001.pdf
   [+] PDF OK
   [ ] .mp4 → no
   [+] VIDEO: .m4v

==============================
          SUMMARY
==============================
Total:     1247
PDF OK:    1198
Video:     342
No Video:  856
==============================
```

### results.json
```json
[
  {
    "pdf": "https://www.justice.gov/.../file.pdf",
    "pdf_ok": true,
    "video_ext": "m4v",
    "video_url": "https://www.justice.gov/.../file.m4v"
  }
]
```

---

## 🛡️ Legal & Ethical

- ✅ **Public Domain** - All files are officially released government court documents
- ✅ **Respectful Crawling** - Built-in delays prevent server overload
- ✅ **No Authentication Bypass** - Uses publicly accessible URLs only
- ✅ **Rate Limited** - Configurable throttling

**Disclaimer:** This tool archives publicly released Jeffrey Epstein court documents for research and transparency purposes. Users are responsible for compliance with local laws and the DOJ's terms of service.

---

## 🐛 Troubleshooting

### Cookie refresh fails
```bash
# Ensure ChromeDriver is installed
which chromedriver

# Update undetected-chromedriver
pip install --upgrade undetected-chromedriver
```

### "Corrupt PDF" errors
- Lower `--threads 1`
- Increase `--delay 2.0`
- Check network stability

### Resume after interruption
- Script auto-resumes using `progress.json`
- Delete `progress.json` to restart from scratch

### High block count
```
[!] Block 10/10
[!] Refreshing cookie with Selenium...
```
- Normal behavior - script auto-refreshes cookies
- Increase `--delay` if blocks happen frequently
- Reduce `--threads` to lower request rate

---

## 🔄 Workflow
```
1. Download cleaned_data.json (or extract yourself)
   ↓
2. Run: ./media_scraper.py --threads 3
   ↓
3. Files downloaded to downloads/
   - PDFs + companion videos
   - Progress tracked in progress.json
```

---

## 🤝 Contributing

Pull requests welcome. For major changes, open an issue first.

---

## 📜 License

MIT © 2025 - For educational and archival purposes

---

## 🔗 References

- [DOJ Jeffrey Epstein Files Portal](https://www.justice.gov/multimedia-search?keys=no%20images%20produced)
- [Undetected ChromeDriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver)

---

<div align="center">

**[CBKB] Deadly-Data**

*Built for transparency • Archived for history*

</div>