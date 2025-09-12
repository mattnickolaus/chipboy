from asyncio import Event
from textual import widgets
from textual.app import App, ComposeResult
from textual.events import Key
from textual.widget import Widget
from textual.widgets import Header, Footer, DataTable, Input, Static
from textual.coordinate import Coordinate
from notes import NoteEvent, get_next_note_in_scale, change_octave, note_frequency_chart
from sequencer import Track, Sequencer
import sounddevice as sd
import numpy as np
import threading
import time
import asyncio

import sequencer


class RealTimeNotePlayer:
    """Real-time note player for immediate feedback during editing"""
    
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.current_stream = None
        self.playing = False
        self.lock = threading.Lock()
        
    def generate_square_wave(self, frequency, duration, volume=0.1):
        """Generate a square wave for immediate playback"""
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        waveform = np.where((t * frequency) % 1 < 0.5, 1.0, -1.0)
        return (waveform * volume).astype(np.float32)
    
    def generate_sine_wave(self, frequency, duration, volume=0.1):
        """Generate a sine wave for immediate playback"""
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        waveform = np.sin(2 * np.pi * frequency * t)
        return (waveform * volume).astype(np.float32)
    
    def generate_sawtooth_wave(self, frequency, duration, volume=0.1):
        """Generate a sawtooth wave for immediate playback"""
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        waveform = 2 * ((t * frequency) % 1) - 1
        return (waveform * volume).astype(np.float32)
    
    def generate_noise(self, duration, volume=0.1):
        """Generate noise for immediate playback"""
        samples = int(self.sample_rate * duration)
        waveform = np.random.uniform(-1, 1, samples)
        return (waveform * volume).astype(np.float32)
    
    def play_note(self, note_name, duration=0.2, waveform_type='square'):
        """Play a note immediately, stopping any currently playing note"""
        if not note_name or note_name == "---":
            self.stop_note()
            return
            
        try:
            # Get frequency from note chart
            frequency = note_frequency_chart.get(note_name)
            if not frequency:
                return
                
            # Stop any currently playing note
            self.stop_note()
            
            # Generate wave based on waveform type
            if waveform_type == 'square':
                wave = self.generate_square_wave(frequency, duration, volume=0.05)
            elif waveform_type == 'sine':
                wave = self.generate_sine_wave(frequency, duration, volume=0.05)
            elif waveform_type == 'sawtooth':
                wave = self.generate_sawtooth_wave(frequency, duration, volume=0.05)
            elif waveform_type == 'noise':
                wave = self.generate_noise(duration, volume=0.05)
            else:
                # Default to square wave
                wave = self.generate_square_wave(frequency, duration, volume=0.05)
            
            with self.lock:
                self.playing = True
                self.current_stream = sd.play(wave, self.sample_rate)
                
        except Exception as e:
            print(f"Error playing note: {e}")
    
    def stop_note(self):
        """Stop the currently playing note"""
        with self.lock:
            if self.current_stream and self.playing:
                sd.stop()
                self.playing = False
                self.current_stream = None


