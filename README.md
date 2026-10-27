# Cutline — AI Video Clipper

Cutline adalah aplikasi web lokal untuk mengubah video panjang menjadi klip
short-form untuk TikTok, Instagram Reels, dan YouTube Shorts.

Aplikasi ini menggunakan Flask sebagai backend, FFmpeg untuk pemrosesan video,
dan Whisper lokal untuk membaca ucapan serta mencari kandidat hook.

## Fitur

- Memotong video YouTube berdasarkan URL dan timestamp.
- Upload video lokal melalui halaman AI Editor.
- Deteksi ucapan menggunakan `faster-whisper`.
- Pemilihan satu kandidat hook terbaik.
- Alur analisis dan persetujuan sebelum render final.
- Subtitle otomatis berbasis timestamp kata.
- Format vertikal 9:16 dengan background blur agar video landscape tidak
  terpotong secara ekstrem.
- Hook text pada awal video.
- CTA pada akhir video.
- Normalisasi audio sekitar -14 LUFS.
- Export MP4 H.264 dengan resolusi 1080x1920.
- Preview video hasil edit langsung dari browser.
- Download hasil edit.
- Animasi upload dan progress proses.
- Campaign brief yang dapat diubah dari halaman editor.

## Teknologi

- Python 3.13
- Flask
- `yt-dlp`
- `faster-whisper`
- FFmpeg
- Node.js sebagai JavaScript runtime untuk ekstraksi YouTube
- HTML, CSS, dan JavaScript tanpa framework frontend

## Struktur Project

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

### File penting

- `app.py` — Flask application, API, analisis Whisper, dan pipeline FFmpeg.
- `templates/index.html` — halaman manual YouTube clipper.
- `templates/editor.html` — halaman AI Editor untuk upload dan review hasil.
- `requirements.txt` — dependency Python.
- `downloads/` — penyimpanan sementara dan hasil video.

## Persyaratan Sistem

Pastikan tersedia:

- Windows 10 atau Windows 11.
- Python 3.10 atau lebih baru.
- FFmpeg.
- Node.js.
- Koneksi internet saat pertama kali mengunduh model Whisper.

FFmpeg dan Node.js dibutuhkan untuk workflow yang berbeda:

- FFmpeg digunakan untuk membaca, memotong, merender, dan meng-encode video.
- Node.js membantu `yt-dlp` menangani ekstraksi YouTube.

## Instalasi

Masuk ke folder project:

```powershell
cd D:\ABDUL\xampp\htdocs\yt-clipper
```

Jika virtual environment belum ada:

```powershell
python -m venv venv
```

Aktifkan virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependency:

```powershell
python -m pip install -r requirements.txt
```

Install FFmpeg jika belum ada:

```powershell
winget install --id Gyan.FFmpeg.Shared --exact --source winget
```

Node.js dapat dipasang melalui:

```powershell
winget install OpenJS.NodeJS.LTS
```

Setelah instalasi FFmpeg atau Node.js, tutup dan buka kembali terminal agar
perubahan PATH terbaca.

## Menjalankan Aplikasi

```powershell
cd D:\ABDUL\xampp\htdocs\yt-clipper
.\venv\Scripts\python.exe app.py
```

Buka halaman berikut di browser:

```text
http://localhost:5000
```

Halaman AI Editor:

```text
http://localhost:5000/editor
```

Untuk menghentikan server:

```text
CTRL + C
```

## Workflow AI Editor

### 1. Upload

Buka `/editor`, lalu pilih atau drag-and-drop video. Format yang didukung:

- MP4
- MOV
- MKV
- WEBM
- AVI
- M4V

Ukuran upload maksimal adalah 500 MB.

### 2. Analisis

Whisper lokal akan:

1. Membaca audio video.
2. Membuat transkrip dengan timestamp.
3. Mencari kalimat yang memiliki sinyal hook.
4. Memberikan kandidat dengan skor viralitas.
5. Menampilkan timestamp, durasi, hook, dan alasan pemilihan.

### 3. Review

Aplikasi menampilkan satu kandidat hook terlebih dahulu. Video belum dirender
sebagai hasil final pada tahap ini.

### 4. Approve dan render

Klik **APPROVE & RENDER CLIP** untuk membuat satu video final. Output meliputi:

- Satu klip terbaik.
- Format 9:16.
- Video sumber tetap terlihat utuh di atas background blur.
- Subtitle otomatis.
- Hook text maksimal delapan kata di awal.
- CTA pada bagian akhir.
- Audio AAC 192 kbps pada 48 kHz.
- Video H.264 dengan bitrate target sekitar 10 Mbps.

