import sys
import json
import base64
import zlib
import tempfile
import cv2
import numpy as np
import pygame
from pydub import AudioSegment
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QLabel, QSlider
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt


class PVXPlayer(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PVX Video Player")
        self.setGeometry(100, 100, 900, 600)

        # Видео-область
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)

        # Кнопки управления
        self.open_button = QPushButton("Open PVX")
        self.open_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 16px; padding: 10px;")
        self.open_button.clicked.connect(self.open_file)

        self.play_button = QPushButton("Play")
        self.play_button.setStyleSheet("background-color: #2196F3; color: white; font-size: 16px; padding: 10px;")
        self.play_button.setEnabled(False)
        self.play_button.clicked.connect(self.play_video)

        self.pause_button = QPushButton("Pause")
        self.pause_button.setStyleSheet("background-color: #FFC107; color: white; font-size: 16px; padding: 10px;")
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self.pause_video)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setStyleSheet("background-color: #F44336; color: white; font-size: 16px; padding: 10px;")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_video)

        # Полоса громкости
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.set_volume)

        # Layouts
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.open_button)
        button_layout.addWidget(self.play_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.stop_button)

        volume_layout = QHBoxLayout()
        volume_label = QLabel("Volume:")
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_slider)

        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        layout.addLayout(button_layout)
        layout.addLayout(volume_layout)

        self.setLayout(layout)

        # Таймер обновления кадров
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.video_path = None
        self.audio_path = None
        self.cap = None
        self.audio_playing = False

        # Инициализация pygame.mixer
        pygame.mixer.init()

    def open_file(self):
        file_dialog = QFileDialog(self)
        pvx_file, _ = file_dialog.getOpenFileName(self, "Open PVX File", "", "PVX Files (*.pvx)")

        if pvx_file:
            self.video_path, self.audio_path = self.extract_pvx(pvx_file)
            if self.video_path and self.audio_path:
                self.play_button.setEnabled(True)

    def extract_pvx(self, pvx_file):
        """ Декомпрессия PVX-файла и извлечение видео/аудио """
        with open(pvx_file, "rb") as f:
            compressed_data = f.read()

        decompressed_data = zlib.decompress(compressed_data)
        pvx_data = json.loads(decompressed_data)

        video_data = base64.b64decode(pvx_data["video"])
        audio_data = base64.b64decode(pvx_data["audio"])

        video_file = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
        with open(video_file.name, "wb") as vf:
            vf.write(video_data)

        # Сохраняем аудиофайл перед обработкой
        audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".flac")
        with open(audio_file.name, "wb") as af:
            af.write(audio_data)

        # Конвертация FLAC → WAV
        wav_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        audio = AudioSegment.from_file(audio_file.name, format="flac")
        audio.export(wav_file.name, format="wav")

        return video_file.name, wav_file.name

    def play_video(self):
        if self.video_path:
            self.cap = cv2.VideoCapture(self.video_path)
            if not self.cap.isOpened():
                print("Ошибка открытия видео")
                return

            self.play_audio()
            self.timer.start(30)

            self.play_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            self.stop_button.setEnabled(True)

    def play_audio(self):
        """ Воспроизведение WAV через pygame """
        pygame.mixer.music.load(self.audio_path)
        pygame.mixer.music.set_volume(self.volume_slider.value() / 100.0)
        pygame.mixer.music.play()
        self.audio_playing = True

    def pause_video(self):
        if self.cap and self.audio_playing:
            self.timer.stop()
            pygame.mixer.music.pause()
            self.audio_playing = False
            self.play_button.setEnabled(True)

    def stop_video(self):
        if self.cap:
            self.cap.release()
            self.timer.stop()
            self.video_label.clear()

        pygame.mixer.music.stop()
        self.audio_playing = False

        self.play_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)

    def update_frame(self):
        if self.cap:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                height, width, channel = frame.shape
                bytes_per_line = 3 * width
                qimg = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
                self.video_label.setPixmap(QPixmap.fromImage(qimg))
            else:
                self.stop_video()

    def set_volume(self, value):
        """ Изменение громкости pygame.mixer """
        pygame.mixer.music.set_volume(value / 100.0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = PVXPlayer()
    player.show()
    sys.exit(app.exec_())
