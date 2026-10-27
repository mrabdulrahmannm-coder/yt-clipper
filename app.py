# app.py
import os
import json
import re
import subprocess
import sys
import shutil
import uuid
import glob
from urllib.parse import urlparse
from flask import Flask, render_template, request, send_file, jsonify, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

# Direktori penyimpanan sementara
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), 'downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
WHISPER_MODEL = os.environ.get('CUTLINE_WHISPER_MODEL', 'base')
_whisper_model = None
ANALYSIS_DIR = os.path.join(DOWNLOAD_DIR, 'analysis')
os.makedirs(ANALYSIS_DIR, exist_ok=True)

# Regex validasi timestamp (HH:MM:SS atau MM:SS atau SS)
TIMESTAMP_REGEX = re.compile(r'^(\d{1,2}:)?([0-5]?\d:)?([0-5]?\d)$')

def is_valid_timestamp(ts: str) -> bool:
    return bool(TIMESTAMP_REGEX.fullmatch(ts.strip()))

def timestamp_to_seconds(ts: str) -> int:
    parts = [int(part) for part in ts.strip().split(':')]
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return parts[0] * 3600 + parts[1] * 60 + parts[2]

def is_youtube_url(url: str) -> bool:
    hostname = (urlparse(url).hostname or '').lower()
    return hostname in {'youtube.com', 'www.youtube.com', 'm.youtube.com',
                        'youtu.be', 'www.youtu.be'}

def find_js_runtime() -> str | None:
    for runtime in ('deno', 'node', 'bun'):
        if shutil.which(runtime):
            return runtime
    node_path = r'D:\node.exe'
    return node_path if os.path.exists(node_path) else None

def find_ffmpeg() -> str | None:
    executable = shutil.which('ffmpeg')
    if executable:
        return executable
    for candidate in (
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'WinGet',
                     'Packages', 'Gyan.FFmpeg.Shared_Microsoft.Winget.Source_8wekyb3d8bbwe',
                     'ffmpeg-*', 'bin', 'ffmpeg.exe'),
        r'C:\ffmpeg\bin\ffmpeg.exe',
    ):
        matches = glob.glob(candidate)
        if matches:
            return matches[0]
    return None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        _whisper_model = WhisperModel(WHISPER_MODEL, device='cpu', compute_type='int8')
    return _whisper_model

def format_srt_time(seconds: float) -> str:
    millis = int(max(0, seconds) * 1000)
    hours, millis = divmod(millis, 3600000)
    minutes, millis = divmod(millis, 60000)
    seconds, millis = divmod(millis, 1000)
    return f'{hours:02}:{minutes:02}:{seconds:02},{millis:03}'

def ass_escape(text: str) -> str:
    return text.replace('\\', r'\\').replace('{', r'\{').replace('}', r'\}')

def write_clip_subtitles(segments, start: float, end: float, path: str,
                         title: str = '', add_cta: bool = False) -> None:
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Arial,52,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80101010,1,0,2,70,70,300,1
Style: Title,Arial,62,&H006AF5D8,&H006AF5D8,&H00101010,&H90101010,1,0,8,70,70,130,1
Style: CTA,Arial,46,&H00FFFFFF,&H00FFFFFF,&H00101010,&H90101010,1,0,2,70,70,170,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    if title:
        events.append(f'Dialogue: 0,0:00:00.00,0:00:03.00,Title,,0,0,0,,{ass_escape(title)}')
    keyword_pattern = re.compile(
        r'\b(gula|jerawat|minggu ke enam|minggu keenam|ngidam|rahasia|penting)\b',
        re.IGNORECASE
    )
    for segment in segments:
        words = getattr(segment, 'words', None) or []
        if not words:
            words = [type('Word', (), {'start': segment.start, 'end': segment.end,
                                       'word': segment.text})]
        for offset in range(0, len(words), 4):
            chunk = words[offset:offset + 4]
            chunk_start = max(chunk[0].start, start) - start
            chunk_end = min(chunk[-1].end, end) - start
            if chunk_end <= 0 or chunk_start >= end - start:
                continue
            text = ' '.join(word.word.strip() for word in chunk).strip()
            text = re.sub(r'\s+', ' ', text)
            text = keyword_pattern.sub(r'{\\c&H006AF5D8&}\g<0>{\\c&H00FFFFFF&}', text)
            text = ass_escape(text).replace(r'\{\\c', r'{\c').replace(r'\&H', r'\&H')
            events.append(
                f'Dialogue: 0,{format_ass_time(chunk_start)},{format_ass_time(chunk_end)},'
                f'Caption,,0,0,0,,{text}'
            )
    if add_cta:
        clip_duration = max(0, end - start)
        cta_start = max(0, clip_duration - 3)
        events.append(
            f'Dialogue: 0,{format_ass_time(cta_start)},{format_ass_time(clip_duration)},'
            'CTA,,0,0,0,,Follow untuk part 2'
        )
    with open(path, 'w', encoding='utf-8-sig') as subtitle_file:
        subtitle_file.write(header + '\n'.join(events))

