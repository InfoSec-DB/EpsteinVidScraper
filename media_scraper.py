#!/usr/bin/env python3

import json
import os
import time
import subprocess
import argparse
import threading
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed

import undetected_chromedriver as uc


# ==============================
# COLORS
# ==============================

RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
BOLD = "\033[1m"


# ==============================
# CONFIG
# ==============================

JSON_FILE = "cleaned_data.json"
OUT_DIR = "downloads"

PROGRESS_FILE = "progress.json"
MIN_VALID_SIZE = 1024  # bytes

START_COOKIE = (
    "QueueITAccepted-SDFrts345E-V3_usdojfiles="
    "EventId%3Dusdojfiles%26RedirectType%3Dsafetynet%26IssueTime%3D1770770963"
    "%26Hash%3D25e96c582b599b7883673a6269f33734d21f004b0f0b8e431e06902472c7055d"
    "; justiceGovAgeVerified=true"
)

USER_AGENT = "Mozilla/5.0"
REFERER = "https://www.justice.gov/"

VIDEO_EXTS = ["mp4", "m4v", "mov", "webm", "avi"]

BLOCK_THRESHOLD = 10


# ==============================
# GLOBAL STATE
# ==============================

COOKIE = START_COOKIE
BLOCK_COUNT = 0

cookie_lock = threading.Lock()
block_lock = threading.Lock()
progress_lock = threading.Lock()


# ==============================
# BANNER
# ==============================

def banner():

    print(f"""{CYAN}{BOLD}
	

   DOJ / Epstein Files AUTO SCRAPER
   Made by: [CBKB] Deadly-Data
{RESET}
""")


# ==============================
# PROGRESS
# ==============================

def load_progress():

    if not os.path.exists(PROGRESS_FILE):
        return {"completed": []}

    with open(PROGRESS_FILE, "r") as f:
        return json.load(f)


def save_progress(progress):

    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


# ==============================
# ARGUMENTS
# ==============================

def parse_args():

    p = argparse.ArgumentParser()

    p.add_argument("--threads", type=int, default=3)
    p.add_argument("--delay", type=float, default=1.0)

    return p.parse_args()


# ==============================
# SELENIUM COOKIE
# ==============================

def get_new_cookie():

    print(f"\n{YELLOW}[!] Refreshing cookie with Selenium...{RESET}\n")

    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = uc.Chrome(options=options)

    try:
        driver.get("https://www.justice.gov/")
        time.sleep(10)

        cookies = driver.get_cookies()

    finally:
        driver.quit()


    new_cookie = ""

    for c in cookies:
        if "QueueITAccepted" in c["name"]:
            new_cookie += f"{c['name']}={c['value']}; "


    new_cookie += "justiceGovAgeVerified=true"

    if "QueueITAccepted" in new_cookie:
        print(f"{GREEN}[+] New cookie acquired{RESET}")
    else:
        print(f"{RED}[!] Cookie refresh failed{RESET}")

    return new_cookie


# ==============================
# CURL
# ==============================

def curl_head(url):

    with cookie_lock:
        cookie = COOKIE

    cmd = [
        "curl", "-s", "-L", "-I",
        "-H", f"Cookie: {cookie}",
        "-H", f"User-Agent: {USER_AGENT}",
        "-H", f"Referer: {REFERER}",
        url
    ]

    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout.lower()


def curl_download(url, out_path):

    with cookie_lock:
        cookie = COOKIE

    cmd = [
        "curl", "-s", "-L",
        "-H", f"Cookie: {cookie}",
        "-H", f"User-Agent: {USER_AGENT}",
        "-H", f"Referer: {REFERER}",
        "-o", out_path,
        url
    ]

    subprocess.run(cmd)


def encode_url(url: str) -> str:
    return quote(url, safe=":/%")


# ==============================
# BLOCK HANDLING
# ==============================

def register_block():

    global BLOCK_COUNT, COOKIE

    with block_lock:

        BLOCK_COUNT += 1

        print(f"{RED}[!] Block {BLOCK_COUNT}/{BLOCK_THRESHOLD}{RESET}")

        if BLOCK_COUNT >= BLOCK_THRESHOLD:

            with cookie_lock:
                COOKIE = get_new_cookie()

            BLOCK_COUNT = 0


