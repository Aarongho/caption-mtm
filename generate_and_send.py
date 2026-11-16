#!/usr/bin/env python3
"""
AI Agent: Caption Generator + Fonnte Sender
Toko Maju Terus Maju - Kertas Thermal Otani

Alur tiap kali jalan:
1. Generate 7 caption marketplace baru (via Claude API) untuk minggu depan
2. Hitung tanggal + sisipkan Promo Toko / Flash Sale tanggal kembar
3. Kirim tiap caption ke Fonnte (blast ke daftar nomor / grup WA)

Dijalankan otomatis oleh GitHub Actions (lihat .github/workflows/mingguan.yml).
Semua rahasia (API key) diambil dari environment variable — JANGAN hardcode di sini.
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
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
FONNTE_TOKEN      = os.environ.get("FONNTE_TOKEN", "")

# Tujuan kirim WA. Bisa:
#  - daftar nomor dipisah koma: "6281234567890,6289876543210"
#  - atau ID grup WA Fonnte
# Diisi lewat Secret FONNTE_TARGET.
FONNTE_TARGET = os.environ.get("FONNTE_TARGET", "")

# Kalau DRY_RUN=1, caption HANYA dibuat & dicetak, TIDAK dikirim ke WA.
# Berguna untuk tes pertama kali tanpa spam pelanggan.
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"

# Jeda antar pengiriman (detik) biar tidak dianggap spam
SEND_DELAY = int(os.environ.get("SEND_DELAY", "3"))

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-4-8")

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
    """Kembalikan list 7 date object: Senin s/d Minggu minggu depan."""
    today = datetime.date.today()
    # weekday(): Senin=0 ... Minggu=6
    # Senin minggu depan = Senin terdekat setelah hari ini
    days_ahead = 7 - today.weekday()  # kalau hari ini Minggu(6) -> besok Senin
    senin_depan = today + datetime.timedelta(days=days_ahead)
    return [senin_depan + datetime.timedelta(days=i) for i in range(7)]


def is_tanggal_kembar(d):
    """True kalau tanggal == bulan (1.1, 2.2, ... 12.12)."""
    return d.day == d.month


def info_flashsale(dates):
    """Cari tanggal kembar di minggu ini; kalau tidak ada, cari yang terdekat berikutnya."""
    kembar = [d for d in dates if is_tanggal_kembar(d)]
    if kembar:
        return {"ada_minggu_ini": True, "tanggal": kembar}
    # cari tanggal kembar terdekat ke depan (dalam 60 hari)
    base = dates[-1]
    for i in range(1, 60):
        d = base + datetime.timedelta(days=i)
        if is_tanggal_kembar(d):
            return {"ada_minggu_ini": False, "berikutnya": d}
    return {"ada_minggu_ini": False, "berikutnya": None}


# ----------------------------------------------------------------------
# 2. GENERATE CAPTION via CLAUDE API
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


def generate_captions(dates, fs):
    prompt = build_prompt(dates, fs)
    payload = json.dumps({
        "model": MODEL,
        "max_tokens": 8000,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    text = data["content"][0]["text"].strip()
    # bersihkan kalau dibungkus ```json ... ```
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    captions = json.loads(text)
    if not isinstance(captions, list) or len(captions) != 7:
        raise ValueError(f"Expected 7 captions, got: {type(captions)} len={len(captions) if isinstance(captions, list) else 'NA'}")
    return captions


# ----------------------------------------------------------------------
# 3. KIRIM ke FONNTE
# ----------------------------------------------------------------------
def send_fonnte(message, target):
    data = urllib.parse.urlencode({
        "target": target,
        "message": message,
    }).encode("utf-8")
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
    if not ANTHROPIC_API_KEY:
        sys.exit("ERROR: ANTHROPIC_API_KEY belum diisi (set di GitHub Secrets).")

    dates = tanggal_minggu_depan()
    fs = info_flashsale(dates)

    print(f"[INFO] Generate caption untuk {dates[0]} s/d {dates[-1]}")
    print(f"[INFO] Flash sale info: {fs}")
    print(f"[INFO] DRY_RUN = {DRY_RUN}")

    captions = generate_captions(dates, fs)

    # Simpan arsip ke folder output
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
        sys.exit("ERROR: FONNTE_TOKEN / FONNTE_TARGET belum diisi. Set di GitHub Secrets, atau pakai DRY_RUN=1 untuk tes.")

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
