# Cutline — AI Video Clipper

**Cutline** adalah aplikasi web lokal berbasis AI untuk mengubah video berdurasi panjang menjadi klip *short-form* yang siap ditinjau dan diekspor untuk TikTok, Instagram Reels, dan YouTube Shorts.

Aplikasi ini menggunakan Flask sebagai backend, FFmpeg untuk pemrosesan video, serta Whisper lokal untuk mentranskripsikan ucapan dan menemukan kandidat *hook*.

## ✨ Fitur Utama

- **YouTube Clipper:** Memotong video YouTube berdasarkan URL dan timestamp.
- **Upload Video Lokal:** Mengunggah video melalui halaman AI Editor.
- **AI Speech Detection:** Mendeteksi ucapan menggunakan `faster-whisper`.
- **Hook Selection:** Memilih satu kandidat hook terbaik berdasarkan hasil analisis.
- **Review Before Render:** Menyediakan tahap analisis dan persetujuan sebelum rendering final.
- **Automatic Subtitles:** Membuat subtitle otomatis berdasarkan timestamp kata.
- **Vertical Video Format:** Mengubah video menjadi format vertikal 9:16 dengan background blur agar video landscape tetap terlihat tanpa crop ekstrem.
- **Hook Text:** Menampilkan teks hook pada awal video.
- **Call to Action (CTA):** Menambahkan CTA pada akhir video.
- **Audio Normalization:** Menormalisasi audio ke sekitar -14 LUFS.
- **High-Resolution Export:** Mengekspor video MP4 H.264 dengan resolusi 1080 × 1920.
- **Browser Preview:** Memutar preview video hasil edit langsung dari browser.
- **Download Result:** Mengunduh video hasil rendering.
- **Upload Progress:** Menampilkan animasi upload dan progres pemrosesan.
- **Campaign Brief:** Mengatur instruksi editing melalui panel yang dapat diubah pada halaman editor.

## 🛠️ Teknologi

| Teknologi | Fungsi |
|---|---|
| Python 3.13 | Bahasa pemrograman utama |
| Flask | Backend dan API |
| `yt-dlp` | Ekstraksi video YouTube |
| `faster-whisper` | Transkripsi ucapan dan analisis kandidat hook |
| FFmpeg | Pemotongan, rendering, dan encoding video |
| Node.js | JavaScript runtime untuk workflow ekstraksi YouTube |
| HTML, CSS, JavaScript | Antarmuka frontend tanpa framework |

## 📁 Struktur Project

```text
yt-clipper/
├── app.py
├── requirements.txt
├── downloads/
│   └── analysis/
├── templates/
│   ├── index.html
│   └── editor.html
└── venv/
```

### File dan Folder Penting

- `app.py` — Aplikasi Flask, endpoint API, analisis Whisper, dan pipeline FFmpeg.
- `templates/index.html` — Halaman manual YouTube clipper.
- `templates/editor.html` — Halaman AI Editor untuk upload video dan review hasil analisis.
- `requirements.txt` — Daftar dependency Python.
- `downloads/` — Penyimpanan sementara dan hasil video.
- `venv/` — Virtual environment Python.

> **Catatan:** Folder `venv/` biasanya tidak perlu dimasukkan ke repository Git. Virtual environment dapat dibuat kembali melalui proses instalasi.

## 💻 Persyaratan Sistem

Pastikan perangkat memiliki:

- Windows 10 atau Windows 11.
- Python 3.10 atau lebih baru.
- FFmpeg.
- Node.js.
- Koneksi internet saat pertama kali mengunduh model Whisper.

FFmpeg dan Node.js digunakan untuk kebutuhan yang berbeda:

- **FFmpeg** digunakan untuk membaca, memotong, merender, dan melakukan encoding video.
- **Node.js** membantu `yt-dlp` menangani proses ekstraksi YouTube pada workflow yang memerlukannya.

## 🚀 Instalasi

### 1. Masuk ke Folder Project

Buka PowerShell, kemudian jalankan:

```powershell
cd D:\ABDUL\xampp\htdocs\yt-clipper
```

Sesuaikan path tersebut jika folder project berada di lokasi lain.

### 2. Buat Virtual Environment

Jika virtual environment belum tersedia:

```powershell
python -m venv venv
```

### 3. Aktifkan Virtual Environment

```powershell
.\venv\Scripts\Activate.ps1
```

Jika PowerShell menolak menjalankan script aktivasi, kamu dapat menggunakan Python langsung melalui `venv\Scripts\python.exe` tanpa aktivasi.

### 4. Install Dependency Python

```powershell
python -m pip install -r requirements.txt
```

### 5. Install FFmpeg

Jika FFmpeg belum tersedia, jalankan:

```powershell
winget install --id Gyan.FFmpeg.Shared --exact --source winget
```

### 6. Install Node.js

