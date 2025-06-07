from asyncio import Event
from textual import widgets
from textual.app import App, ComposeResult
from textual.events import Key
from textual.widget import Widget
from textual.widgets import Header, Footer, DataTable, Input
from notes import NoteEvent
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
        self.selected_cell = (0, 0)


    def compose(self) -> ComposeResult:
        yield DataTable()
        yield Input(placeholder="Edit value", id="edit_input")


    def on_data_table_cell_selected(self, event: DataTable.CellSelected):
        row_key = event.coordinate.row
        column_index = event.coordinate.column

        self.selected_cell = (row_key, column_index)
        print(f"Selected cell at row {row_key}, column {column_index}")


    def on_key(self, event: Key) -> None:
        if event.key == "e":
            # row, col = self.selected_cell
            current_value = self.phrase.get_cell_at(self.selected_cell)
            input_widget = self.query_one("#edit_input", Input)
            input_widget.value = str(current_value)
            input_widget.compact = True
            input_widget.display = True
            input_widget.max_length = 3
            input_widget.focus()
        if event.key == "j":
            new_value = "C 4"
            self.phrase.update_cell_at(self.selected_cell, new_value)
            test = Track("test")
            test.add_note(NoteEvent('C4', start_beat=0, duration_beats=1, volume=0.1, waveform_type='sawtooth'))
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
