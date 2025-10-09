from synth import *


class NoteEvent:
    def __init__(self, note, start_beat, duration_beats, volume=0.1, waveform_type='square'):
        self.note = note
        self.frequency = note_frequency_chart[note]
        self.start_beat = start_beat
        self.duration_beats = duration_beats
        self.volume = volume
        self.waveform_type = waveform_type

    def render(self, bpm, sample_rate=44100):
        start_time = self.start_beat * (60 / bpm)
        duration = self.duration_beats * (60 / bpm)

        if self.waveform_type == 'square':
            wave = generate_square_wave(self.frequency, duration, sample_rate, volume=self.volume)
        elif self.waveform_type == 'sine':
            wave = generate_custom_waveform(generate_sine(), self.frequency, duration, sample_rate, volume=self.volume)
        elif self.waveform_type == 'sawtooth':
            wave = generate_custom_waveform([0, 0.33, 0.66, 1], self.frequency, duration, sample_rate, volume=self.volume)
        elif self.waveform_type == 'noise':
            wave = generate_noise(duration, sample_rate, volume=self.volume)
        else:
            raise ValueError("Unsupported waveform")

        wave = apply_envelope(wave)
        return start_time, wave


    def copy_with_offset_beats(self, beat_offset):
        return NoteEvent(
            note=self.note,
            start_beat=self.start_beat + beat_offset,
            duration_beats=self.duration_beats,
            volume=self.volume,
            waveform_type=self.waveform_type
        )


# Note editing helper functions
def parse_note(note_str):
    """Parse a note string like 'C 4' or 'C# 4' into (note_name, octave)"""
    if not note_str or note_str == "----":
        return None, None
    
    # Handle "C 4" and "C# 4" formats
    parts = note_str.split()
    if len(parts) != 2:
        return None, None
    
    note_name = parts[0]
    try:
        octave = int(parts[1])
    except ValueError:
        return None, None
    
    return note_name, octave


def format_note(note_name, octave):
    """Format note_name and octave into standard format 'C 4'"""
    return f"{note_name} {octave}"


def get_note_sequence():
    """Get the sequence of notes in chromatic order"""
    return ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def get_next_note_in_scale(current_note, direction=1):
    """Get the next note in the chromatic scale (direction: 1 for up, -1 for down)"""
    if not current_note or current_note == "---":
        return "C 4"  # Default starting note
    
    note_name, octave = parse_note(current_note)
    if note_name is None or octave is None:
        return "C 4"
    
    note_sequence = get_note_sequence()
    try:
        current_index = note_sequence.index(note_name)
        new_index = current_index + direction
        
        # Handle octave changes
        if new_index >= len(note_sequence):
            new_index = 0
            octave += 1
        elif new_index < 0:
            new_index = len(note_sequence) - 1
            octave -= 1
        
        # Clamp octave to valid range (0-8)
        octave = max(0, min(8, octave))
        
        new_note_name = note_sequence[new_index]
        return format_note(new_note_name, octave)
    except ValueError:
        return "C 4"


def change_octave(current_note, direction=1):
    """Change the octave of a note (direction: 1 for up, -1 for down)"""
    if not current_note or current_note == "---":
        return "C 4"  # Default starting note
    
    note_name, octave = parse_note(current_note)
    if note_name is None or octave is None:
        return "C 4"
    
    new_octave = octave + direction
    # Clamp octave to valid range (0-8)
    new_octave = max(0, min(8, new_octave))
    
    return format_note(note_name, new_octave)


note_frequency_chart = {
        # Octave 0
        "C 0":16.35,
        "C# 0":17.32,
        "D 0":18.35,
        "D# 0":19.45,
        "E 0":20.60,
        "F 0":21.83,
        "F# 0":23.12,
        "G 0":24.50,
        "G# 0":25.96,
        "A 0":27.50,
        "A# 0":29.14,
        "B 0":30.87,
        # Octave 1
        "C 1":32.70,
        "C# 1":34.65,
        "D 1":36.71,
        "D# 1":38.89,
        "E 1":41.20,
        "F 1":43.65,
        "F# 1":46.25,
        "G 1":49,
        "G# 1":51.91,
        "A 1":55,
        "A# 1":58.27,
        "B 1":61.74,
        # Octave 2
        "C 2":65.41,
        "C# 2":69.30,
        "D 2":73.42,
        "D# 2":77.78,
        "E 2":82.41,
        "F 2":87.31,
        "F# 2":92.50,
        "G 2":98,
        "G# 2":103.83,
        "A 2":110,
        "A# 2":116.54,
        "B 2":123.47,
        # Octave 3
        "C 3":130.81,
        "C# 3":138.59,
        "D 3":146.83,
        "D# 3":155.56,
        "E 3":164.81,
        "F 3":174.61,
        "F# 3":185,
        "G 3":196,
        "G# 3":207.65,
        "A 3":220,
        "A# 3":233.08,
        "B 3":246.94,
        # Octave 4
        "C 4":261.63,
        "C# 4":277.18,
        "D 4":293.66,
        "D# 4":311.13,
        "E 4":329.63,
        "F 4":349.23,
        "F# 4":369.99,
        "G 4":392,
        "G# 4":415.30,
        "A 4":440,
        "A# 4":466.16,
        "B 4":493.88,
        # Octave 5
        "C 5":523.25,
        "C# 5":554.37,
        "D 5":587.33,
        "D# 5":622.25,
        "E 5":659.25,
        "F 5":698.46,
        "F# 5":739.99,
        "G 5":783.99,
        "G# 5":830.61,
        "A 5":880, 
        "A# 5":932.33,
        "B 5":987.77,
        # Octave 6
        "C 6":1046.50,
        "C# 6":1108.73,
        "D 6":1174.66,
        "D# 6":1244.51,
        "E 6":1318.51,
        "F 6":1396.91,
        "F# 6":1479.98,
        "G 6":1567.98,
        "G# 6":1661.22,
        "A 6":1760, 
        "A# 6":1864.66,
        "B 6":1975.53,
        # Octave 7
        "C 7":2093.00,
        "C# 7":2217.46,
        "D 7":2349.32,
        "D# 7":2489.02,
        "E 7":2637.02,
        "F 7":2793.83,
        "F# 7":2959.96,
        "G 7":3135.96,
        "G# 7":3322.44,
        "A 7":3520, 
        "A# 7":3729.31,
        "B 7":3951.07,
        # Octave 8
        "C 8":4186.01,
        "C# 8":4434.92,
        "D 8":4698.63,
        "D# 8":4978.03,
        "E 8":5274.04,
        "F 8":5587.65,
        "F# 8":5919.91,
        "G 8":6271.93,
        "G# 8":6644.88,
        "A 8":7040, 
        "A# 8":7458.62,
        "B 8":7902.13,
        }
