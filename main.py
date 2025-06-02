from notes import NoteEvent
from sequencer import Track, Sequencer

def main():
    note_durations = {
        'whole': 4,
        'half': 2,
        'quarter': 1,
        'eighth': 0.5,
        'sixteenth': 0.25
    }


    melody = Track()
    melody.add_note(NoteEvent('C4', start_beat=0, duration_beats=1, volume=0.05))
    melody.add_note(NoteEvent('G4', start_beat=1, duration_beats=1, volume=0.05))
    melody.add_note(NoteEvent('F4', start_beat=2, duration_beats=1, volume=0.05))
    melody.add_note(NoteEvent('D4', start_beat=3, duration_beats=1, volume=0.05))

    bass = Track()
    bass.add_note(NoteEvent("C2", start_beat=0, duration_beats=0.5, volume=0.3, waveform_type='sawtooth'))
    bass.add_note(NoteEvent("C2", start_beat=0.5, duration_beats=0.5, volume=0.3, waveform_type='sawtooth'))
    bass.add_note(NoteEvent("E2", start_beat=1, duration_beats=0.5, volume=0.3, waveform_type='sawtooth'))
    bass.add_note(NoteEvent("E2", start_beat=1.5, duration_beats=0.5, volume=0.3, waveform_type='sawtooth'))
    bass.add_note(NoteEvent("C2", start_beat=2, duration_beats=0.5, volume=0.3, waveform_type='sawtooth'))
    bass.add_note(NoteEvent("C2", start_beat=2.5, duration_beats=0.5, volume=0.3, waveform_type='sawtooth'))
    bass.add_note(NoteEvent("B2", start_beat=3, duration_beats=0.5, volume=0.3, waveform_type='sawtooth'))
    bass.add_note(NoteEvent("B2", start_beat=3.5, duration_beats=0.5, volume=0.3, waveform_type='sawtooth'))
    
    drums = Track()
    drums.add_note(NoteEvent("C4", start_beat=0, duration_beats=0.25, waveform_type='noise'))
    drums.add_note(NoteEvent("C4", start_beat=1, duration_beats=0.25, waveform_type='noise'))
    drums.add_note(NoteEvent("C4", start_beat=2, duration_beats=0.25, waveform_type='noise'))
    drums.add_note(NoteEvent("C4", start_beat=3, duration_beats=0.25, waveform_type='noise'))
    
    seq = Sequencer(bpm=120)
    seq.add_track(melody)
    seq.add_track(bass)
    seq.add_track(drums)

    # seq.play(total_duration=4)
    seq.loop(total_duration=4, num_of_loops=4)

if __name__ == '__main__':
    main()
