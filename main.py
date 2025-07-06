import tkinter as tk
import numpy as np
import sounddevice as sd
import scipy.fft as ft
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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

        # Create a figure with 2 subplots: time and frequency
        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.ax_time = self.figure.add_subplot(211)
        self.ax_freq = self.figure.add_subplot(212)
        self.ax_time.set_title("Senoidal DTMF")
        self.ax_time.set_xlabel("Tiempo [s]")
        self.ax_time.set_ylabel("Amplitud")
        self.ax_time.grid(True)
        self.ax_freq.set_title("Espectro de Frecuencia (FFT)")
        self.ax_freq.set_xlabel("Frecuencia [Hz]")
        self.ax_freq.set_ylabel("Magnitud")
        self.ax_freq.grid(True)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        # Place the canvas to the right of the keypad
        self.canvas.get_tk_widget().grid(row=0, column=3, rowspan=7, padx=10, pady=5, sticky="nsew")

    def plot_tone(self, t, tone, char):
        # Time domain plot
        self.ax_time.clear()
        self.ax_time.plot(t, tone)
        self.ax_time.set_title(f"Senoidal DTMF '{char}'")
        self.ax_time.set_xlabel("Tiempo [s]")
        self.ax_time.set_ylabel("Amplitud")
        self.ax_time.set_xlim(0, 0.01)  # Show only the first 10 ms for clarity
        self.ax_time.grid(True)

        # Frequency domain plot
        self.ax_freq.clear()
        N = len(tone)
        yf = np.abs(ft.fft(tone))
        xf = np.fft.fftfreq(N, 1 / FS)
        # Only show positive frequencies up to 2500 Hz for DTMF
        idx = np.where((xf >= 0) & (xf <= 2500))
        self.ax_freq.stem(xf[idx], yf[idx], basefmt=" ")
        self.ax_freq.set_title("Espectro de Frecuencia (FFT)")
        self.ax_freq.set_xlabel("Frecuencia [Hz]")
        self.ax_freq.set_ylabel("Magnitud")
        self.ax_freq.set_xlim(0, 2500)
        self.ax_freq.grid(True)

        self.canvas.draw()

    def play_dtmf(self, char):
        if char not in DTMF_FREQS:
            return
        f1, f2 = DTMF_FREQS[char]
        t = np.linspace(0, DURATION, int(FS * DURATION), endpoint=False)
        tone = 0.5 * (np.sin(2 * np.pi * f1 * t) + np.sin(2 * np.pi * f2 * t))
        self.plot_tone(t, tone, char)
        self.update()  # Ensure GUI updates before playing sound
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