def format_ass_time(seconds: float) -> str:
    total = max(0, int(seconds * 100))
    hours, remainder = divmod(total, 360000)
    minutes, remainder = divmod(remainder, 6000)
    seconds, centiseconds = divmod(remainder, 100)
    return f'{hours}:{minutes:02}:{seconds:02}.{centiseconds:02}'

def ffmpeg_subtitle_path(path: str) -> str:
    project_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.relpath(path, project_dir).replace('\\', '/')

def load_video_for_analysis(video):
    original_name = secure_filename(video.filename or '')
    extension = os.path.splitext(original_name)[1].lower()
    if extension not in {'.mp4', '.mov', '.mkv', '.webm', '.avi', '.m4v'}:
        raise ValueError('Format video harus MP4, MOV, MKV, WEBM, AVI, atau M4V.')
    job_id = str(uuid.uuid4())[:8]
    source_path = os.path.join(ANALYSIS_DIR, f'source_{job_id}{extension}')
    video.save(source_path)
    return job_id, source_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/editor')
def editor():
    return render_template('editor.html')

@app.route('/api/download/<path:filename>')
def download_result(filename):
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)

@app.route('/api/preview/<path:filename>')
def preview_result(filename):
    return send_from_directory(DOWNLOAD_DIR, filename)

@app.errorhandler(413)
def request_too_large(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'File terlalu besar. Ukuran maksimal adalah 500 MB.'}), 413
    return error

@app.errorhandler(500)
def internal_server_error(error):
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Server gagal memproses video.',
            'details': 'Lihat terminal Flask untuk detail error.'
        }), 500
    return error

