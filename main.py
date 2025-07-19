import tkinter as tk
import numpy as np
import sounddevice as sd
import scipy.fft as ft
import tkinter.filedialog as fd
from scipy.io import wavfile
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


#Definicion de las frecuencias DTMF, Dada tecla produce un tono compuesto por dos frecuencuas
# - Una frecuencia de la fila (697-941 Hz)
# - Una frecuencia de la columna (1209-1477 Hz)

DTMF_FREQS = {
    '1': (697, 1209), '2': (697, 1336), '3': (697, 1477),
    '4': (770, 1209), '5': (770, 1336), '6': (770, 1477),
    '7': (852, 1209), '8': (852, 1336), '9': (852, 1477),
    '0': (941, 1336), '*': (941, 1209), '#': (941, 1477),
}

DURATION = 0.25  # Duracion de cada tono en segundos
FS = 32768  # Frecuencua de muestreo

#Var global para almacenar la secuencia de tonos introducida
tones = ""


class NumPad(tk.Frame):
    def __init__(self, master=None):
        #Iniciar la interfaz grafica
        super().__init__(master)
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        #Campo para mostrar la secuencia seleccionada
        self.display = tk.Entry(self, width=20, font=('Arial', 18), justify='right')
        self.display.grid(row=0, column=0, columnspan=3, pady=2)
        #Boton de reproduccion
        self.play_button = tk.Button(self, text="▶", width=5, height=2, font=('Arial', 16)
                                     ,command=self.on_play_button)
        self.play_button.grid(row=5, column=2, padx=2, pady=2)
        #Configurando los botones en el teclado numerico
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

        # Boton para importar y decodificar archivo WAV
        import_btn = tk.Button(self, text="Importar WAV", width=12, height=2, font=('Arial', 12),
                               command=self.import_and_decode_wav)
        import_btn.grid(row=6, column=0, columnspan=3, pady=5)

        # Boton para exportar el sonido DTMF a un archivo WAV
        export_btn = tk.Button(self, text="Exportar WAV", width=12, height=2, font=('Arial', 12),
                           command=self.export_wav)
        export_btn.grid(row=7, column=0, columnspan=3, pady=5)


        #Crea una figura con 2 subgráficas: tiempo y frecuencia
        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.ax_time = self.figure.add_subplot(211)
        self.ax_freq = self.figure.add_subplot(212)
        #Configuracion grafica de tiempo
        self.ax_time.set_title("Senoidal DTMF")
        self.ax_time.set_xlabel("Tiempo [s]")
        self.ax_time.set_ylabel("Amplitud")
        self.ax_time.grid(True)
        #Configuracion grafica de frecuencia
        self.ax_freq.set_title("Espectro de Frecuencia (FFT)")
        self.ax_freq.set_xlabel("Frecuencia [Hz]")
        self.ax_freq.set_ylabel("Magnitud")
        self.ax_freq.grid(True)
        self.figure.subplots_adjust(hspace=0.5)
        # Canvas integrado con Tkinter
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().grid(row=0, column=3, rowspan=7, padx=10, pady=5, sticky="nsew")

    def plot_tone(self, t, tone, char):
        # Grafica la señal DTMF en el dominio tiempo y frecuencia
        # Amplitud por tiempo
        self.ax_time.clear()
        self.ax_time.plot(t, tone)
        self.ax_time.set_title(f"Senoidal DTMF '{char}'")
        self.ax_time.set_xlabel("Tiempo [s]")
        self.ax_time.set_ylabel("Amplitud")
        self.ax_time.set_xlim(0, 0.01)  # Es ciclica, asi que mostramos solo 10 ms
        self.ax_time.grid(True)

        # Magnitud por frecuencia usando FFT
        self.ax_freq.clear()
        N = len(tone)
        yf = np.abs(ft.fft(tone))  # Transformada de Fourier
        xf = np.fft.fftfreq(N, 1 / FS) # Frecuencuas correspondientes

        # Filtrar solo frecuencias positivas hasta 2500 Hz 
        idx = np.where((xf >= 0) & (xf <= 2500))
        self.ax_freq.stem(xf[idx], yf[idx], basefmt=" ")
        self.ax_freq.set_title("Espectro de Frecuencia (FFT)")
        self.ax_freq.set_xlabel("Frecuencia [Hz]")
        self.ax_freq.set_ylabel("Magnitud")
        self.ax_freq.set_xlim(0, 2500)
        self.ax_freq.grid(True)

        #Actualizar grafica
        self.canvas.draw()

    def play_dtmf(self, char):
        #GEnera y reproduce un tono DTMF para el caracter especificado
        if char not in DTMF_FREQS:
            return
        
        #Frecuencias correspondientes
        f1, f2 = DTMF_FREQS[char]
        #Generar vector de tiempo
        t = np.linspace(0, DURATION, int(FS * DURATION), endpoint=False)
        #Generar el tono DTMF como combinacion de dos senoidales
        tone = 0.5 * (np.sin(2 * np.pi * f1 * t) + np.sin(2 * np.pi * f2 * t))
        
        #Mostrar graficas y actualizar la interfaz
        self.plot_tone(t, tone, char)
        self.update()  #actualiza la GUI
        #Reproduce el tono
        sd.play(tone, FS)
        sd.wait()

    def on_button_click(self, char):
        #Manejo del evento de click en un boton del teclado
        global tones
        if char == 'C':
            #Limpiar el display y la secuencia de tonos
            self.display.delete(0, tk.END)
            tones = ""
        else:
            #Agregar caracter al display y la secuencia
            self.display.insert(tk.END, char)
            tones += char
            #Reproducir el tono correspondiente
            self.play_dtmf(char)

    def export_wav(self):
        #Exporta la secuencia de tonos generada a un archivo WAV
        global tones
        if not tones:
            return
        #Generar vector de tiempo
        t = np.linspace(0, DURATION, int(FS * DURATION), endpoint=False)
        audio = np.array([], dtype=np.float32)
        #Generar tono por cada caracter en la secuencia
        for char in tones:
            if char in DTMF_FREQS:
                f1, f2 = DTMF_FREQS[char]
                tone = 0.5 * (np.sin(2 * np.pi * f1 * t) + np.sin(2 * np.pi * f2 * t))
                audio = np.concatenate((audio, tone))
        # Normalizar el audio a 16 bits
        audio_int16 = np.int16(audio / np.max(np.abs(audio)) * 32767)
        file_path = fd.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV files", "*.wav")])
        if file_path:
            #Guardar el archivo
            wavfile.write(file_path, FS, audio_int16)

    def on_play_button(self):
        #Reproduce toda la secuencia de tonos generada
        global tones
        for char in tones:
            self.play_dtmf(char)

    def import_and_decode_wav(self):
        #Importa un archivo WAV y decodifica la secuencia DTMF usando FFT
        global tones
        tones = ""
        #PEdir el WAV
        file_path = fd.askopenfilename(filetypes=[("WAV files", "*.wav")])
        if not file_path:
            return
        #Leer el archivo
        fs, data = wavfile.read(file_path)

        #Caso estereo (utilizar un solo canal)
        if data.ndim > 1:
            data = data[:, 0]  # usa solo un canal si es estéreo

        #Normalizar los datos si no estan en float
        if data.dtype != np.float32:
            data = data / np.max(np.abs(data))

        # Parametros para el analisis
        window_size = int(0.1 * fs)  # 100 ms tamaño
        step_size = int(0.25 * fs)   # 25 ms separacion
        detected = [] #Guarda los caracteres detectados

        #Analisis del audio por ventana

        for start in range(0, len(data) - window_size, step_size):
            window = data[start:start + window_size]
            #Calcular el espectro de frecuencia
            spectrum = np.abs(np.fft.rfft(window))
            freqs = np.fft.rfftfreq(window_size, 1/fs)

            # Busca picos que coincidan con las frecuencias DTMF
            for key, (f1, f2) in DTMF_FREQS.items():
                idx1 = np.argmin(np.abs(freqs - f1))
                idx2 = np.argmin(np.abs(freqs - f2))
                if spectrum[idx1] > 0.3 * np.max(spectrum) and spectrum[idx2] > 0.3 * np.max(spectrum):
                    detected.append(key)
                    break

        # Mostrar y almacenar la secuencia detectada
        print("Decoded DTMF sequence:", ''.join(detected))
        self.display.delete(0, tk.END)
        self.display.insert(0, ''.join(detected))        
        tones = ''.join(detected)
        #Reproducir la secuencia detectada
        self.on_play_button()




if __name__ == "__main__":
    root = tk.Tk()
    root.title("fourer-transform")
    app = NumPad(master=root)
    app.mainloop()