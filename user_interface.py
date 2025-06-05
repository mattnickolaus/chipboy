from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Welcome

class ChipBoy(App):
    BINDINGS = [(">", "toggle_dark", "Toggle Dark Mode")]

    def compose(self) -> ComposeResult:
        yield Header(name="ChipBoy")
        yield Footer()
        # Replace with custom welcome widget
        yield Welcome()

    def action_toggle_dark(self) -> None:
        self.theme = ("textual-dark" if self.theme == "textual-light" else "textual-light")

if __name__ == "__main__":
    app = ChipBoy()
    app.run()
