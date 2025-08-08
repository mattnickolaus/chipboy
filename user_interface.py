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
    
    def play_note(self, note_name, duration=0.2):
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
            
            # Generate and play the new note
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

        self.phrase.add_columns("Note", "Instrument", "Command", "Value")

        for i in range(16):
            row = ["---", "--", "--", "--"]
            self.phrase.add_row(*row, label=f"{i:02X}", key=f"{i:02X}")

        self.query_one("#edit_input").display = False
        self.selected_cell = Coordinate(0, 0)
        self.edit_mode = False  # Track if we're in note editing mode
        
        # Initialize real-time note player
        self.note_player = RealTimeNotePlayer()
        
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
            else:
                status_text = "[NAVIGATION] | <Enter> Edit Note | <Backspace> Clear Cell | <P> Play Sequence"
            
            status_widget.update(status_text)
        except:
            # Status bar not available, skip update
            pass


    def on_data_table_cell_selected(self, event: DataTable.CellSelected):
        row_key = event.coordinate.row
        column_index = event.coordinate.column

        self.selected_cell = Coordinate(row_key, column_index)
        print(f"Selected cell at row {row_key}, column {column_index}")


    def on_key(self, event: Key) -> None:
        # Handle backspace to clear cells
        if event.key == "backspace":
            # Determine default value based on column
            if self.selected_cell.column == 0:  # Note column
                default_value = "---"
            else:  # Instrument, Command, Value columns
                default_value = "--"
            
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
        
        # Handle Enter to enter edit mode (only for Note column)
        if event.key == "enter" and self.selected_cell.column == 0:
            # Get the current cursor position from the DataTable
            current_cursor = self.phrase.cursor_coordinate
            if current_cursor:
                self.selected_cell = current_cursor
            self.edit_mode = True
            # Play the current note when entering edit mode
            current_value = self.phrase.get_cell_at(self.selected_cell)
            if current_value and current_value != "---":
                self.note_player.play_note(current_value, duration=0.75)
            self.update_status_bar()
            event.stop()
            return
        
        # Note editing (only when in edit mode and in Note column)
        if self.edit_mode and self.selected_cell.column == 0:
            current_value = self.phrase.get_cell_at(self.selected_cell)
            
            if event.key in ["k", "up"]:  # up - next note in scale
                new_value = get_next_note_in_scale(current_value, 1)
                self.phrase.update_cell_at(self.selected_cell, new_value)
                # Play the new note immediately
                self.note_player.play_note(new_value, duration=0.75)
                event.stop()
                return
            elif event.key in ["j", "down"]:  # down - previous note in scale
                new_value = get_next_note_in_scale(current_value, -1)
                self.phrase.update_cell_at(self.selected_cell, new_value)
                # Play the new note immediately
                self.note_player.play_note(new_value, duration=0.75)
                event.stop()
                return
            elif event.key in ["l", "right"]:  # right - octave up
                new_value = change_octave(current_value, 1)
                self.phrase.update_cell_at(self.selected_cell, new_value)
                # Play the new note immediately
                self.note_player.play_note(new_value, duration=0.75)
                event.stop()
                return
            elif event.key in ["h", "left"]:  # left - octave down
                new_value = change_octave(current_value, -1)
                self.phrase.update_cell_at(self.selected_cell, new_value)
                # Play the new note immediately
                self.note_player.play_note(new_value, duration=0.75)
                event.stop()
                return
        
        # Vim-style navigation (only when not in edit mode)
        if not self.edit_mode:
            if event.key == "h":  # left
                if self.selected_cell.column > 0:
                    self.selected_cell = Coordinate(self.selected_cell.row, self.selected_cell.column - 1)
                    self.phrase.move_cursor(row=self.selected_cell.row, column=self.selected_cell.column)
            elif event.key == "l":  # right
                if self.selected_cell.column < 3:  # 4 columns (0-3)
                    self.selected_cell = Coordinate(self.selected_cell.row, self.selected_cell.column + 1)
                    self.phrase.move_cursor(row=self.selected_cell.row, column=self.selected_cell.column)
            elif event.key == "k":  # up
                if self.selected_cell.row > 0:
                    self.selected_cell = Coordinate(self.selected_cell.row - 1, self.selected_cell.column)
                    self.phrase.move_cursor(row=self.selected_cell.row, column=self.selected_cell.column)
            elif event.key == "j":  # down
                if self.selected_cell.row < 15:  # 16 rows (0-15)
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
                test = Track("test")
                test.add_note(NoteEvent('C 4', start_beat=0, duration_beats=1, volume=0.1, waveform_type='sawtooth'))
                seq = Sequencer(bpm=120)
                seq.add_track(test)
                seq.play_once(1)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        new_value = event.value
        self.phrase.update_cell_at(self.selected_cell, new_value)
        self.query_one("#edit_input", Input).display = False

    def convert_table_to_track(self):
        """Convert the current table data to a Track with 16th notes"""
        track = Track("phrase")
        
        # Get all notes from the table (16 rows)
        for row_index in range(16):
            # Get the note from the first column (Note column)
            note_value = self.phrase.get_cell_at(Coordinate(row_index, 0))
            
            # Skip empty notes (treat as rest)
            if not note_value or note_value == "---":
                continue
                
            # Each row represents a 16th note, so duration_beats = 0.25 (1/4)
            # start_beat is the row index * 0.25
            start_beat = row_index * 0.25
            duration_beats = 0.25
            
            # Create NoteEvent and add to track
            note_event = NoteEvent(
                note=note_value,
                start_beat=start_beat,
                duration_beats=duration_beats,
                volume=0.1,
                waveform_type='sawtooth' # 'square'  # Default to square wave
            )
            track.add_note(note_event)
        
        return track

    def play_phrase_sequence(self):
        """Play the current phrase as a sequence"""
        try:
            # Convert table to track
            track = self.convert_table_to_track()
            
            # Create sequencer and add track
            sequencer = Sequencer(bpm=120)
            sequencer.add_track(track)
            
            # Play the sequence (4 beats = 1 measure of 16th notes)
            # sequencer.play_once(4)
            sequencer.loop_output_and_play(duration=4, num_of_loops=2)
            
        except Exception as e:
            print(f"Error playing phrase sequence: {e}")


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
