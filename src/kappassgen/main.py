#!/usr/bin/env python3
import sys
import secrets
import gi
import html
import os

import importlib.resources

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gio, Gtk, Adw, Gdk

Adw.init()

# --- Carga de WORDS usando importlib.resources ---
try:
    WORDS_PATH = importlib.resources.files("kappassgen").joinpath("data/words.txt")
    with WORDS_PATH.open("r", encoding="utf-8") as f:
        WORDS = [line.strip() for line in f if line.strip()]
except AttributeError:
    # Método alternativo para versiones anteriores
    import pkg_resources
    WORDS_PATH = pkg_resources.resource_filename("kappassgen", "data/words.txt")
    with open(WORDS_PATH, "r", encoding="utf-8") as f:
        WORDS = [line.strip() for line in f if line.strip()]
except Exception:
    # Fallback para desarrollo local, carga relativa al script
    HERE = os.path.dirname(os.path.abspath(__file__))
    fallback_path = os.path.join(HERE, 'data', 'words.txt')
    with open(fallback_path, 'r', encoding='utf-8') as f:
        WORDS = [line.strip() for line in f if line.strip()]


if len(WORDS) < 1000:
    while len(WORDS) < 1000:
        WORDS += WORDS
    WORDS = WORDS[:1000]


def colorize_markup(text):
    out = []
    for ch in text:
        ch_real = html.unescape(ch)
        if ch_real.isalpha():
            out.append(f'<span foreground="black">{ch}</span>')
        elif ch_real.isdigit():
            out.append(f'<span foreground="#0077CC">{ch}</span>')
        else:
            safe_ch = ch.replace('&', '&amp;')
            out.append(f'<span foreground="#CC5500">{safe_ch}</span>')
    return "".join(out)

