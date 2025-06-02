from synth import *
from notes import *
import numpy as np

class Track:
    def __init__(self):
        self.notes = []

    def add_note(self, note_event):
        self.notes.append(note_event)

    def render(self, bpm, total_duration, sample_rate=44100):
        final_wave = np.zeros(int(sample_rate * total_duration), dtype=np.float32)

        for note in self.notes:
            start_time, wave = note.render(bpm, sample_rate)
            start_index = int(start_time * sample_rate)
            end_index = start_index + len(wave)

            if end_index > len(final_wave):
                end_index = len(final_wave)
                wave = wave[:end_index - start_index]
            final_wave[start_index:end_index] += wave

        return final_wave

class Sequencer:
    def __init__(self, bpm=120, sample_rate=44100):
        self.bpm = bpm
        self.tracks = []
        self.sample_rate = sample_rate

    def add_track(self, track):
        self.tracks.append(track)

    def play(self, total_duration):
        total_duration = total_duration * (60 / self.bpm) + 0.2
        final_output = np.zeros(int(self.sample_rate * total_duration), dtype=np.float32)

        for track in self.tracks:
            final_output += track.render(self.bpm, total_duration, self.sample_rate)

        max_val = np.max(np.abs(final_output))
        if max_val > 1.0:
            final_output = final_output / max_val

        sd.play(final_output, self.sample_rate)
        sd.wait()

    def loop(self, total_duration, num_of_loops):
        total_duration = total_duration * (60 / self.bpm)
        final_output = np.zeros(int(self.sample_rate * total_duration), dtype=np.float32)

        for track in self.tracks:
            final_output += track.render(self.bpm, total_duration, self.sample_rate)

        max_val = np.max(np.abs(final_output))
        if max_val > 1.0:
            final_output = final_output / max_val

        original_final_output = final_output
        for i in range(num_of_loops):
            # Duplicating the np array to loop the track
            final_output = np.append(final_output, original_final_output)

        sd.play(final_output, self.sample_rate)
        sd.wait()
