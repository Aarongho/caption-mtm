#!/usr/bin/env python3
"""
AI Agent: Caption Generator (Google Gemini - GRATIS) + Fonnte Sender
Toko Maju Terus Maju - Kertas Thermal Otani

Alur tiap kali jalan:
1. Generate 7 caption marketplace baru (via Gemini API gratis) untuk minggu depan
2. Hitung tanggal + sisipkan Promo Toko / Flash Sale tanggal kembar
3. Kirim tiap caption ke Fonnte (blast ke daftar nomor / grup WA)

Dijalankan otomatis oleh GitHub Actions (lihat .github/workflows/mingguan.yml).
Semua rahasia (API key) diambil dari environment variable — JANGAN hardcode di sini.

API key Gemini gratis: https://aistudio.google.com  ->  Get API Key
"""

import os
import sys
import json
import datetime
import time
import urllib.request
import urllib.error
import urllib.parse

# ----------------------------------------------------------------------
# KONFIGURASI (diisi lewat environment variable / GitHub Secrets)
# ----------------------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
FONNTE_TOKEN   = os.environ.get("FONNTE_TOKEN", "")

# Tujuan kirim WA: daftar nomor dipisah koma ("62...,62...") atau ID grup Fonnte.
FONNTE_TARGET = os.environ.get("FONNTE_TARGET", "")

# DRY_RUN=1 -> caption HANYA dibuat & dicetak, TIDAK dikirim ke WA (buat tes aman).
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"

# Jeda antar pengiriman (detik) biar tidak dianggap spam.
SEND_DELAY = int(os.environ.get("SEND_DELAY", "5"))

# Model Gemini gratis. flash = cepat & kuota besar.
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

# ----------------------------------------------------------------------
# DATA PRODUK (ubah di sini kalau ada ukuran / kontak baru)
# ----------------------------------------------------------------------
UKURAN = """🧾 57x31 Coreless → semua Mesin EDC
🧾 57x38 & 57x40 Coreless → Mobile Printer, Struk EDC, Struk Gojek dll
🧾 57x47 Core 13, 57x50 Core, 79x50 Core 13 → Kasir
🧾 80x80 Core 17 → Struk Kasir & Antrian
🧾 80x80 Core 19 → Struk Kasir & Antrian
🧾 80x80 Core 20 → Struk Kasir & Antrian
🧾 79x140 → Struk ATM & Antrian
🏷️ Sticker Label Barcode 100x150mm → Online Shop & Cargo"""

KONTAK = "📞 Rini & Edi | 📱 WA: 0815-9073-321"
PENUTUP = "Toko Maju Terus Maju! 🚀"

HARI_ID = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
BULAN_ID = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
            "Juli", "Agustus", "September", "Oktober", "November", "Desember"]


# ----------------------------------------------------------------------
# 1. HITUNG TANGGAL MINGGU DEPAN (Senin-Minggu)
# ----------------------------------------------------------------------
def tanggal_minggu_depan():
    today = datetime.date.today()
    days_ahead = 7 - today.weekday()  # Senin minggu depan
    senin_depan = today + datetime.timedelta(days=days_ahead)
    return [senin_depan + datetime.timedelta(days=i) for i in range(7)]


def is_tanggal_kembar(d):
    return d.day == d.month


def info_flashsale(dates):
    kembar = [d for d in dates if is_tanggal_kembar(d)]
    if kembar:
        return {"ada_minggu_ini": True, "tanggal": kembar}
    base = dates[-1]
    for i in range(1, 60):
        d = base + datetime.timedelta(days=i)
        if is_tanggal_kembar(d):
            return {"ada_minggu_ini": False, "berikutnya": d}
    return {"ada_minggu_ini": False, "berikutnya": None}


# ----------------------------------------------------------------------
# 2. GENERATE CAPTION via GEMINI API
# ----------------------------------------------------------------------
def build_prompt(dates, fs):
    tgl_list = "\n".join(
        f"- {HARI_ID[d.weekday()]}, {d.day} {BULAN_ID[d.month]} {d.year}"
        + (" (TANGGAL KEMBAR / FLASH SALE!)" if is_tanggal_kembar(d) else "")
        for d in dates
    )
    if fs["ada_minggu_ini"]:
        fs_note = "Ada tanggal kembar minggu ini — buat caption hari itu bertema FLASH SALE besar."
    else:
        b = fs.get("berikutnya")
        fs_note = (
            f"Tidak ada tanggal kembar minggu ini. Pakai teaser Flash Sale tanggal kembar berikutnya: "
            f"{b.day}.{b.month}." if b else "Tidak ada tanggal kembar; cukup Promo Toko."
        )

    return f"""Kamu copywriter marketplace. Buat 7 listing marketplace (gaya Shopee/Tokopedia) untuk kertas thermal merk OTANI, satu untuk tiap hari berikut:
{tgl_list}

ATURAN:
- Format tiap caption: BARIS PERTAMA = judul produk penuh keyword (tanpa label "Judul"). Lalu deskripsi menarik dengan hook/angle BERBEDA tiap hari. Lalu 1 baris hashtag.
- JANGAN tulis kata "Judul" atau "Deskripsi".
- Tiap hari tonjolkan segmen ukuran berbeda (EDC, Kasir 80x80, Label Barcode, ATM, Mobile Printer, Grosir, dll).
- WAJIB sertakan blok ukuran lengkap ini PERSIS di tiap caption:
{UKURAN}
- Keunggulan: cetak HITAM PEKAT, tulisan tahan 5-6 bulan, aman head printer tidak berdebu, Exp. 2 Tahun, OTANI Asli, bisa Custom Logo, Harga Pabrik, Gratis Ongkir se-Indonesia, bisa ecer & grosir dus-dusan, bisa COD.
- Promo: selalu sebut "PROMO TOKO setiap hari — diskon beragam". {fs_note}
- Akhiri tiap caption dengan:
{KONTAK}
{PENUTUP}

OUTPUT: kembalikan HANYA JSON array berisi 7 string (satu caption per elemen), tanpa penjelasan lain. Contoh: ["caption hari 1", "caption hari 2", ...]."""