def clear_box(box):
    for child in list(box):
        box.remove(child)

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("KappassGen")
        self.set_default_size(650, 420)
        self.set_resizable(True)

        css = """
        switch {
            min-width: 34px;
            min-height: 20px;
            border-radius: 10px;
        }
        switch > slider {
            border-radius: 10px;
        }
        button.mode {
            padding: 6px 14px;
            border-radius: 6px;
            background-color: #d3d7cf;
            color: black;
        }
        button.mode.selected {
            background-color: #3465a4;
            color: white;
        }
        #password-label {
            font-family: monospace;
            font-size: 18px;
            min-width: 420px;
            max-width: 420px;
            min-height: 56px;
            max-height: 56px;
            border: 1px solid #ccc;
            border-radius: 6px;
            padding: 8px;
            background-color: #f8f8f8;
        }
        scale.fixed-width { min-width: 420px; max-width: 420px; }
        """

        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        root.set_margin_top(16)
        root.set_margin_bottom(16)
        root.set_margin_start(16)
        root.set_margin_end(16)
        self.set_content(root)

        header = Gtk.Label()
        header.set_markup("<span size='xx-large' weight='bold'>KappassGen</span>\nGenerador de contraseñas / passphrases")
        header.set_halign(Gtk.Align.CENTER)
        header.set_justify(Gtk.Justification.CENTER)
        root.append(header)

        mode_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        mode_row.set_halign(Gtk.Align.CENTER)
        root.append(mode_row)

        self.mode_password_btn = Gtk.ToggleButton(label="Contraseña aleatoria")
        self.mode_password_btn.get_style_context().add_class("mode")
        self.mode_password_btn.get_style_context().add_class("selected")
        self.mode_password_btn.set_active(True)
        self.mode_password_btn.connect("toggled", self.on_mode_toggled, "password")

        self.mode_passphrase_btn = Gtk.ToggleButton(label="Passphrase")
        self.mode_passphrase_btn.get_style_context().add_class("mode")
        self.mode_passphrase_btn.set_active(False)
        self.mode_passphrase_btn.connect("toggled", self.on_mode_toggled, "passphrase")

        mode_row.append(self.mode_password_btn)
        mode_row.append(self.mode_passphrase_btn)

        self.options_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.append(self.options_box)

        self.password_label = Gtk.Label()
        self.password_label.set_name("password-label")
        self.password_label.set_halign(Gtk.Align.CENTER)
        self.password_label.set_valign(Gtk.Align.CENTER)
        self.password_label.set_wrap(True)
        self.password_label.set_selectable(True)
        self.password_label.set_use_markup(True)
        self.password_label.set_justify(Gtk.Justification.CENTER)
        root.append(self.password_label)

        self.strength_label = Gtk.Label()
        self.strength_label.set_halign(Gtk.Align.CENTER)
        root.append(self.strength_label)

        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        buttons.set_halign(Gtk.Align.CENTER)
        root.append(buttons)

        self.btn_generate = Gtk.Button(label="Generar")
        self.btn_generate.connect("clicked", lambda b: self.generate())
        buttons.append(self.btn_generate)

        self.btn_copy = Gtk.Button(label="Copiar")
        self.btn_copy.connect("clicked", lambda b: self.copy_to_clipboard())
        buttons.append(self.btn_copy)

        self.btn_close = Gtk.Button(label="Cerrar")
        self.btn_close.connect("clicked", lambda b: self.close())
        buttons.append(self.btn_close)

        self.current_mode = "password"
        self.build_password_options()
        self.generate()

    def on_mode_toggled(self, button, mode):
        if not button.get_active():
            return
        if mode == "password":
            self.mode_passphrase_btn.set_active(False)
            self.mode_password_btn.get_style_context().add_class("selected")
            self.mode_passphrase_btn.get_style_context().remove_class("selected")
            self.current_mode = "password"
            self.build_password_options()
        else:
            self.mode_password_btn.set_active(False)
            self.mode_passphrase_btn.get_style_context().add_class("selected")
            self.mode_password_btn.get_style_context().remove_class("selected")
            self.current_mode = "passphrase"
            self.build_passphrase_options()
        self.generate()

    def build_password_options(self):
        clear_box(self.options_box)
        grid = Gtk.Grid(column_spacing=12, row_spacing=10)
        self.options_box.append(grid)

        lbl_upper = Gtk.Label(label="Mayúsculas")
        lbl_upper.set_halign(Gtk.Align.START)
        lbl_upper.set_valign(Gtk.Align.CENTER)
        self.sw_upper = Gtk.Switch()
        self.sw_upper.set_active(True)
        self.sw_upper.connect("notify::active", lambda w, p: self.generate())
        grid.attach(lbl_upper, 0, 0, 1, 1)
        grid.attach(self.sw_upper, 1, 0, 1, 1)

        lbl_numbers = Gtk.Label(label="Números")
        lbl_numbers.set_halign(Gtk.Align.START)
        lbl_numbers.set_valign(Gtk.Align.CENTER)
        self.sw_numbers = Gtk.Switch()
        self.sw_numbers.set_active(True)
        self.sw_numbers.connect("notify::active", lambda w, p: self.generate())
        grid.attach(lbl_numbers, 0, 1, 1, 1)
        grid.attach(self.sw_numbers, 1, 1, 1, 1)

        lbl_special = Gtk.Label(label="Caracteres especiales")
        lbl_special.set_halign(Gtk.Align.START)
        lbl_special.set_valign(Gtk.Align.CENTER)
        self.sw_special = Gtk.Switch()
        self.sw_special.set_active(True)
        self.sw_special.connect("notify::active", lambda w, p: self.generate())
        grid.attach(lbl_special, 0, 2, 1, 1)
        grid.attach(self.sw_special, 1, 2, 1, 1)

        lbl_len = Gtk.Label(label="Longitud")
        lbl_len.set_halign(Gtk.Align.START)
        lbl_len.set_valign(Gtk.Align.CENTER)
        self.adj_length = Gtk.Adjustment(value=16, lower=8, upper=64, step_increment=1)
        self.scale_length = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.adj_length)
        self.scale_length.set_digits(0)
        self.scale_length.set_hexpand(False)
        self.scale_length.set_valign(Gtk.Align.CENTER)
        self.scale_length.get_style_context().add_class("fixed-width")
        self.scale_length.connect("value-changed", lambda s: self.generate())
        grid.attach(lbl_len, 0, 3, 1, 1)
        grid.attach(self.scale_length, 1, 3, 1, 1)

    def build_passphrase_options(self):
        clear_box(self.options_box)
        grid = Gtk.Grid(column_spacing=12, row_spacing=10)
        self.options_box.append(grid)

        lbl_sep = Gtk.Label(label="Separador (usar guion)")
        lbl_sep.set_halign(Gtk.Align.START)
        lbl_sep.set_valign(Gtk.Align.CENTER)
        self.sw_sep = Gtk.Switch()
        self.sw_sep.set_active(True)
        self.sw_sep.connect("notify::active", lambda w, p: self.generate())
        grid.attach(lbl_sep, 0, 0, 1, 1)
        grid.attach(self.sw_sep, 1, 0, 1, 1)

        lbl_cap = Gtk.Label(label="Mayúsculas")
        lbl_cap.set_halign(Gtk.Align.START)
        lbl_cap.set_valign(Gtk.Align.CENTER)
        self.sw_capital = Gtk.Switch()
        self.sw_capital.set_active(False)
        self.sw_capital.connect("notify::active", lambda w, p: self.generate())
        grid.attach(lbl_cap, 0, 1, 1, 1)
        grid.attach(self.sw_capital, 1, 1, 1, 1)

        lbl_pp_num = Gtk.Label(label="Números (0-9)")
        lbl_pp_num.set_halign(Gtk.Align.START)
        lbl_pp_num.set_valign(Gtk.Align.CENTER)
        self.sw_pp_numbers = Gtk.Switch()
        self.sw_pp_numbers.set_active(False)
        self.sw_pp_numbers.connect("notify::active", lambda w, p: self.generate())
        grid.attach(lbl_pp_num, 0, 2, 1, 1)
        grid.attach(self.sw_pp_numbers, 1, 2, 1, 1)

        lbl_words = Gtk.Label(label="Número de palabras")
        lbl_words.set_halign(Gtk.Align.START)
        lbl_words.set_valign(Gtk.Align.CENTER)
        self.adj_words = Gtk.Adjustment(value=3, lower=3, upper=10, step_increment=1)
        self.scale_words = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.adj_words)
        self.scale_words.set_digits(0)
        self.scale_words.set_hexpand(False)
        self.scale_words.set_valign(Gtk.Align.CENTER)
        self.scale_words.get_style_context().add_class("fixed-width")
        self.scale_words.connect("value-changed", lambda s: self.generate())
        grid.attach(lbl_words, 0, 3, 1, 1)
        grid.attach(self.scale_words, 1, 3, 1, 1)

    def generate(self):
        if self.current_mode == "password":
            self._generate_random_password()
        else:
            self._generate_passphrase()

    def _generate_random_password(self):
        length = int(self.adj_length.get_value())
        use_upper = bool(self.sw_upper.get_active())
        use_numbers = bool(self.sw_numbers.get_active())
        use_special = bool(self.sw_special.get_active())

        lower = "abcdefghijklmnopqrstuvwxyz"
        upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if use_upper else ""
        numbers = "0123456789" if use_numbers else ""
        special = "!@#$%^&*()-_=+[]{};:,.<>?/" if use_special else ""

        pool = lower + upper + numbers + special
        if not pool:
            self.password_label.set_text("Selecciona al menos una categoría.")
            self.strength_label.set_text("")
            return

        pw = "".join(secrets.choice(pool) for _ in range(length))
        escaped_pw = html.escape(pw)
        self.password_label.set_markup(colorize_markup(escaped_pw))
        self._update_strength(pw)

    def _generate_passphrase(self):
        words_n = int(self.adj_words.get_value())
        use_sep = bool(self.sw_sep.get_active())
        use_caps = bool(self.sw_capital.get_active())
        use_nums = bool(self.sw_pp_numbers.get_active())

        sep = "-" if use_sep else ""
        selected = secrets.choice(WORDS) if words_n == 1 else [secrets.choice(WORDS) for _ in range(words_n)]

        if use_caps:
            selected = [w.capitalize() for w in selected]

        if use_nums:
            digits = [secrets.choice("0123456789") for _ in range(secrets.choice([1, 2]))]
            interleaved = []
            for i, word in enumerate(selected):
                interleaved.append(word)
                if i < len(selected) - 1:
                    interleaved.append(None)
            possible_positions = [0] + [i for i, v in enumerate(interleaved) if v is None] + [len(interleaved)]
            insert_positions = secrets.SystemRandom().sample(possible_positions, k=len(digits))
            insert_positions.sort()
            result = []
            idx_digit = 0
            for i in range(len(interleaved) + 1):
                if i in insert_positions:
                    result.append(digits[idx_digit])
                    idx_digit += 1
                if i < len(interleaved) and interleaved[i] is not None:
                    result.append(interleaved[i])
            phrase = sep.join(result)
        else:
            phrase = sep.join(selected)

        escaped_phrase = html.escape(phrase)
        self.password_label.set_markup(colorize_markup(escaped_phrase))
        self._update_strength(phrase)

    def _update_strength(self, text):
        length = len(text)
        categories = 0
        if any(c.islower() for c in text): categories += 1
        if any(c.isupper() for c in text): categories += 1
        if any(c.isdigit() for c in text): categories += 1
        if any(not c.isalnum() for c in text): categories += 1

        score = length + categories * 4
        if score < 24:
            label, color = "Débil", "#FF4500"
        elif score < 40:
            label, color = "Moderada", "#FFA500"
        else:
            label, color = "Fuerte", "#32CD32"

        self.strength_label.set_markup(f"<span foreground='{color}' weight='bold'>Seguridad: {label}</span>")

    def copy_to_clipboard(self):
        text = self.password_label.get_text()
        display = Gdk.Display.get_default()
        clipboard = display.get_clipboard()

        provider = Gdk.ContentProvider.new_for_value(text)
        clipboard.set_content(provider)


class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.kappa707.KappassGen", flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        win = MainWindow(self)
        win.present()

def main():
    app = App()
    app.run(sys.argv)

if __name__ == "__main__":
    main()

