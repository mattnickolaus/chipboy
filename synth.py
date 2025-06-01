import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
import time
import math


def generate_square_wave(frequency, duration, sample_rate=44100, duty_cycle=0.5, volume=0.1):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    waveform = np.where((t * frequency) % 1 < duty_cycle, 1.0, -1.0)
    # print(f"Square Waveform: {waveform}")
    return (waveform * volume).astype(np.float32)


def generate_noise(duration, sample_rate=44100, volume=0.1):
    samples = np.random.uniform(-1, 1, int(sample_rate * duration))
    # print(f"White noise: {samples}")
    return (samples * volume).astype(np.float32)


def generate_custom_waveform(waveform_data, frequency, duration, sample_rate=44100, volume=0.1):
    # Normalize input waveform to range [-1, 1]
    waveform_data = np.array(waveform_data, dtype=np.float32)
    waveform_data = waveform_data / np.max(np.abs(waveform_data))

    samples_per_cycle = int(sample_rate / frequency)
    num_cycles = int(duration * frequency)

    # Resize the waveform to match one cycle
    one_cycle = np.interp(
        np.linspace(0, len(waveform_data), samples_per_cycle, endpoint=False),
        np.arange(len(waveform_data)),
        waveform_data
    )
    # Repeat for the number of cycles needed for the duration
    full_wave = np.tile(one_cycle, num_cycles)
    return (full_wave * volume).astype(np.float32)
        

def generate_sine(data_steps = 120):
    pi = math.pi
    step = pi / data_steps
    sin_array = []
    for i in range(0, data_steps):
        value = i * step
        output = math.sin(value)
        sin_array.append(output)
    sin_array.append(0.0)
    return sin_array

def apply_envelope(wave, attack=0.01, decay=0.2, sustain_level=1, release=0.02, sample_rate=44100):
    length = len(wave)
    env = np.zeros(length)

    # Sample lengths
    attack_len = int(sample_rate * attack)
    decay_len = int(sample_rate * decay)
    release_len = int(sample_rate * release)

    sustain_start = attack_len + decay_len
    sustain_end = length - release_len
    sustain_len = max(sustain_end - sustain_start, 0)

    if attack_len > 0:
        env[:attack_len] = np.linspace(0.0, 1.0, attack_len)
    if decay_len > 0:
        env[attack_len:sustain_start] = np.linspace(1.0, sustain_level, decay_len)
    if sustain_len > 0:
        env[sustain_start:sustain_end] = sustain_level
    if release_len > 0:
        env[sustain_end:] = np.linspace(sustain_level, 0.0, release_len)

    if len(env) < length:
        env = np.pad(env, (0, length - len(env)), 'constant', constant_values=(0,))
    elif len(env) > length:
        env = env[:length]

    return wave * env

sine_wave = generate_custom_waveform(generate_sine(), frequency=261.63, duration=1.0, volume=2.0)

saw_tooth = [0.0, 0.33, 0.66, 1]
saw_tooth_wave = generate_custom_waveform(saw_tooth, frequency=261.63, duration=3.0)

wave = generate_square_wave(261.63, duration=1.0, duty_cycle=0.5)
noise = generate_noise(duration=0.5)

new_wave = apply_envelope(wave, attack=0.0, decay=0.3, sustain_level=1, release=0.1)
sd.play(new_wave, 44100)
sd.wait()
# sd.play(saw_tooth_wave, 44100)
# time.sleep(1.0)
# sd.play(sine_wave, 44100)
# time.sleep(1.0)
# sd.play(wave, 44100)
# time.sleep(1.0)
# sd.play(noise, 44100)
# sd.wait()

def play_drum_at_tempo(bpm, measures):
    time_period = 60 / bpm
    noise = generate_noise(duration=time_period)

    for i in range(measures):
        for i in range(4):
            sd.play(noise, 44100)
            time.sleep(time_period)
            # time.sleep(time_period - drum_duration)
        # time.sleep(3 * time_period)

# play_drum_at_tempo(128, 4)


# write("square.wav", 44100, wave)

