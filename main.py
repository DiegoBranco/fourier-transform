import tkinter as tk
import numpy as np
import sounddevice as sd
import scipy.fft as ft

DTMF_FREQS = {
    '1': (697, 1209), '2': (697, 1336), '3': (697, 1477),
    '4': (770, 1209), '5': (770, 1336), '6': (770, 1477),
    '7': (852, 1209), '8': (852, 1336), '9': (852, 1477),
    '0': (941, 1336), '*': (941, 1209), '#': (941, 1477),
}

DURATION = 0.25  # segundos
FS = 32768  # sampling rate


class NumPad(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        self.display = tk.Entry(self, width=20, font=('Arial', 18), justify='right')
        self.display.grid(row=0, column=0, columnspan=3, pady=5)

        buttons = [
            ('1', 1, 0), ('2', 1, 1), ('3', 1, 2),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2),
            ('7', 3, 0), ('8', 3, 1), ('9', 3, 2),
            ('*', 4, 0), ('0', 4, 1), ('#', 4, 2),
            ('C', 5, 1)
        ]

        for (text, row, col) in buttons:
            btn = tk.Button(self, text=text, width=5, height=2, font=('Arial', 16),
                            command=lambda t=text: self.on_button_click(t))
            btn.grid(row=row, column=col, padx=2, pady=2)

    def play_dtmf(self, char):
        if char not in DTMF_FREQS:
            return
        f1, f2 = DTMF_FREQS[char]
        t = np.linspace(0, DURATION, int(FS * DURATION), endpoint=False)
        tone = 0.5 * (np.sin(2 * np.pi * f1 * t) + np.sin(2 * np.pi * f2 * t))
        sd.play(tone, FS)
        sd.wait()

    def on_button_click(self, char):
        if char == 'C':
            self.display.delete(0, tk.END)
        else:
            self.display.insert(tk.END, char)
            self.play_dtmf(char)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Numerical Pad")
    app = NumPad(master=root)
    app.mainloop()