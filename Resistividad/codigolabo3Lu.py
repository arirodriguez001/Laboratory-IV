#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 31 13:37:02 2025

@author: luciabasili
"""

import pyvisa as visa
import numpy as np
import matplotlib.pyplot as plt
import time

# === Inicialización de los recursos ===
rm = visa.ResourceManager()
instrumentos = rm.list_resources()
print("Instrumentos detectados:", instrumentos)

# Identificar los recursos conectados
resource_gen = instrumentos[0]  # Generador de funciones
resource_osci = instrumentos[1]  # Osciloscopio

# Conectar a los instrumentos
fungen = rm.open_resource(resource_gen)
osci = rm.open_resource(resource_osci)

# === Comprobar que ambos instrumentos están conectados ===
print("Generador:", fungen.query('*IDN?'))
print("Osciloscopio:", osci.query('*IDN?'))

# === Configuración del generador de funciones ===
#fungen.write('SOURCE1:FUNC SIN')  # Configurar forma de onda sinusoidal
#fungen.write('SOURCE1:VOLT 1')  # Amplitud de 1 V

# === Configuración del osciloscopio ===
osci.write("DAT:ENC RPB")
osci.write("DAT:WID 1")

xze, xin = osci.query_ascii_values('WFMPRE:XZE?;XIN?', separator=';')

osci.write("DAT:SOU CH1")
yze1, ymu1, yoff1 = osci.query_ascii_values('WFMPRE:YZE?;YMU?;YOFF?', separator=';')
osci.write("DAT:SOU CH2")
yze2, ymu2, yoff2 = osci.query_ascii_values('WFMPRE:YZE?;YMU?;YOFF?', separator=';')

# === Bucle para realizar el barrido de frecuencias y guardar datos por archivo ===
for freq in np.linspace(1, 10000, 50):  # Barrido lineal de frecuencias de 1 Hz a 10 kHz
	# Configurar la frecuencia del generador
	fungen.write(f'SOURCE1:FREQ {freq}')
	print(f"Frecuencia ajustada a: {freq} Hz")
    
	# Esperar un poco para estabilizar
	time.sleep(0.5)

	# Capturar datos del osciloscopio
	osci.write("DAT:SOU CH1")
	data1 = osci.query_binary_values('CURV?', datatype='B', container=np.array)

	osci.write("DAT:SOU CH2")
	data2 = osci.query_binary_values('CURV?', datatype='B', container=np.array)
    
	# Configura el osciloscopio para mostrar 4 períodos
	periodo = 1 / (2*freq)  # Período de la señal en segundos
	tiempo_por_division = (6 * periodo) / 10  # Para mostrar 4 períodos en 10 divisiones horizontales
	osci.write(f"HORizontal:SCALe {tiempo_por_division * 0.9}")  # Ajuste fino para mejorar la visualización

	voltaje_por_division = (1)  # Para que 10 Vpp ocupen 8 divisiones verticales
	osci.write(f"CH1:SCALe {voltaje_por_division}")  # Ajuste de escala de voltaje en CH1
    
	# Convertir los datos a voltaje
	tiempo = xze + np.arange(len(data1)) * xin
	data1v = (data1 - yoff1) * ymu1 + yze1
	data2v = (data2 - yoff2) * ymu2 + yze2

	# Crear el nombre del archivo usando la frecuencia
	nombre_archivo = f"cambiooscCOMPLETAdiodorapidosSINC10k_osci_{int(freq)}Hz.csv"
    
	# Guardar los datos en un archivo CSV
	salida = np.column_stack((tiempo, data1v, data2v))
	np.savetxt(nombre_archivo, salida, delimiter=',', header='Tiempo,CH1,CH2', comments='')

	print(f"Datos guardados en '{nombre_archivo}'")

print("Captura y guardado finalizados.")


