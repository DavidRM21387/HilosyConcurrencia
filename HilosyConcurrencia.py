import tkinter as tk
from tkinter import ttk
import threading
import time
import random

class LineaProduccion(threading.Thread):
    def __init__(self, nombre, callback_actualizacion, callback_contador, callback_progreso):
        super().__init__()
        self.nombre = nombre
        self.callback_actualizacion = callback_actualizacion
        self.callback_contador = callback_contador
        self.callback_progreso = callback_progreso
        self._detener = False

    def detener(self):
        self._detener = True

    def run(self):
        try:
            self.callback_contador(1)  # Incrementar contador
            self.callback_progreso(self.nombre, 0)  # Inicializar progreso
            
            for i in range(1, 11):  # Cambiado de 6 a 11 (1-10 piezas)
                if self._detener:
                    self.callback_actualizacion(self.nombre, "Detenida por el usuario.")
                    return
                
                tiempo = random.uniform(0.5, 1.5)
                time.sleep(tiempo)

                # Simular error aleatorio - cambiado de 0.1 (10%) a 0.3 (30%)
                if random.random() < 0.3:
                    raise Exception("Falla técnica inesperada.")

                self.callback_actualizacion(self.nombre, f"Produciendo pieza {i}/10")
                # Actualizar barra de progreso
                progreso = (i / 10) * 100
                self.callback_progreso(self.nombre, progreso)

            # Mensaje final modificado
            self.callback_actualizacion(self.nombre, "✔️ Producción completada exitosamente")
            self.callback_progreso(self.nombre, 100)
            
        except Exception as e:
            self.callback_actualizacion(self.nombre, f"❌ Error: {str(e)}")
        finally:
            self.callback_contador(-1)  # Decrementar contador al finalizar

class SimuladorApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Simulador de Fábrica Concurrente - Mejorado")
        self.master.geometry("600x500")
        self.lineas = []
        self.area_estado = {}
        self.barras_progreso = {}
        self.hilos_activos = 0

        # Frame superior para controles
        self.frame_superior = tk.Frame(master)
        self.frame_superior.pack(pady=10)

        self.entrada_nombre = tk.Entry(self.frame_superior, width=30)
        self.entrada_nombre.pack(side=tk.LEFT, padx=5)
        self.entrada_nombre.insert(0, "Línea A")

        self.boton_agregar = tk.Button(self.frame_superior, text="Agregar línea", command=self.agregar_linea)
        self.boton_agregar.pack(side=tk.LEFT, padx=5)

        # Frame para botones de control
        self.frame_botones = tk.Frame(master)
        self.frame_botones.pack(pady=10)

        self.boton_iniciar = tk.Button(self.frame_botones, text="Iniciar producción", command=self.iniciar_produccion)
        self.boton_iniciar.pack(side=tk.LEFT, padx=5)

        # Nuevo boton para detener todas las líneas
        self.boton_detener = tk.Button(self.frame_botones, text="Detener todas las líneas", 
                                     command=self.detener_todas_lineas, bg="red", fg="white")
        self.boton_detener.pack(side=tk.LEFT, padx=5)

        self.etiqueta_hilos = tk.Label(master, text="Hilos activos: 0", font=("Arial", 12, "bold"))
        self.etiqueta_hilos.pack(pady=5)

        # Frame con scroll para resultados
        self.frame_scroll = tk.Frame(master)
        self.frame_scroll.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(self.frame_scroll)
        self.scrollbar = ttk.Scrollbar(self.frame_scroll, orient="vertical", command=self.canvas.yview)
        self.area_resultados = tk.Frame(self.canvas)

        self.area_resultados.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.area_resultados, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def agregar_linea(self):
        nombre = self.entrada_nombre.get().strip()
        if not nombre:
            return
        if nombre in self.area_estado:
            return

        # Frame para cada linea
        frame_linea = tk.Frame(self.area_resultados, relief=tk.RIDGE, bd=1)
        frame_linea.pack(fill=tk.X, padx=5, pady=2)

        # Etiqueta de estado
        etiqueta = tk.Label(frame_linea, text=f"{nombre}: En espera", anchor="w", width=40)
        etiqueta.pack(anchor="w", padx=5, pady=2)

        # Barra de progreso
        barra_progreso = ttk.Progressbar(frame_linea, length=300, mode='determinate')
        barra_progreso.pack(fill=tk.X, padx=5, pady=2)

        self.area_estado[nombre] = etiqueta
        self.barras_progreso[nombre] = barra_progreso
        self.lineas.append((nombre, None))
        
        # Limpiar entrada y generar siguiente nombre
        self.entrada_nombre.delete(0, tk.END)
        siguiente_letra = chr(ord(nombre[-1]) + 1) if nombre[-1] < 'Z' else 'A'
        self.entrada_nombre.insert(0, f"Línea {siguiente_letra}")

    def actualizar_estado(self, nombre, mensaje):
        if nombre in self.area_estado:
            self.area_estado[nombre].config(text=f"{nombre}: {mensaje}")

    def actualizar_progreso(self, nombre, valor):
        if nombre in self.barras_progreso:
            self.barras_progreso[nombre]['value'] = valor

    def actualizar_contador_hilos(self, delta):
        self.hilos_activos += delta
        self.etiqueta_hilos.config(text=f"Hilos activos: {self.hilos_activos}")
        
        # Cambiar color segun el numero de hilos
        if self.hilos_activos == 0:
            self.etiqueta_hilos.config(fg="green")
        elif self.hilos_activos < 3:
            self.etiqueta_hilos.config(fg="orange")
        else:
            self.etiqueta_hilos.config(fg="red")

    def iniciar_produccion(self):
        nuevas_lineas = []
        for nombre, hilo in self.lineas:
            if hilo is None or not hilo.is_alive():
                nueva_linea = LineaProduccion(nombre, self.actualizar_estado, 
                                            self.actualizar_contador_hilos, self.actualizar_progreso)
                nueva_linea.start()
                nuevas_lineas.append((nombre, nueva_linea))
            else:
                nuevas_lineas.append((nombre, hilo))
        self.lineas = nuevas_lineas

    def detener_todas_lineas(self):
        """Nuevo método para detener todas las líneas activas"""
        for nombre, hilo in self.lineas:
            if hilo is not None and hilo.is_alive():
                hilo.detener()
        
        # Mostrar mensaje de confirmacion
        messagebox.showinfo("Detener líneas", "Señal de parada enviada a todas las líneas activas.")

if __name__ == "__main__":
    # Importar messagebox para el boton de detener
    from tkinter import messagebox
    
    root = tk.Tk()
    app = SimuladorApp(root)
    root.mainloop()