Jika Node.js belum tersedia, jalankan:

```powershell
winget install OpenJS.NodeJS.LTS
```

Setelah instalasi FFmpeg atau Node.js, tutup dan buka kembali terminal agar perubahan `PATH` dapat terbaca.

## ▶️ Menjalankan Aplikasi

Masuk ke direktori project:

```powershell
cd D:\ABDUL\xampp\htdocs\yt-clipper
```

Jalankan server Flask:

```powershell
.\venv\Scripts\python.exe app.py
```

Setelah server berjalan, buka aplikasi melalui browser.

| Halaman | URL |
|---|---|
| Manual YouTube Clipper | `http://localhost:5000` |
| AI Editor | `http://localhost:5000/editor` |

Untuk menghentikan server, tekan `CTRL + C` pada terminal tempat aplikasi berjalan.

## 🎬 Workflow AI Editor

### 1. Upload Video

Buka halaman `/editor`, lalu pilih video dari perangkat atau gunakan fitur drag-and-drop.

Format video yang didukung:

- MP4
- MOV
- MKV
- WEBM
- AVI
- M4V

Ukuran maksimum file upload adalah **500 MB**.

### 2. Analisis Video

Whisper lokal menjalankan proses analisis untuk:

1. Membaca audio dari video.
2. Membuat transkrip beserta timestamp.
3. Mencari kalimat yang memiliki sinyal hook.
4. Memberikan kandidat beserta skor viralitas.
5. Menampilkan timestamp, durasi, teks hook, dan alasan pemilihan kandidat.

### 3. Review Kandidat

Aplikasi menampilkan satu kandidat hook terlebih dahulu. Pada tahap ini, video belum dirender sebagai hasil final sehingga pengguna dapat meninjau hasil analisis sebelum melanjutkan.

### 4. Approve dan Render

Klik **APPROVE & RENDER CLIP** untuk memulai proses pembuatan satu video final.

Hasil rendering mencakup:

- Satu klip terbaik berdasarkan analisis.
- Format video vertikal 9:16.
- Video sumber tetap terlihat di atas background blur.
- Subtitle otomatis.
- Hook text maksimal delapan kata pada awal video.
- CTA pada bagian akhir.
- Audio AAC 192 kbps dengan sample rate 48 kHz.
- Video H.264 dengan bitrate target sekitar 10 Mbps.

Model Whisper default yang digunakan adalah `base`. Pada penggunaan pertama, model akan diunduh sehingga proses analisis dapat memerlukan waktu lebih lama.

## 🧠 Mengganti Model Whisper

Model Whisper dapat diganti menggunakan environment variable `CUTLINE_WHISPER_MODEL`.

Contoh untuk menggunakan model `small`:

```powershell
$env:CUTLINE_WHISPER_MODEL="small"
.\venv\Scripts\python.exe app.py
```

### Perbandingan Model

| Model | Kecepatan Relatif | Karakteristik |
|---|---|---|
| `tiny` | Paling cepat | Akurasi relatif rendah |
| `base` | Seimbang | Cocok untuk penggunaan umum |
| `small` | Lebih lambat | Berpotensi lebih akurat |
| `medium` | Paling berat di antara pilihan ini | Membutuhkan resource lebih besar dan dapat memberikan hasil transkripsi lebih akurat |

Kecepatan dan akurasi aktual bergantung pada perangkat, bahasa, kualitas audio, serta karakteristik video.

## 📋 Campaign Brief

Panel **Campaign Brief** tersedia pada halaman `/editor` dan digunakan untuk mengatur instruksi editing sesuai kebutuhan campaign.

Parameter yang dapat dijelaskan meliputi:

- Platform tujuan.
- Bahasa subtitle.
- Jumlah klip.
- Durasi target.
- Aturan hook.
- Aturan framing.
- Larangan watermark.
- Format output.
- Aturan caption dan hashtag.

### Contoh Campaign Brief

```text
MODE: AUTO
JUMLAH KLIP: 1
DURASI: 30-60 detik

WAJIB:
- Hook kuat dalam 3 detik pertama.
- Subtitle maksimal 2 baris.

DILARANG:
- Crop wajah.
- Klaim palsu.
- Watermark pihak lain.

TEKNIS:
- Format MP4 H.264.
- Resolusi 1080x1920.
- Frame rate 30 fps.

POSTING:
- Buat caption dan hashtag sesuai isi video.
```

Tuliskan aturan campaign secara eksplisit agar instruksi lebih mudah dipahami. Efektivitas setiap aturan tetap bergantung pada bagaimana pipeline aplikasi memproses `campaign_rules`.

## 🔌 API Reference

### 1. Health Check

```http
GET /api/health
```

Memeriksa status komponen yang digunakan aplikasi, termasuk FFmpeg, `yt-dlp`, dan JavaScript runtime.

