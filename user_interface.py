from asyncio import Event
from textual import widgets
from textual.app import App, ComposeResult
from textual.events import Key
from textual.widget import Widget
from textual.widgets import Header, Footer, DataTable, Input
from textual.coordinate import Coordinate
from notes import NoteEvent, get_next_note_in_scale, change_octave
from sequencer import Track, Sequencer


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


    def compose(self) -> ComposeResult:
        yield DataTable()
        yield Input(placeholder="Edit value", id="edit_input")


    def on_data_table_cell_selected(self, event: DataTable.CellSelected):
        row_key = event.coordinate.row
        column_index = event.coordinate.column

        self.selected_cell = Coordinate(row_key, column_index)
        print(f"Selected cell at row {row_key}, column {column_index}")


    def on_key(self, event: Key) -> None:
        # Handle ESC to exit edit mode
        if event.key == "escape":
            self.edit_mode = False
            return
        
        # Handle Enter to enter edit mode (only for Note column)
        if event.key == "enter" and self.selected_cell.column == 0:
            self.edit_mode = True
            return
        
        # Note editing (only when in edit mode and in Note column)
        if self.edit_mode and self.selected_cell.column == 0:
            current_value = self.phrase.get_cell_at(self.selected_cell)
            
            if event.key == "k" or event.key == "up":  # up - next note in scale
                new_value = get_next_note_in_scale(current_value, 1)
                self.phrase.update_cell_at(self.selected_cell, new_value)
                return
            elif event.key == "j" or event.key == "down":  # down - previous note in scale
                new_value = get_next_note_in_scale(current_value, -1)
                self.phrase.update_cell_at(self.selected_cell, new_value)
                return
            elif event.key == "l" or event.key == "right":  # right - octave up
                new_value = change_octave(current_value, 1)
                self.phrase.update_cell_at(self.selected_cell, new_value)
                return
            elif event.key == "h" or event.key == "left":  # left - octave down
                new_value = change_octave(current_value, -1)
                self.phrase.update_cell_at(self.selected_cell, new_value)
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
            elif event.key == "e":
                # row, col = self.selected_cell
                current_value = self.phrase.get_cell_at(self.selected_cell)
                input_widget = self.query_one("#edit_input", Input)
                input_widget.value = str(current_value)
                input_widget.compact = True
                input_widget.display = True
                input_widget.max_length = 3
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



class ChipBoy(App):
    TITLE = "ChipBoy"
    BINDINGS = [(">", "toggle_dark", "Toggle Dark Mode")]

    CSS = """
    DataTable {
        height: 90%;
        width: 60%;
    }
    """

    def on_mount(self) -> None:
        self.theme = "tokyo-night"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Phrases()

    def action_toggle_dark(self) -> None:
        self.theme = ("textual-dark" if self.theme == "textual-light" else "textual-light")

if __name__ == "__main__":
    app = ChipBoy()
    app.run()
