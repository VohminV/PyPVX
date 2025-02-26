import json
import base64
import subprocess
import tempfile
import zlib

def mp4_to_pvx(mp4_file, pvx_file):
    # Временные файлы для кодированного видео и аудио
    video_file = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
    audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".flac")

    # Кодируем видео в VP9 без потери качества (параметры для сжатия без потерь)
    subprocess.run([
        "ffmpeg", "-i", mp4_file, "-c:v", "libvpx-vp9", "-lossless", "1", video_file.name, "-y"
    ], check=True)

    # Кодируем аудио в FLAC без потерь
    subprocess.run([
        "ffmpeg", "-i", mp4_file, "-c:a", "flac", audio_file.name, "-y"
    ], check=True)

    # Читаем сжатые данные и кодируем их в base64
    with open(video_file.name, "rb") as vf, open(audio_file.name, "rb") as af:
        video_base64 = base64.b64encode(vf.read()).decode('utf-8')
        audio_base64 = base64.b64encode(af.read()).decode('utf-8')

    # Формируем PVX-структуру
    pvx_data = {
        "video": video_base64,
        "audio": audio_base64
    }

    # Сжимаем PVX-структуру с использованием zlib для уменьшения размера
    pvx_json = json.dumps(pvx_data, indent=2)
    compressed_pvx = zlib.compress(pvx_json.encode('utf-8'))

    # Сохраняем сжатый PVX-файл
    with open(pvx_file, "wb") as f:
        f.write(compressed_pvx)

    print(f"Файл {pvx_file} успешно создан с сжатием!")

# Использование
mp4_to_pvx("input.mp4", "output.pvx")
