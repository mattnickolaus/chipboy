from synth import *
from notes import *
import numpy as np

class Track:
    def __init__(self, name):
        self.notes = []
        self.name = name

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
    
    def loop_track(self, num_of_loops, phrase_duration_beats):
        original_notes = self.notes.copy()
        for i in range(1, num_of_loops): 
            beat_offset = i * phrase_duration_beats
            for note in original_notes:
                new_note = note.copy_with_offset_beats(beat_offset)
                self.notes.append(new_note)



class Sequencer:
    def __init__(self, bpm=120, sample_rate=44100):
        self.bpm = bpm
        self.tracks = []
        self.sample_rate = sample_rate

    def add_track(self, track):
        self.tracks.append(track)


    def setup_phrase_length(self, phrase_duration):
        total_duration = phrase_duration * (60 / self.bpm) 
        final_output = np.zeros(int(self.sample_rate * total_duration), dtype=np.float32)
        return final_output

    
    def combine_tracks(self, total_duration, final_output):
        total_duration = total_duration * (60 / self.bpm)
        combined = final_output
        for track in self.tracks:
            combined += track.render(self.bpm, total_duration, self.sample_rate)
        return combined


    def loop_output_and_play(self, duration, num_of_loops):  
        blank_output = self.setup_phrase_length(duration)
        combined_output = self.combine_tracks(duration, blank_output)

        original_combined_output = combined_output
        for i in range(1, num_of_loops):
            # Duplicating the np array to loop the track
            combined_output = np.append(combined_output, original_combined_output)

        self.play(combined_output)


    def normalize_output(self, final_output):
        max_val = np.max(np.abs(final_output))
        if max_val > 1.0:
            final_output = final_output / max_val
        return final_output


    def play(self, output):
        output = self.normalize_output(output)
        # Adding a buffer of 0.2 * sample_rate so stopping playback isn't so harsh
        extended_output = np.append(output, np.zeros(int(0.2 * self.sample_rate), dtype=np.float32))
        sd.play(extended_output, self.sample_rate)
        sd.wait()

    
    def play_once(self, duration):
        blank_output = self.setup_phrase_length(duration)
        combined_output = self.combine_tracks(duration, blank_output)
        self.play(combined_output)