@app.route('/api/auto-edit', methods=['POST'])
def auto_edit():
    if not request.files.get('video'):
        return jsonify({'error': 'Pilih file video terlebih dahulu.'}), 400

    video = request.files['video']
    original_name = secure_filename(video.filename or '')
    extension = os.path.splitext(original_name)[1].lower()
    if extension not in {'.mp4', '.mov', '.mkv', '.webm', '.avi', '.m4v'}:
        return jsonify({'error': 'Format video harus MP4, MOV, MKV, WEBM, AVI, atau M4V.'}), 400

    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        return jsonify({'error': 'FFmpeg belum tersedia. Restart server setelah instalasi FFmpeg.'}), 503

    ffprobe = os.path.join(os.path.dirname(ffmpeg), 'ffprobe.exe')
    if not os.path.exists(ffprobe):
        ffprobe = shutil.which('ffprobe') or 'ffprobe'

    job_id = str(uuid.uuid4())[:8]
    source_path = os.path.join(DOWNLOAD_DIR, f'source_{job_id}{extension}')
    video.save(source_path)
    subtitle_paths = []
    try:
        probe = subprocess.run(
            [ffprobe, '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', source_path],
            capture_output=True, text=True, check=True, timeout=60
        )
        duration = float(probe.stdout.strip())
        if duration < 8:
            return jsonify({'error': 'Video terlalu pendek. Minimal durasi 8 detik.'}), 400

        model = get_whisper_model()
        transcript, _ = model.transcribe(
            source_path, vad_filter=True, beam_size=3, word_timestamps=True
        )
        segments = list(transcript)
        if not segments:
            return jsonify({'error': 'Suara atau ucapan tidak terdeteksi pada video.'}), 422

        keywords = ('cara', 'rahasia', 'penting', 'ternyata', 'masalah',
                    'jangan', 'kenapa', 'how', 'why', 'secret', 'mistake',
                    'important', 'but', 'however')
        ranked = sorted(
            segments,
            key=lambda item: (
                any(word in item.text.lower() for word in keywords),
                min(len(item.text.strip()), 120)
            ),
            reverse=True
        )
        clip_length = min(60.0, max(15.0, duration / 4))
        max_start = max(0.0, duration - clip_length)
        candidate_starts = [max(0.0, segment.start - 2.0) for segment in ranked[:3]]
        positions = [0.12, 0.5, 0.78] if duration >= 45 else [0.25, 0.6]
        candidate_starts.extend(duration * position for position in positions)
        clips = []
        used_starts = []
        for index, candidate_start in enumerate(candidate_starts, 1):
            start = min(max_start, candidate_start)
            if any(abs(start - previous) < 4 for previous in used_starts):
                continue
            used_starts.append(start)
            output_name = f'ai_clip_{job_id}_{index}.mp4'
            output_path = os.path.join(DOWNLOAD_DIR, output_name)
            subtitle_path = os.path.join(DOWNLOAD_DIR, f'subs_{job_id}_{index}.srt')
            subtitle_paths.append(subtitle_path)
            write_clip_subtitles(segments, start, start + clip_length, subtitle_path)
            subtitle_filter = (
                f"scale=1080:1920:force_original_aspect_ratio=increase,"
                f"crop=1080:1920,subtitles='{ffmpeg_subtitle_path(subtitle_path)}'"
            )
            subprocess.run([
                ffmpeg, '-y', '-ss', f'{start:.2f}', '-i', source_path,
                '-t', f'{clip_length:.2f}', '-vf', subtitle_filter,
                '-c:v', 'libx264', '-preset', 'fast', '-crf', '22',
                '-c:a', 'aac', '-movflags', '+faststart', output_path
            ], capture_output=True, text=True, check=True, timeout=600,
                cwd=os.path.dirname(os.path.abspath(__file__)))
            clips.append({
                'name': f'Highlight {index}',
                'start': round(start),
                'duration': round(clip_length),
                'url': f'/api/download/{output_name}',
                'preview': f'/api/preview/{output_name}',
                'hook': ' '.join(ranked[min(index - 1, len(ranked) - 1)].text.strip().split())[:140]
            })
            if len(clips) == 3:
                break
        return jsonify({
            'message': 'Video berhasil dianalisis dan clip otomatis dibuat.',
            'duration': round(duration),
            'clips': clips
        })
    except subprocess.CalledProcessError as error:
        details = (error.stderr or error.stdout or 'FFmpeg gagal menjalankan proses.').strip()
        return jsonify({'error': 'Video gagal dirender.', 'details': details[-1000:]}), 500
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Proses video terlalu lama dan dihentikan.'}), 504
    except (ValueError, OSError, RuntimeError, ImportError) as error:
        return jsonify({
            'error': 'AI gagal menganalisis video.',
            'details': str(error)
        }), 500
    finally:
        if os.path.exists(source_path):
            os.remove(source_path)
        for subtitle_path in subtitle_paths:
            if os.path.exists(subtitle_path):
                os.remove(subtitle_path)

