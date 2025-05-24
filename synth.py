import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write


def generate_square_wave(frequency, duration, sample_rate=44100, duty_cycle=0.5, volume=0.3):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    waveform = np.where((t * frequency) % 1 < duty_cycle, 1.0, -1.0)
    return (waveform * volume).astype(np.float32)

wave = generate_square_wave(440, duration=1.0, duty_cycle=0.5)

write("square.wav", 44100, wave)

