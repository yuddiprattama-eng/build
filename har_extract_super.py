import json
import os
import base64
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# Nama HAR
HAR_FILE = "website.har"  # ganti sesuai HAR kamu
OUTPUT_FOLDER = "extracted_files"

# Folder berdasarkan tipe
FOLDERS = {
    "html": os.path.join(OUTPUT_FOLDER, "html"),
    "css": os.path.join(OUTPUT_FOLDER, "css"),
    "js": os.path.join(OUTPUT_FOLDER, "js"),
    "images": os.path.join(OUTPUT_FOLDER, "images"),
    "fonts": os.path.join(OUTPUT_FOLDER, "fonts"),
    "json": os.path.join(OUTPUT_FOLDER, "json"),
    "xml": os.path.join(OUTPUT_FOLDER, "xml"),
    "other": os.path.join(OUTPUT_FOLDER, "other")
}

for folder in FOLDERS.values():
    os.makedirs(folder, exist_ok=True)

# Mapping mimeType ke folder & ekstensi
MIME_MAP = {
    "text/html": ("html", ".html"),
    "text/css": ("css", ".css"),
    "application/javascript": ("js", ".js"),
    "application/x-javascript": ("js", ".js"),
    "image/png": ("images", ".png"),
    "image/jpeg": ("images", ".jpg"),
    "image/jpg": ("images", ".jpg"),
    "image/webp": ("images", ".webp"),
    "image/gif": ("images", ".gif"),
    "image/svg+xml": ("images", ".svg"),
    "font/woff2": ("fonts", ".woff2"),
    "font/woff": ("fonts", ".woff"),
    "application/font-woff": ("fonts", ".woff"),
    "application/json": ("json", ".json"),
    "application/xml": ("xml", ".xml"),
}

# Step 1: Ekstrak semua file dari HAR
with open(HAR_FILE, "r", encoding="utf-8") as f:
    har_data = json.load(f)

count = 0
html_files = []

for entry in har_data.get("log", {}).get("entries", []):
    request_url = entry["request"]["url"]
    content = entry["response"].get("content", {})
    text = content.get("text")
    if not text:
        continue

    mime = content.get("mimeType", "other")
    folder_name, ext = MIME_MAP.get(mime, ("other", ""))

    path = urlparse(request_url).path
    filename = os.path.basename(path)
    if not filename:
        filename = f"file_{count}"
    if not filename.endswith(ext):
        filename += ext

    filepath = os.path.join(FOLDERS[folder_name], filename)

    # Simpan file
    if content.get("encoding") == "base64":
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(text))
    else:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)

    if folder_name == "html":
        html_files.append(filepath)

    count += 1

print(f"✅ Ekstraksi selesai: {count} file disimpan di '{OUTPUT_FOLDER}'")

# Step 2: Tentukan HTML utama (file terbesar)
index_html = None
max_size = 0
for html_file in html_files:
    size = os.path.getsize(html_file)
    if size > max_size:
        max_size = size
        index_html = html_file

# Rename HTML utama jadi index.html
if index_html:
    index_path = os.path.join(FOLDERS["html"], "index.html")
    os.rename(index_html, index_path)
    print(f"✅ HTML utama diubah menjadi: {index_path}")
else:
    print("⚠️ Tidak ditemukan HTML utama")

# Step 3: Perbaiki path HTML
FOLDER_MAP = {
    ".css": "../css",
    ".js": "../js",
    ".png": "../images",
    ".jpg": "../images",
    ".jpeg": "../images",
    ".webp": "../images",
    ".gif": "../images",
    ".svg": "../images",
    ".woff": "../fonts",
    ".woff2": "../fonts",
}

html_files_to_fix = [index_path] if index_html else []

for html_file in html_files_to_fix:
    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    for tag in soup.find_all("link", href=True):
        ext = os.path.splitext(tag['href'])[1]
        if ext in FOLDER_MAP:
            tag['href'] = os.path.join(FOLDER_MAP[ext], os.path.basename(tag['href']))

    for tag in soup.find_all("script", src=True):
        ext = os.path.splitext(tag['src'])[1]
        if ext in FOLDER_MAP:
            tag['src'] = os.path.join(FOLDER_MAP[ext], os.path.basename(tag['src']))

    for tag in soup.find_all("img", src=True):
        ext = os.path.splitext(tag['src'])[1]
        if ext in FOLDER_MAP:
            tag['src'] = os.path.join(FOLDER_MAP[ext], os.path.basename(tag['src']))

    for tag in soup.find_all("source", src=True):
        ext = os.path.splitext(tag['src'])[1]
        if ext in FOLDER_MAP:
            tag['src'] = os.path.join(FOLDER_MAP[ext], os.path.basename(tag['src']))

    with open(html_file, "w", encoding="utf-8") as f:
        f.write(str(soup))

    print(f"✅ Fixed paths: {html_file}")

print("🎉 Semua file siap dibuka di browser tanpa error link!")
