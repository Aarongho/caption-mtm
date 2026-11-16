# 🤖 AI Agent Caption Otani — Toko Maju Terus Maju

Agent yang tiap minggu **otomatis**:
1. Bikin 7 caption marketplace baru (via Claude API) untuk minggu depan
2. Hitung tanggal + sisipkan Promo Toko / Flash Sale tanggal kembar (11.11, 12.12, dst)
3. Kirim tiap caption ke WhatsApp lewat **Fonnte** (blast ke daftar nomor / grup)

Jalan di **GitHub Actions** (gratis) — nggak perlu PC nyala, nggak perlu kamu sentuh tiap minggu.

---

## 🧩 Isi folder

| File | Fungsi |
|------|--------|
| `generate_and_send.py` | Otak agent: generate caption + kirim Fonnte |
| `.github/workflows/mingguan.yml` | Penjadwal: jalan tiap Minggu 17:00 WIB |
| `README.md` | Petunjuk ini |

---

## 🚀 Cara setup (sekali saja, ±15 menit)

### 1. Buat repo GitHub
- Buat repo baru (boleh **private**), misal `caption-otani-agent`.
- Upload semua file di folder ini ke repo (termasuk folder `.github`).

### 2. Siapkan 3 kunci rahasia

**a. ANTHROPIC_API_KEY** (buat generate caption)
- Daftar di https://console.anthropic.com → bikin API Key.
- Ada biaya pemakaian, tapi untuk 7 caption/minggu sangat kecil (hitungan ratusan rupiah).

**b. FONNTE_TOKEN** (buat kirim WA)
- Login https://fonnte.com → connect device WA kamu → ambil **Token** device.

**c. FONNTE_TARGET** (tujuan kirim)
- Daftar nomor dipisah koma, format `62...`:
  `6281234567890,6289876543210`
- Atau ID grup WA (lihat dokumentasi Fonnte).

### 3. Masukkan ke GitHub Secrets
Di repo → **Settings → Secrets and variables → Actions → New repository secret**.
Buat 3 secret ini (nama harus PERSIS):

| Name | Value |
|------|-------|
| `ANTHROPIC_API_KEY` | API key Anthropic kamu |
| `FONNTE_TOKEN` | Token device Fonnte |
| `FONNTE_TARGET` | Nomor/grup tujuan |

> ⚠️ Secret tidak akan terlihat siapa pun, termasuk di log. JANGAN tulis key langsung di kode.

### 4. Tes dulu (tanpa spam pelanggan!)
- Repo → tab **Actions** → pilih "Caption Mingguan Otani" → **Run workflow**.
- Biarkan `dry_run = 1` (default). Ini **cuma bikin caption, tidak kirim WA**.
- Buka hasilnya di bagian **Artifacts** ("caption-minggu-ini") → cek 7 caption-nya.

### 5. Aktifkan beneran
- Kalau hasil tes sudah oke, biarkan saja. Tiap **Minggu 17:00 WIB** agent jalan sendiri
  dan **kirim beneran** ke WA (jadwal otomatis selalu `DRY_RUN=0`).
- Mau kirim manual kapan saja? Run workflow → set `dry_run = 0`.

---

## 🔧 Ubah produk / kontak / ukuran
Edit bagian atas `generate_and_send.py`:
- `UKURAN` → daftar ukuran (tambah/kurangi di sini)
- `KONTAK`, `PENUTUP` → kontak & penutup
- Ganti jam: edit `cron` di `mingguan.yml` (ingat: pakai UTC, WIB = UTC+7)

---

## 💡 Catatan jujur
- Agent ini **tidak "mengintip" caption trending Shopee/Tokopedia** secara langsung — itu tidak
  tersedia lewat API resmi & melanggar aturan platform. Sebagai gantinya, caption dibuat pakai
  formula copywriting yang memang terbukti laku (hook, urgensi, promo tanggal kembar, keyword produk).
- Kalau mau caption makin nendang: pasang bareng **foto/video produk asli** saat posting.

---

## 🆘 Kalau gagal
- Cek tab **Actions** → klik run yang merah → baca log.
- Error `FONNTE` biasanya: token salah / device WA kebetulan offline / nomor format salah.
- Error `ANTHROPIC`: API key salah atau saldo habis.
