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


    melody = Track("melody")
    melody.add_note(NoteEvent('G5', start_beat=0, duration_beats=4, volume=0.05, waveform_type='sawtooth'))
    melody.add_note(NoteEvent('G5', start_beat=4, duration_beats=1, volume=0.05, waveform_type='sawtooth'))
    melody.add_note(NoteEvent('F5', start_beat=5, duration_beats=3, volume=0.05, waveform_type='sawtooth'))
    melody.add_note(NoteEvent('F5', start_beat=8, duration_beats=1, volume=0.05, waveform_type='sawtooth'))
    melody.add_note(NoteEvent('G5', start_beat=9, duration_beats=3, volume=0.05, waveform_type='sawtooth'))

    bass = Track("bass")
    bass.add_note(NoteEvent("C2", start_beat=0, duration_beats=0.5, volume=0.3, waveform_type='sawtooth'))
    bass.add_note(NoteEvent("C2", start_beat=0.5, duration_beats=0.5, volume=0.3, waveform_type='sawtooth'))
    bass.add_note(NoteEvent("E2", start_beat=1, duration_beats=0.5, volume=0.3, waveform_type='sawtooth'))
    bass.add_note(NoteEvent("E2", start_beat=1.5, duration_beats=0.5, volume=0.3, waveform_type='sawtooth'))
    bass.add_note(NoteEvent("C2", start_beat=2, duration_beats=0.5, volume=0.3, waveform_type='sawtooth'))
    bass.add_note(NoteEvent("C2", start_beat=2.5, duration_beats=0.5, volume=0.3, waveform_type='sawtooth'))
    bass.add_note(NoteEvent("B2", start_beat=3, duration_beats=0.5, volume=0.3, waveform_type='sawtooth'))
    bass.add_note(NoteEvent("B2", start_beat=3.5, duration_beats=0.5, volume=0.3, waveform_type='sawtooth'))
    bass.loop_track(num_of_loops=3, phrase_duration_beats=4)
    
    drums = Track("drums")
    drums.add_note(NoteEvent("C4", start_beat=0, duration_beats=0.25, waveform_type='noise'))
    drums.add_note(NoteEvent("C4", start_beat=1, duration_beats=0.25, waveform_type='noise'))
    drums.add_note(NoteEvent("C4", start_beat=2, duration_beats=0.25, waveform_type='noise'))
    drums.add_note(NoteEvent("C4", start_beat=3, duration_beats=0.25, waveform_type='noise'))
    drums.loop_track(num_of_loops=3, phrase_duration_beats=4)

    
    seq = Sequencer(bpm=120)
    seq.add_track(melody)
    seq.add_track(bass)
    seq.add_track(drums)

    # seq.play_once(duration=12)
    seq.loop_output_and_play(duration=12, num_of_loops=2)

if __name__ == '__main__':
    main()