@app.route('/api/analyze-video', methods=['POST'])
def analyze_video():
    if not request.files.get('video'):
        return jsonify({'error': 'Pilih file video terlebih dahulu.'}), 400
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        return jsonify({'error': 'FFmpeg belum tersedia.'}), 503
    try:
        job_id, source_path = load_video_for_analysis(request.files['video'])
        campaign_rules = request.form.get('campaign_rules', '').strip()
        subtitle_language = request.form.get('subtitle_language', 'same_as_speech')
        platform = request.form.get('platform', 'tiktok')
        clip_count = max(1, min(1, int(request.form.get('clip_count', '1'))))
        if not campaign_rules:
            campaign_rules = 'Gunakan aturan default Cutline: hook kuat, 9:16, subtitle maksimal 2 baris, tanpa konteks menyesatkan.'
        ffprobe = os.path.join(os.path.dirname(ffmpeg), 'ffprobe.exe')
        probe = subprocess.run(
            [ffprobe, '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', source_path],
            capture_output=True, text=True, check=True, timeout=60
        )
        duration = float(probe.stdout.strip())
        model = get_whisper_model()
        transcript, _ = model.transcribe(source_path, vad_filter=True, beam_size=3)
        segments = list(transcript)
        if not segments:
            os.remove(source_path)
            return jsonify({'error': 'Suara atau ucapan tidak terdeteksi pada video.'}), 422
        keywords = ('cara', 'rahasia', 'penting', 'ternyata', 'masalah',
                    'jangan', 'kenapa', 'how', 'why', 'secret', 'mistake')
        ranked = sorted(segments, key=lambda item: (
            any(word in item.text.lower() for word in keywords),
            min(len(item.text.strip()), 120)
        ), reverse=True)
        chosen = ranked[0]
        start = max(0.0, chosen.start - 2)
        end = min(duration, max(chosen.end + 35, start + 30))
        analysis = {
            'job_id': job_id, 'source_path': source_path, 'start': start,
            'end': end, 'duration': end - start,
            'campaign_rules': campaign_rules,
            'subtitle_language': subtitle_language,
            'platform': platform,
            'clip_count': clip_count,
            'hook': ' '.join(chosen.text.strip().split())[:180],
            'score': 8 if any(word in chosen.text.lower() for word in keywords) else 7,
            'reason': 'Kalimat memiliki sinyal hook dan dapat dimulai tanpa intro panjang.',
            'segments': [{'start': item.start, 'end': item.end, 'text': item.text,
                          'words': [{'start': word.start, 'end': word.end,
                                     'word': word.word}
                                    for word in (getattr(item, 'words', None) or [])]}
                         for item in segments]
        }
        with open(os.path.join(ANALYSIS_DIR, f'{job_id}.json'), 'w', encoding='utf-8') as file:
            json.dump(analysis, file, ensure_ascii=False)
        return jsonify({
            'job_id': job_id,
            'duration': round(duration),
            'candidate': {key: analysis[key] for key in ('start', 'end', 'duration', 'hook', 'score', 'reason')}
        })
    except (ValueError, OSError, RuntimeError, ImportError, subprocess.CalledProcessError) as error:
        return jsonify({'error': 'AI gagal menganalisis video.', 'details': str(error)}), 500

@app.route('/api/render-edit', methods=['POST'])
def render_edit():
    data = request.get_json() or {}
    job_id = data.get('job_id', '')
    analysis_path = os.path.join(ANALYSIS_DIR, f'{secure_filename(job_id)}.json')
    if not os.path.exists(analysis_path):
        return jsonify({'error': 'Sesi analisis tidak ditemukan. Upload ulang video.'}), 404
    with open(analysis_path, encoding='utf-8') as file:
        analysis = json.load(file)
    source_path = analysis['source_path']
    ffmpeg = find_ffmpeg()
    subtitle_path = os.path.join(DOWNLOAD_DIR, f'subs_{job_id}.srt')
    output_name = f'klip_01_hook_{job_id}.mp4'
    output_path = os.path.join(DOWNLOAD_DIR, output_name)
    try:
        segments = []
        for item in analysis['segments']:
            segment = type('Segment', (), item)
            segment.words = [type('Word', (), word) for word in item.get('words', [])]
            segments.append(segment)
        subtitle_title = ' '.join(analysis['hook'].split()[:8])
        write_clip_subtitles(
            segments, analysis['start'], analysis['end'], subtitle_path,
            title=subtitle_title, add_cta=True
        )
        subtitle_filter = (
            "split=2[base][subject];"
            "[base]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,gblur=sigma=28[blur];"
            "[subject]scale=1080:1920:force_original_aspect_ratio=decrease,"
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black@0[fit];"
            "[blur][fit]overlay=(W-w)/2:(H-h)/2,"
            f"subtitles='{ffmpeg_subtitle_path(subtitle_path)}'"
        )
        subprocess.run([
            ffmpeg, '-y', '-ss', str(analysis['start']), '-i', source_path,
            '-t', str(analysis['duration']), '-vf', subtitle_filter,
            '-c:v', 'libx264', '-preset', 'medium', '-b:v', '10M',
            '-maxrate', '12M', '-bufsize', '20M', '-r', '30',
            '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
            '-af', 'loudnorm=I=-14:TP=-1:LRA=11',
            '-movflags', '+faststart', output_path
        ], cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True, text=True, check=True, timeout=900)
        return jsonify({
            'message': 'Satu klip terbaik berhasil dirender.',
            'clip': {
                'name': 'Klip 01 — Hook utama', 'start': round(analysis['start']),
                'duration': round(analysis['duration']), 'hook': analysis['hook'],
                'score': analysis['score'], 'preview': f'/api/preview/{output_name}',
                'url': f'/api/download/{output_name}'
            }
        })
    except subprocess.CalledProcessError as error:
        return jsonify({'error': 'Video gagal dirender.', 'details': (error.stderr or '')[-1000:]}), 500
    finally:
        for path in (source_path, subtitle_path, analysis_path):
            if os.path.exists(path):
                os.remove(path)