# ==============================
# WORKER
# ==============================

def process_record(i, rec, total, delay, progress):

    raw_pdf = rec["ORIGIN_FILE_URI"]
    pdf_url = encode_url(raw_pdf)

    pdf_name = pdf_url.split("/")[-1]
    pdf_out = os.path.join(OUT_DIR, pdf_name)
    tmp_out = pdf_out + ".tmp"


    # Skip completed
    with progress_lock:
        if pdf_name in progress["completed"]:
            return None


    print(f"{CYAN}[{i}/{total}]{RESET} {pdf_name}")


    result = {
        "pdf": pdf_url,
        "pdf_ok": False,
        "video_ext": None,
        "video_url": None
    }


    # ----------------------
    # PDF CHECK
    # ----------------------

    headers = curl_head(pdf_url)

    if (
        "content-type: application/pdf" not in headers
        or "queue-it" in headers
        or "text/html" in headers
    ):

        print(f"   {RED}[-] PDF BLOCKED{RESET}")
        register_block()
        time.sleep(delay)
        return result


    # Download to temp
    curl_download(pdf_url, tmp_out)


    # Validate
    if not os.path.exists(tmp_out) or os.path.getsize(tmp_out) < MIN_VALID_SIZE:

        print(f"   {YELLOW}[!] Corrupt PDF — removed{RESET}")

        if os.path.exists(tmp_out):
            os.remove(tmp_out)

        register_block()
        return result


    os.replace(tmp_out, pdf_out)

    print(f"   {GREEN}[+] PDF OK{RESET}")
    result["pdf_ok"] = True


    # ----------------------
    # VIDEO CHECK
    # ----------------------

    base = pdf_url[:-4]

    for ext in VIDEO_EXTS:

        vid_url = f"{base}.{ext}"

        headers = curl_head(vid_url)

        if "content-type: video" in headers:

            vid_name = vid_url.split("/")[-1]
            vid_out = os.path.join(OUT_DIR, vid_name)

            curl_download(vid_url, vid_out)

            print(f"   {MAGENTA}[+] VIDEO: .{ext}{RESET}")

            result["video_ext"] = ext
            result["video_url"] = vid_url
            break

        else:
            print(f"   {YELLOW}[ ] .{ext} → no{RESET}")


    if not result["video_ext"]:
        print(f"   {BLUE}[-] No video{RESET}")


    # Save progress
    with progress_lock:
        progress["completed"].append(pdf_name)
        save_progress(progress)


    time.sleep(delay)

    return result


# ==============================
# MAIN
# ==============================

def main():

    global COOKIE

    banner()

    args = parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)

    progress = load_progress()


    with open(JSON_FILE, "r") as f:
        records = json.load(f)


    total = len(records)


    print(f"{GREEN}[+] Records:{RESET} {total}")
    print(f"{GREEN}[+] Threads:{RESET} {args.threads}")
    print(f"{GREEN}[+] Delay:{RESET} {args.delay}s\n")


    results = []


    with ThreadPoolExecutor(max_workers=args.threads) as executor:

        futures = {
            executor.submit(
                process_record,
                i + 1,
                rec,
                total,
                args.delay,
                progress
            ): i
            for i, rec in enumerate(records)
        }


        for fut in as_completed(futures):

            try:
                res = fut.result()

                if res:
                    results.append(res)

            except Exception as e:
                print(f"{RED}[!] Worker error:{RESET} {e}")


    # ----------------------
    # SUMMARY
    # ----------------------

    with open("results.json", "w") as f:
        json.dump(results, f, indent=2)


    pdf_ok = sum(1 for r in results if r["pdf_ok"])
    vid_ok = sum(1 for r in results if r["video_ext"])


    print(f"""
{BOLD}{CYAN}==============================
          SUMMARY
=============================={RESET}
{GREEN}Total:{RESET}     {len(results)}
{GREEN}PDF OK:{RESET}    {pdf_ok}
{MAGENTA}Video:{RESET}     {vid_ok}
{YELLOW}No Video:{RESET}  {pdf_ok - vid_ok}
{CYAN}=============================={RESET}
""")


if __name__ == "__main__":
    main()