def list_available_models():
    """Ambil daftar model yang support generateContent untuk key ini."""
    url = (f"https://generativelanguage.googleapis.com/v1beta/models"
           f"?key={GEMINI_API_KEY}")
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[WARN] Gagal ambil daftar model: {e}")
        return []
    models = []
    for m in data.get("models", []):
        if "generateContent" in m.get("supportedGenerationMethods", []):
            # nama datang sebagai "models/xxx"; ambil bagian setelah "models/"
            models.append(m["name"].split("/", 1)[-1])
    return models


def _call_gemini(model, prompt):
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={GEMINI_API_KEY}")
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.9,
            "maxOutputTokens": 8000,
            "responseMimeType": "application/json",
        },
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload,
        headers={"content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def generate_captions(dates, fs):
    prompt = build_prompt(dates, fs)

    # Daftar model yang dicoba berurutan. Model dari GEMINI_MODEL didahulukan,
    # lalu beberapa nama umum sebagai cadangan kalau yang pertama 404.
    candidates = [GEMINI_MODEL, "gemini-flash-latest", "gemini-2.5-flash",
                  "gemini-2.0-flash", "gemini-1.5-flash"]
    # buang duplikat sambil jaga urutan
    seen = set()
    candidates = [m for m in candidates if not (m in seen or seen.add(m))]

    data = None
    last_err = None
    for model in candidates:
        try:
            print(f"[INFO] Coba model: {model}")
            data = _call_gemini(model, prompt)
            print(f"[OK] Model dipakai: {model}")
            break
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")
            last_err = f"HTTP {e.code} untuk {model}: {body[:300]}"
            print(f"[WARN] {last_err}")
            if e.code != 404:
                # error selain 404 (misal key salah / kuota) — tidak perlu coba model lain
                break

    if data is None:
        avail = list_available_models()
        hint = (f" Model yang tersedia untuk key-mu: {avail}" if avail
                else " Tidak bisa ambil daftar model (cek GEMINI_API_KEY).")
        raise RuntimeError(f"Semua model gagal. Error terakhir: {last_err}.{hint} "
                           f"Set Secret GEMINI_MODEL ke salah satu model di atas.")

    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    captions = json.loads(text)
    if not isinstance(captions, list) or len(captions) != 7:
        raise ValueError(f"Expected 7 captions, got {type(captions)} "
                         f"len={len(captions) if isinstance(captions, list) else 'NA'}")
    return captions


# ----------------------------------------------------------------------
# 3. KIRIM ke FONNTE
# ----------------------------------------------------------------------
def send_fonnte(message, target):
    data = urllib.parse.urlencode({"target": target, "message": message}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.fonnte.com/send",
        data=data,
        headers={"Authorization": FONNTE_TOKEN},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
def main():
    if not GEMINI_API_KEY:
        sys.exit("ERROR: GEMINI_API_KEY belum diisi (set di GitHub Secrets). "
                 "Ambil gratis di https://aistudio.google.com")

    dates = tanggal_minggu_depan()
    fs = info_flashsale(dates)

    print(f"[INFO] Generate caption untuk {dates[0]} s/d {dates[-1]}")
    print(f"[INFO] Flash sale info: {fs}")
    print(f"[INFO] Model: {GEMINI_MODEL} | DRY_RUN = {DRY_RUN}")

    captions = generate_captions(dates, fs)

    os.makedirs("output", exist_ok=True)
    for i, (d, cap) in enumerate(zip(dates, captions), start=1):
        fname = f"output/{i}-{HARI_ID[d.weekday()].lower()}-{d.day:02d}{BULAN_ID[d.month][:3].lower()}.txt"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(cap)
        print(f"[OK] Tersimpan: {fname}")

    if DRY_RUN:
        print("\n===== DRY RUN: caption dibuat tapi TIDAK dikirim ke WA =====")
        for i, cap in enumerate(captions, 1):
            print(f"\n--- Caption {i} ---\n{cap}\n")
        return

    if not FONNTE_TOKEN or not FONNTE_TARGET:
        sys.exit("ERROR: FONNTE_TOKEN / FONNTE_TARGET belum diisi. "
                 "Set di GitHub Secrets, atau pakai DRY_RUN=1 untuk tes.")

    print("\n[INFO] Mengirim ke Fonnte...")
    for i, cap in enumerate(captions, 1):
        try:
            resp = send_fonnte(cap, FONNTE_TARGET)
            print(f"[SENT {i}/7] {resp}")
        except urllib.error.HTTPError as e:
            print(f"[FAIL {i}/7] HTTP {e.code}: {e.read().decode('utf-8', 'ignore')}")
        except Exception as e:
            print(f"[FAIL {i}/7] {e}")
        time.sleep(SEND_DELAY)

    print("\n[DONE] Selesai.")


if __name__ == "__main__":
    main()