class Phrases(Widget):

    def on_mount(self) -> None:
        # self.styles.border = ("round", "white")
        self.phrase = self.query_one(DataTable)
        self.phrase.show_header = True
        self.phrase.show_header=True
        self.phrase.show_row_labels=True
        self.phrase.zebra_stripes=True
        self.phrase.cursor_type="cell"

        self.phrase.add_columns("Note", "Duration", "Wave")

        for i in range(15):
            # row = ["----", "----", "------"] 
            row = ["----", "1/16", "square  "]
            self.phrase.add_row(*row, label=f"{i:02X}", key=f"{i:02X}")

        self.query_one("#edit_input").display = False
        self.selected_cell = Coordinate(0, 0)
        self.edit_mode = False  # Track if we're in note editing mode
        
        # Duration options (in 4:4 time signature)
        self.duration_options = ["1/32", "1/16", "1/8", "1/4", "1/2", "1"]
        
        # Wave options
        self.wave_options = ["square", "sine", "sawtooth", "noise"]
        
        # Initialize real-time note player
        self.note_player = RealTimeNotePlayer()
        
        # Playback highlighting
        self.playback_active = False
        self.current_playback_row = -1
        self.playback_highlight_task = None
        
        self.update_status_bar()


    def compose(self) -> ComposeResult:
        yield DataTable()
        yield Input(placeholder="Edit value", id="edit_input")


    def update_status_bar(self):
        """Update the status bar to show current mode and hotkeys"""
        # Find the status bar in the parent app
        app = self.app
        try:
            status_widget = app.query_one("#status_bar", Static)
            if self.edit_mode:
                status_text = "[EDIT MODE] | <ESC> Exit"
            elif self.playback_active:
                status_text = "[PLAYBACK] | Playing sequence..."
            else:
                status_text = "[NAVIGATION] | <Enter> Edit Cell | <Backspace> Clear Cell | <P> Play Sequence"
            
            status_widget.update(status_text)
        except:
            # Status bar not available, skip update
            pass


    def on_data_table_cell_selected(self, event: DataTable.CellSelected):
        row_key = event.coordinate.row
        column_index = event.coordinate.column

        self.selected_cell = Coordinate(row_key, column_index)
        print(f"Selected cell at row {row_key}, column {column_index}")


    def get_next_option(self, current_value, options, direction=1):
        """Get the next option in a list of options"""
        if not current_value or current_value == "----":
            return options[0] if direction > 0 else options[-1]
        
        try:
            current_index = options.index(current_value)
            new_index = current_index + direction
            
            # Handle wrapping
            if new_index >= len(options):
                new_index = 0
            elif new_index < 0:
                new_index = len(options) - 1
            
            return options[new_index]
        except ValueError:
            return options[0] if direction > 0 else options[-1]


    async def highlight_playback_row(self, row_index):
        """Highlight a specific row during playback"""
        if not self.playback_active:
            return
            
        # Clear previous highlight
        if self.current_playback_row >= 0:
            # self.phrase.get_row_at(self.current_playback_row).styles.background = None
            pass
        
        # Set new highlight
        if 0 <= row_index < 15:
            self.current_playback_row = row_index
            # self.phrase.get_row_at(row_index).styles.background = "blue"
        else:
            self.current_playback_row = -1


    async def playback_highlight_loop(self, bpm=120, num_loops=2):
        """Loop that highlights rows in time with the music"""
        self.playback_active = True
        self.update_status_bar()
        
        # Calculate time per 16th note (assuming 4/4 time signature)
        beats_per_measure = 4
        sixteenth_note_duration = 60.0 / bpm / 4  # seconds per 16th note
        
        total_loops = num_loops
        current_loop = 0
        
        try:
            while current_loop < total_loops and self.playback_active:
                # Highlight each row for the duration of a 16th note
                for row in range(15):
                    if not self.playback_active:
                        break
                    
                    # Highlight the current row
                    await self.highlight_playback_row(row)
                    
                    # Wait for the duration of a 16th note
                    await asyncio.sleep(sixteenth_note_duration)
                
                current_loop += 1
                
                # If we're looping, continue to the next loop
                if current_loop < total_loops and self.playback_active:
                    await asyncio.sleep(0.1)  # Small gap between loops
                    
        except Exception as e:
            print(f"Error in playback highlight loop: {e}")
        finally:
            # Clear highlight when done
            await self.highlight_playback_row(-1)
            self.playback_active = False
            self.update_status_bar()


    def on_key(self, event: Key) -> None:
        # Handle backspace to clear cells
        if event.key == "backspace":
            # Determine default value based on column
            if self.selected_cell.column == 0:  # Note column
                default_value = "----"
            elif self.selected_cell.column == 1:  # Duration column
                default_value = "1/16"
            else:  # Wave column
                default_value = "square"
            
            self.phrase.update_cell_at(self.selected_cell, default_value)
            event.stop()
            return
        
        # Handle ESC to exit edit mode
        if event.key == "escape":
            self.edit_mode = False
            # Stop any playing note when exiting edit mode
            self.note_player.stop_note()
            self.update_status_bar()
            event.stop()
            return
        
        # Handle Enter to enter edit mode for any column
        if event.key == "enter":
            # Get the current cursor position from the DataTable
            current_cursor = self.phrase.cursor_coordinate
            if current_cursor:
                self.selected_cell = current_cursor
            self.edit_mode = True
            
            # Play the current note when entering edit mode (only for note column)
            if self.selected_cell.column == 0:
                current_value = self.phrase.get_cell_at(self.selected_cell)
                if current_value and current_value != "----":
                    # Get duration and wave from the same row
                    duration_value = self.phrase.get_cell_at(Coordinate(self.selected_cell.row, 1))
                    wave_value = self.phrase.get_cell_at(Coordinate(self.selected_cell.row, 2))
                    
                    # Convert duration to seconds for playback
                    duration_seconds = 0.75  # default
                    if duration_value and duration_value != "----":
                        try:
                            numerator_str, denominator_str = duration_value.split("/")
                            numerator = int(numerator_str)
                            denominator = int(denominator_str)
                            # Convert to seconds (assuming 120 BPM)
                            duration_seconds = (numerator / denominator) * (60 / 120)
                        except:
                            duration_seconds = 0.75
                    
                    # Use specified wave type or default to square
                    wave_type = wave_value if wave_value and wave_value != "------" else "square"
                    
                    self.note_player.play_note(current_value, duration=duration_seconds, waveform_type=wave_type)
            
            self.update_status_bar()
            event.stop()
            return
        
        # Cell editing (only when in edit mode)
        if self.edit_mode:
            current_value = self.phrase.get_cell_at(self.selected_cell)
            
            if event.key in ["k", "up"]:  # up - next option
                if self.selected_cell.column == 0:  # Note column
                    new_value = get_next_note_in_scale(current_value, 1)
                    self.phrase.update_cell_at(self.selected_cell, new_value)
                    # Play the new note immediately with current duration and wave
                    self.play_current_note_with_settings(new_value)
                elif self.selected_cell.column == 1:  # Duration column
                    new_value = self.get_next_option(current_value, self.duration_options, 1)
                    self.phrase.update_cell_at(self.selected_cell, new_value)
                elif self.selected_cell.column == 2:  # Wave column
                    new_value = self.get_next_option(current_value, self.wave_options, 1)
                    self.phrase.update_cell_at(self.selected_cell, new_value)
                    # If we're editing wave, play the current note with new wave
                    note_value = self.phrase.get_cell_at(Coordinate(self.selected_cell.row, 0))
                    if note_value and note_value != "----":
                        self.play_current_note_with_settings(note_value)
                event.stop()
                return
            elif event.key in ["j", "down"]:  # down - previous option
                if self.selected_cell.column == 0:  # Note column
                    new_value = get_next_note_in_scale(current_value, -1)
                    self.phrase.update_cell_at(self.selected_cell, new_value)
                    # Play the new note immediately with current duration and wave
                    self.play_current_note_with_settings(new_value)
                elif self.selected_cell.column == 1:  # Duration column
                    new_value = self.get_next_option(current_value, self.duration_options, -1)
                    self.phrase.update_cell_at(self.selected_cell, new_value)
                elif self.selected_cell.column == 2:  # Wave column
                    new_value = self.get_next_option(current_value, self.wave_options, -1)
                    self.phrase.update_cell_at(self.selected_cell, new_value)
                    # If we're editing wave, play the current note with new wave
                    note_value = self.phrase.get_cell_at(Coordinate(self.selected_cell.row, 0))
                    if note_value and note_value != "----":
                        self.play_current_note_with_settings(note_value)
                event.stop()
                return
            elif event.key in ["l", "right"]:  # right - octave up (only for notes)
                if self.selected_cell.column == 0:  # Note column
                    new_value = change_octave(current_value, 1)
                    self.phrase.update_cell_at(self.selected_cell, new_value)
                    # Play the new note immediately with current duration and wave
                    self.play_current_note_with_settings(new_value)
                    event.stop()
                    return
            elif event.key in ["h", "left"]:  # left - octave down (only for notes)
                if self.selected_cell.column == 0:  # Note column
                    new_value = change_octave(current_value, -1)
                    self.phrase.update_cell_at(self.selected_cell, new_value)
                    # Play the new note immediately with current duration and wave
                    self.play_current_note_with_settings(new_value)
                    event.stop()
                    return
        
        # Vim-style navigation (only when not in edit mode)
        if not self.edit_mode:
            if event.key == "h":  # left
                if self.selected_cell.column > 0:
                    self.selected_cell = Coordinate(self.selected_cell.row, self.selected_cell.column - 1)
                    self.phrase.move_cursor(row=self.selected_cell.row, column=self.selected_cell.column)
            elif event.key == "l":  # right
                if self.selected_cell.column < 2:  # 3 columns (0-2)
                    self.selected_cell = Coordinate(self.selected_cell.row, self.selected_cell.column + 1)
                    self.phrase.move_cursor(row=self.selected_cell.row, column=self.selected_cell.column)
            elif event.key == "k":  # up
                if self.selected_cell.row > 0:
                    self.selected_cell = Coordinate(self.selected_cell.row - 1, self.selected_cell.column)
                    self.phrase.move_cursor(row=self.selected_cell.row, column=self.selected_cell.column)
            elif event.key == "j":  # down
                if self.selected_cell.row < 14:  # 15 rows (0-14)
                    self.selected_cell = Coordinate(self.selected_cell.row + 1, self.selected_cell.column)
                    self.phrase.move_cursor(row=self.selected_cell.row, column=self.selected_cell.column)
            elif event.key == "p":  # play phrase sequence
                self.play_phrase_sequence()
                event.stop()
                return
            elif event.key == "e":
                # row, col = self.selected_cell
                current_value = self.phrase.get_cell_at(self.selected_cell)
                input_widget = self.query_one("#edit_input", Input)
                input_widget.value = str(current_value)
                input_widget.compact = True
                input_widget.display = True
                input_widget.max_length = 4
                input_widget.focus()
            elif event.key == "t":  # test note
                new_value = "C 4"
                self.phrase.update_cell_at(self.selected_cell, new_value)
                # Set default duration and wave for this row
                self.phrase.update_cell_at(Coordinate(self.selected_cell.row, 1), "1/16")
                self.phrase.update_cell_at(Coordinate(self.selected_cell.row, 2), "square")
                test = Track("test")
                test.add_note(NoteEvent('C 4', start_beat=0, duration_beats=1, volume=0.1, waveform_type='sawtooth'))
                seq = Sequencer(bpm=120)
                seq.add_track(test)
                seq.play_once(1)

    def play_current_note_with_settings(self, note_value):
        """Play a note using the duration and wave settings from the current row"""
        if not note_value or note_value == "----":
            return
            
        # Get duration and wave from the same row
        duration_value = self.phrase.get_cell_at(Coordinate(self.selected_cell.row, 1))
        wave_value = self.phrase.get_cell_at(Coordinate(self.selected_cell.row, 2))
        
        # Convert duration to seconds for playback
        duration_seconds = 0.75  # default
        if duration_value and duration_value != "----":
            try:
                numerator_str, denominator_str = duration_value.split("/")
                numerator = int(numerator_str)
                denominator = int(denominator_str)
                # Convert to seconds (assuming 120 BPM)
                duration_seconds = (numerator / denominator) * (60 / 120)
            except:
                duration_seconds = 0.75
        
        # Use specified wave type or default to square
        wave_type = wave_value if wave_value and wave_value != "------" else "square"
        
        self.note_player.play_note(note_value, duration=duration_seconds, waveform_type=wave_type)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        new_value = event.value
        self.phrase.update_cell_at(self.selected_cell, new_value)
        self.query_one("#edit_input", Input).display = False

    def convert_table_to_track(self):
        """Convert the current table data to a Track with specified duration and wave values"""
        track = Track("phrase")
        
        # Get all notes from the table (15 rows)
        for row_index in range(15):
            # Get the note, duration, and wave from the columns
            note_value = self.phrase.get_cell_at(Coordinate(row_index, 0))
            duration_input = self.phrase.get_cell_at(Coordinate(row_index, 1))
            wave_value = self.phrase.get_cell_at(Coordinate(row_index, 2))
            
            # Skip empty notes (treat as rest)
            if not note_value or note_value == "----":
                continue

            # Each row represents a 16th note, so duration_beats = 0.25 (1/4) (1 being a quater note)
            duration_beats = 0.25
            if duration_input and duration_input != "----":
                try:
                    numerator_str, denominator_str = duration_input.split("/") 
                    numerator = int(numerator_str)
                    denominator = int(denominator_str)

                    duration_beats = (numerator / denominator) * 4 
                    # 1 is a quater note or beat, so if input is 1/4 I want the user to have a quater note meaning 1/4 * 4 = 1 quater note
                except:
                    duration_beats = 0.25  # Default to 16th note
                
            # start_beat is the row index * 0.25
            start_beat = row_index * 0.25
            
            # Use specified wave type or default to square
            wave_type = wave_value if wave_value and wave_value != "------" else "square"
            
            # Create NoteEvent and add to track
            note_event = NoteEvent(
                note=note_value,
                start_beat=start_beat,
                duration_beats=duration_beats,
                volume=0.1,
                waveform_type=wave_type
            )
            track.add_note(note_event)
        
        return track

    def play_phrase_sequence(self):
        """Play the current phrase as a sequence with row highlighting"""
        try:
            # Convert table to track
            track = self.convert_table_to_track()
            
            # Create sequencer and add track
            sequencer = Sequencer(bpm=120)
            sequencer.add_track(track)
            
            # Start the highlighting loop in the background
            self.playback_highlight_task = asyncio.create_task(
                self.playback_highlight_loop(bpm=120, num_loops=2)
            )
            
            # Play the sequence (4 beats = 1 measure of 16th notes)
            # sequencer.play_once(4)
            sequencer.loop_output_and_play(duration=4, num_of_loops=2)
            
        except Exception as e:
            print(f"Error playing phrase sequence: {e}")
            # Stop highlighting if there's an error
            self.playback_active = False
            self.update_status_bar()


class ChipBoy(App):
    TITLE = "ChipBoy"
    BINDINGS = [("p", "play_phrase_sequence", "Play")] #, (">", "toggle_dark", "Toggle Dark Mode")]

    CSS = """
    DataTable {
        height: 90%;
        width: 60%;
    }
    
    #status_bar {
        height: 1;
        background: $accent;
        color: $text;
        text-style: bold;
        padding: 0 1;
        width: 100%;
        margin-bottom: 0;
    }
    
    Footer {
        dock: bottom;
    }
    """

    def on_mount(self) -> None:
        self.theme = "tokyo-night"
        self.status_bar = self.query_one("#status_bar", Static)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(id="status_bar")
        yield Footer()
        yield Phrases()

    def action_toggle_dark(self) -> None:
        self.theme = ("textual-dark" if self.theme == "textual-light" else "textual-light")

if __name__ == "__main__":
    app = ChipBoy()
    app.run()
