# 🤖 AI Agent Caption Otani — Toko Maju Terus Maju

Agent yang tiap minggu **otomatis**:
1. Bikin 7 caption marketplace baru (via **Google Gemini — GRATIS**) untuk minggu depan
2. Hitung tanggal + sisipkan Promo Toko / Flash Sale tanggal kembar (11.11, 12.12, dst)
3. Kirim tiap caption ke WhatsApp lewat **Fonnte** (blast ke daftar nomor / grup)

Jalan di **GitHub Actions** (gratis) — nggak perlu PC nyala, nggak perlu kamu sentuh tiap minggu.

---

## 🧩 Isi folder

| File | Fungsi |
|------|--------|
| `generate_and_send.py` | Otak agent: generate caption (Gemini) + kirim Fonnte |
| `.github/workflows/mingguan.yml` | Penjadwal: jalan tiap Minggu 17:00 WIB |
| `README.md` | Petunjuk ini |

---

## 🚀 Cara setup (sekali saja, ±15 menit)

### 1. Buat repo GitHub
- Buat repo baru (boleh **private**), misal `caption-otani-agent`.
- Upload semua file di folder ini ke repo (termasuk folder `.github`).

### 2. Siapkan kunci rahasia

**a. GEMINI_API_KEY — GRATIS** (buat generate caption)
- Buka https://aistudio.google.com → login Google → **Get API Key** → **Create API Key**.
- Copy key-nya. Free tier Gemini sangat cukup untuk 7 caption/minggu — **tanpa kartu kredit**.

**b. FONNTE_TOKEN** (buat kirim WA) — *opsional, hanya kalau mau auto-kirim WA*
- Login https://fonnte.com → connect device WA → ambil **Token** device.

**c. FONNTE_TARGET** (tujuan kirim) — *opsional*
- Daftar nomor dipisah koma, format `62...`:
  `6281234567890,6289876543210`
- Atau ID grup WA.

> Kalau belum mau kirim WA, cukup isi GEMINI_API_KEY saja dan jalankan mode DRY_RUN (lihat langkah 4).

### 3. Masukkan ke GitHub Secrets
Repo → **Settings → Secrets and variables → Actions → New repository secret**.
Nama harus PERSIS:

| Name | Value | Wajib? |
|------|-------|--------|
| `GEMINI_API_KEY` | API key dari aistudio.google.com | ✅ Ya |
| `FONNTE_TOKEN` | Token device Fonnte | Hanya kalau auto-kirim WA |
| `FONNTE_TARGET` | Nomor/grup tujuan | Hanya kalau auto-kirim WA |

> ⚠️ Secret tidak terlihat siapa pun, termasuk di log. JANGAN tulis key langsung di kode.

### 4. Tes dulu (tanpa spam pelanggan!)
- Repo → tab **Actions** → "Caption Mingguan Otani" → **Run workflow**.
- Biarkan `dry_run = 1` (default). Ini **cuma bikin caption, tidak kirim WA**.
- Lihat hasil di bagian **Artifacts** ("caption-minggu-ini") → cek 7 caption.

### 5. Aktifkan beneran (kalau mau auto-kirim WA)
- Kalau hasil tes oke & Fonnte sudah diisi, biarkan saja. Tiap **Minggu 17:00 WIB** agent
  jalan sendiri dan kirim ke WA (`DRY_RUN=0`).
- Belum mau kirim WA? Biarkan `DRY_RUN` default & pakai hasil Artifacts untuk copas manual.

---

## 💰 Soal biaya
- **Generate caption: GRATIS** (Gemini free tier).
- **GitHub Actions: GRATIS** untuk repo pribadi (kuota bulanan jauh lebih dari cukup).
- **Fonnte: berbayar** kalau mau auto-kirim WA (ada paketnya). Kalau mau 100% gratis,
  skip Fonnte dan sebar caption-nya manual (copas ke Status WA / Broadcast / marketplace).

## ⚠️ Soal risiko ban WhatsApp
Blast WA massal ke nomor yang **tidak mengenal kamu** berisiko nomor kena ban. Aman kalau:
kirim ke pelanggan yang sudah save nomormu, pakai nomor WA Business khusus, jeda antar pesan
(script sudah `SEND_DELAY`), jumlah wajar per hari. Alternatif paling aman: **Status WA** &
**Broadcast List** (fitur resmi) atau posting marketplace/IG/FB.

---

## 🔧 Ubah produk / kontak / ukuran / jam
Edit bagian atas `generate_and_send.py` (`UKURAN`, `KONTAK`, `PENUTUP`).
Ganti jam kirim: edit `cron` di `mingguan.yml` (pakai UTC; WIB = UTC+7, jadi 17:00 WIB = `0 10`).

## 🆘 Kalau gagal
- Tab **Actions** → klik run merah → baca log.
- Error `GEMINI`: key salah / kuota harian habis (tunggu reset besok).
- Error `FONNTE`: token salah / device WA offline / format nomor salah.