Model Whisper default yang dipakai adalah `base`. Pada proses pertama, model
akan diunduh dan proses dapat berlangsung lebih lama.

## Mengganti Model Whisper

Model dapat diubah menggunakan environment variable:

```powershell
$env:CUTLINE_WHISPER_MODEL="small"
.\venv\Scripts\python.exe app.py
```

Pilihan umum:

| Model | Kecepatan | Akurasi |
|---|---:|---:|
| `tiny` | Paling cepat | Rendah |
| `base` | Seimbang | Baik untuk penggunaan umum |
| `small` | Lebih lambat | Lebih akurat |
| `medium` | Paling berat | Lebih akurat, membutuhkan resource besar |

## Campaign Brief

Panel **Campaign Brief** tersedia pada halaman `/editor`. Panel ini digunakan
untuk menjelaskan aturan editing, misalnya:

- Platform tujuan.
- Bahasa subtitle.
- Jumlah klip.
- Durasi target.
- Aturan hook.
- Aturan framing.
- Larangan watermark.
- Format output.
- Aturan caption dan hashtag.

Aturan campaign sebaiknya ditulis secara eksplisit. Contoh:

```text
MODE: AUTO
JUMLAH KLIP: 1
DURASI: 30-60 detik
WAJIB: hook kuat dalam 3 detik pertama, subtitle maksimal 2 baris
DILARANG: crop wajah, klaim palsu, watermark pihak lain
TEKNIS: MP4 H.264, 1080x1920, 30 fps
POSTING: buat caption dan hashtag sesuai isi video
```

## API

### Health check

```http
GET /api/health
```

Memeriksa status FFmpeg, `yt-dlp`, dan JavaScript runtime.

### Analisis video

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

Respons berisi `job_id` dan kandidat hook.

### Render hasil

```http
POST /api/render-edit
Content-Type: application/json
```

Body:

```json
{
  "job_id": "id-hasil-analisis"
}
```

### Preview hasil

```http
GET /api/preview/<filename>
```

### Download hasil

```http
GET /api/download/<filename>
```

### Manual YouTube clipping

```http
POST /api/cut
Content-Type: application/json
```

Body:

```json
{
  "url": "https://www.youtube.com/watch?v=...",
  "start_time": "01:00",
  "end_time": "02:00"
}
```

## Troubleshooting

### FFmpeg belum ditemukan

Periksa status:

```powershell
.\venv\Scripts\python.exe -c "import sys; sys.path.insert(0, '.'); import app; print(app.find_ffmpeg())"
```

Jika hasilnya `None`, pasang FFmpeg:

```powershell
winget install --id Gyan.FFmpeg.Shared --exact --source winget
```

Restart terminal dan server setelah instalasi.

### Model Whisper belum tersedia

Jalankan server dan upload video. Model `base` akan diunduh otomatis pada
analisis pertama. Pastikan koneksi internet tersedia.

### Video tidak memiliki ucapan

Whisper membutuhkan suara atau ucapan manusia untuk mencari hook. Video tanpa
dialog dapat menghasilkan pesan:

```text
Suara atau ucapan tidak terdeteksi pada video.
```

Gunakan video dengan percakapan atau ubah pipeline agar memilih momen berbasis
scene/audio tanpa transkripsi.

### Error subtitle atau path Windows

Pastikan server menggunakan `app.py` terbaru dan restart Flask. Pipeline sudah
menggunakan path subtitle relatif agar drive letter Windows tidak dibaca sebagai
opsi FFmpeg.

### Video YouTube tidak tersedia

Pastikan:

- URL tidak mengandung spasi.
- Video bersifat publik.
- Video tidak dihapus atau private.
- Node.js tersedia.
- `yt-dlp` sudah terpasang di virtual environment.

## Catatan Pengembangan

- Folder `downloads/` berisi file sementara dan hasil render. Jangan menghapus
  file yang sedang digunakan oleh proses aktif.
- File asli upload tidak ditimpa; proses menggunakan file sumber sementara.
- Beberapa hasil lama dapat tetap berada di `downloads/` jika proses dihentikan
  sebelum cleanup selesai.
- Face tracking, B-roll otomatis, musik latar berlisensi, dan SFX belum menjadi
  bagian penuh dari pipeline lokal saat ini.
- Hasil AI tetap perlu direview manusia sebelum dipublikasikan, terutama untuk
  akurasi subtitle, konteks hook, framing, dan klaim pada caption.

## Lisensi dan Penggunaan Konten

Gunakan hanya video, audio, musik, logo, dan aset yang kamu miliki atau memang
memiliki izin untuk diproses dan dipublikasikan. Aplikasi ini tidak memberikan
izin atas konten YouTube atau aset pihak ketiga.
#   y t - c l i p p e r  
 