### 2. Analisis Video

```http
POST /api/analyze-video
Content-Type: multipart/form-data
```

Field utama:

```text
video
campaign_rules
subtitle_language
platform
clip_count
```

Respons menyediakan `job_id` dan kandidat hook berdasarkan hasil analisis.

### 3. Render Hasil Edit

```http
POST /api/render-edit
Content-Type: application/json
```

Contoh request body:

```json
{
  "job_id": "id-hasil-analisis"
}
```

Endpoint ini digunakan untuk memulai rendering berdasarkan hasil analisis yang telah disetujui.

### 4. Preview Video

```http
GET /api/preview/<filename>
```

Digunakan untuk menampilkan video hasil rendering melalui browser.

### 5. Download Video

```http
GET /api/download/<filename>
```

Digunakan untuk mengunduh file video hasil rendering.

### 6. Manual YouTube Clipping

```http
POST /api/cut
Content-Type: application/json
```

Contoh request body:

```json
{
  "url": "https://www.youtube.com/watch?v=...",
  "start_time": "01:00",
  "end_time": "02:00"
}
```

Endpoint ini digunakan untuk memotong video YouTube berdasarkan waktu mulai dan waktu selesai.

> **Catatan API:** Format di atas merangkum endpoint dan field yang tercantum dalam dokumentasi project. Skema respons lengkap, autentikasi, validasi input, serta format error perlu diperiksa langsung pada implementasi `app.py`.

## 🧰 Troubleshooting

### FFmpeg Tidak Ditemukan

Periksa apakah aplikasi dapat menemukan executable FFmpeg:

```powershell
.\venv\Scripts\python.exe -c "import sys; sys.path.insert(0, '.'); import app; print(app.find_ffmpeg())"
```

Jika hasilnya `None`, instal FFmpeg:

```powershell
winget install --id Gyan.FFmpeg.Shared --exact --source winget
```

Setelah instalasi, buka ulang terminal dan restart server Flask.

### Model Whisper Belum Tersedia

Jalankan server, lalu upload video melalui AI Editor. Model `base` akan diunduh secara otomatis saat analisis pertama apabila implementasi aplikasi menggunakan mekanisme tersebut.

Pastikan koneksi internet tersedia dan ruang penyimpanan mencukupi.

### Video Tidak Memiliki Ucapan

Whisper digunakan untuk membaca ucapan dan mencari kandidat hook berbasis transkrip. Video tanpa dialog dapat menghasilkan pesan:

```text
Suara atau ucapan tidak terdeteksi pada video.
```

Untuk mendukung video tanpa dialog, pipeline dapat dikembangkan dengan pemilihan momen berbasis perubahan scene atau karakteristik audio tanpa transkripsi.

### Error Subtitle atau Path Windows

Pastikan server menjalankan `app.py` versi terbaru, kemudian restart Flask.

Pipeline yang didokumentasikan menggunakan path subtitle relatif agar drive letter Windows tidak ditafsirkan sebagai opsi FFmpeg.

### Video YouTube Tidak Tersedia

Periksa hal-hal berikut:

- URL tidak mengandung spasi atau karakter yang tidak diperlukan.
- Video dapat diakses dan bukan video privat yang tidak memiliki izin akses.
- Video tidak dihapus oleh pemiliknya atau oleh platform.
- Node.js tersedia apabila dibutuhkan oleh workflow ekstraksi.
- `yt-dlp` telah terpasang pada virtual environment yang digunakan aplikasi.

Jika masalah berlanjut, periksa pesan error dari `yt-dlp` untuk mengetahui penyebab spesifiknya.

## 📝 Catatan Pengembangan

- Folder `downloads/` digunakan untuk menyimpan file sementara dan hasil rendering. Jangan menghapus file yang sedang digunakan proses aktif.
- File asli yang diunggah tidak ditimpa; pipeline menggunakan file sumber sementara.
- Hasil lama dapat tetap tersimpan di `downloads/` jika proses berhenti sebelum cleanup selesai.
- Face tracking, B-roll otomatis, musik latar berlisensi, dan SFX belum menjadi bagian penuh dari pipeline lokal saat ini.
- Hasil AI tetap perlu ditinjau manusia sebelum dipublikasikan, terutama untuk akurasi subtitle, konteks hook, framing, dan klaim pada caption.

## ⚖️ Lisensi dan Penggunaan Konten

Gunakan hanya video, audio, musik, logo, dan aset lain yang kamu miliki atau yang penggunaannya telah mendapatkan izin yang sesuai.

Cutline merupakan alat pemrosesan video dan tidak memberikan hak atau izin atas konten YouTube maupun aset milik pihak ketiga. Pengguna bertanggung jawab memastikan bahwa pemrosesan, pengunduhan, pengeditan, dan publikasi konten mematuhi ketentuan platform serta hak cipta yang berlaku.