@app.route('/api/health')
def health():
    return jsonify({
        'ready': find_ffmpeg() is not None,
        'ffmpeg': bool(find_ffmpeg()),
        'yt_dlp': True,
        'js_runtime': find_js_runtime(),
    })

@app.route('/api/cut', methods=['POST'])
def cut_video():
    data = request.get_json() or {}
    url = data.get('url', '').strip()
    start_time = data.get('start_time', '').strip()
    end_time = data.get('end_time', '').strip()

    if not url or not start_time or not end_time:
        return jsonify({'error': 'URL, start_time, dan end_time wajib diisi.'}), 400

    if not is_youtube_url(url):
        return jsonify({'error': 'Masukkan URL YouTube yang valid (youtube.com atau youtu.be).'}), 400
    if any(char.isspace() for char in url):
        return jsonify({
            'error': 'URL mengandung spasi. Salin ulang URL YouTube tanpa spasi.'
        }), 400

    if not is_valid_timestamp(start_time) or not is_valid_timestamp(end_time):
        return jsonify({'error': 'Format timestamp salah. Gunakan format MM:SS atau HH:MM:SS.'}), 400

    start_seconds = timestamp_to_seconds(start_time)
    end_seconds = timestamp_to_seconds(end_time)
    if end_seconds <= start_seconds:
        return jsonify({'error': 'Waktu selesai harus lebih besar dari waktu mulai.'}), 400
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        return jsonify({
            'error': 'FFmpeg belum terpasang atau belum masuk PATH.',
            'details': 'Install FFmpeg, tambahkan folder bin ke PATH, lalu restart terminal/server.'
        }), 503
    js_runtime = find_js_runtime()
    if not js_runtime:
        return jsonify({
            'error': 'Node.js, Deno, atau Bun belum tersedia untuk ekstraksi YouTube.',
            'details': 'Install Node.js atau Deno, lalu restart server.'
        }), 503

    job_id = str(uuid.uuid4())[:8]
    output_filename = f"clip_{job_id}.mp4"
    output_path = os.path.join(DOWNLOAD_DIR, output_filename)

    section_arg = f"*{start_time}-{end_time}"

    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--download-sections", section_arg,
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
        "--ffmpeg-location", os.path.dirname(ffmpeg),
        "--merge-output-format", "mp4",
        "--js-runtimes", js_runtime,
        "--remote-components", "ejs:github",
        "--force-overwrites",
        "--no-playlist",
        "-o", output_path,
        url
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, timeout=600
        )
        if os.path.exists(output_path):
            response = send_file(
                output_path,
                as_attachment=True,
                download_name=f"youtube_clip_{job_id}.mp4"
            )
            response.call_on_close(lambda: os.path.exists(output_path) and os.remove(output_path))
            return response
        return jsonify({
            'error': 'Proses selesai tetapi file output tidak ditemukan.',
            'details': result.stdout[-1000:]
        }), 500
    except FileNotFoundError:
        return jsonify({'error': 'Python virtualenv atau yt-dlp tidak dapat dijalankan.'}), 500
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Proses terlalu lama dan dihentikan. Coba video atau rentang yang lebih pendek.'}), 504
    except subprocess.CalledProcessError as e:
        details = (e.stderr or e.stdout or '').strip()
        if 'This video is not available' in details:
            return jsonify({
                'error': 'Video tidak tersedia.',
                'details': 'Video mungkin dihapus, private, dibatasi negara, atau URL bukan video yang valid.'
            }), 422
        return jsonify({
            'error': 'Gagal mengambil atau memotong video dari YouTube.',
            'details': details[-1000:] or 'yt-dlp tidak memberi detail error.'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)