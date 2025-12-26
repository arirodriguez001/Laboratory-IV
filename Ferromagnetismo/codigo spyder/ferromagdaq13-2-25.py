# -*- coding: utf-8 -*-
"""
Created on Mon Feb  3 09:53:29 2025

@author: Publico
"""

import numpy as np
import nidaqmx
import time
import matplotlib.pyplot as plt
from scipy.integrate import cumtrapz

#%%
R_0 = 1 #resistencia en serie con el transformador 
Rs = 1979
alpha = 0.00385  # Coeficiente platino
#%%

#para saber el ID de la placa conectada (DevX)
system = nidaqmx.system.System.local()
for device in system.devices:
    print(device)


#%% Función de medición mejorada


def medicion_continua_tres_canales(duracion, fs):
    cant_puntos = int(duracion * fs)
    
    with nidaqmx.Task() as task:
        # Configuración de canales (RSE y DIFF)
        modo1 = nidaqmx.constants.TerminalConfiguration.RSE
        modo2 = nidaqmx.constants.TerminalConfiguration.DIFF
        
        task.ai_channels.add_ai_voltage_chan("Dev3/ai1", 
            terminal_config=modo2,
            min_val=-10, max_val=10) #H (caida de V EN R_0)
        
        task.ai_channels.add_ai_voltage_chan("Dev3/ai2",
            terminal_config=modo2,
            min_val=-10, max_val=10) #B (salida integrador)
        
        task.ai_channels.add_ai_voltage_chan("Dev3/ai3",
            terminal_config=modo2,
            min_val=-10, max_val=10) #B sin integrar 
        
        task.ai_channels.add_ai_voltage_chan("Dev3/ai4",
            terminal_config=modo2,
            min_val=-1, max_val=1)  #V_platino
        
        task.ai_channels.add_ai_voltage_chan("Dev3/ai6",
            terminal_config=modo2,
            min_val=-1, max_val=1)  #Vs
        
        # Configuración de adquisición continua
        task.timing.cfg_samp_clk_timing(
            rate=fs,
            sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,
            #samps_per_chan=2 * fs  # Buffer para 2 segundos
            samps_per_chan = fs // 2
        )
        
        task.start()


        t0 = time.time()
        data = [[], [], [], [], [] ]
        tiempos = []
        
        print("Iniciando adquisición...")
        while (time.time() - t0) < duracion:
            time.sleep(0.01)  
            # time.sleep(0.5)
            datos = task.read(
                number_of_samples_per_channel=nidaqmx.constants.READ_ALL_AVAILABLE, 
                timeout=2.0)
            
            if not datos[0]:
                continue  # Si no hay datos, reintentar
            
            num_muestras = len(datos[0])
            
            # Almacenamiento de datos
            for i in range(5):
                data[i].extend(datos[i])
            
            # Cálculo preciso de tiempos para cada muestra
            t_actual = time.time()
            tiempo_bloque = np.linspace(
                start = t_actual - num_muestras/fs - t0,
                stop = t_actual - t0,
                num = num_muestras
            )
            tiempos.extend(tiempo_bloque)
            
        
            # Monitoreo de rendimiento
            t1 = time.time()
            #print(
            #    f"Tiempo: {t1 - t0:.2f}s | "
             #   f"Muestras: {num_muestras} | "
              #  f"Frec. bloque: {num_muestras/(t1 - t_actual + 1e-9):.1f} Hz"
            #)
        
    return np.array(tiempos), [np.array(data[0]), np.array(data[1]), np.array(data[2]), np.array(data[3]),np.array(data[4])]
#%%
fs = 50000
duracion = 0.1 #segundos
t0 = time.time()


for t in range(250):
    
    t1 = time.time()
    tiempo = t1 - t0

    tiempos, datos = medicion_continua_tres_canales(duracion, fs)
    
    # Separación de canales
    V1 = datos[0]  # Canal DIFF H
    V2 = datos[1]  # Canal DIFF  B
    VB = datos [2] # Canal DIFF B sin integrar
    Vplat = datos[3] # Canal DIFF Vplatino
    Vs = datos[4]  # Canal DIFF V_s resist en serie a platino 
    
    
    Rplat = (np.std(Vplat)/np.std(Vs))  * Rs  
    print(f"R platino{t}",Rplat)
    
    t_vector=np.ones_like(tiempos)*t
    Rplat_vector = np.ones_like(tiempos) * Rplat
    np.savetxt(f'Medicion_nitrogeno4enS215V{t}.csv', 
               np.column_stack((tiempos, V1, V2, VB, Vplat, Vs, t_vector, Rplat_vector)),
               delimiter=',',
               header='Tiempo[s],V1[V],V2[V],VB[V], Vplat[V], Vs[V], Iteracion, Rplat')
    # np.savetxt('datos.csv', 
    #        np.column_stack((tiempos, V1, V2, VRP, H, B, T)),
    #        delimiter=',',
    #        header='Tiempo[s],V1[V],V2[V],VRP[V],H[A/m],B[T],T[°C]')
    
print("Listo!")
    #%%

plt.figure(figsize=(12, 8))


plt.subplot(2, 1, 1)  
plt.plot(tiempos, V2, label='V2  - B')
plt.plot(tiempos, V1, label='V1 - H')

plt.plot(tiempos, VB, label='Vb - B sin integrar')
plt.plot(tiempos, Vplat, label='Vplatino')
plt.plot(tiempos, Vs, label='Vs - resist serie platino')


plt.xlabel('Tiempo [s]')
plt.ylabel('Voltaje [V]')
plt.title('Señales Crudas')
plt.grid(True)
plt.legend()

# Segundo gráfico: Histéresis (V2 vs. V1)
plt.subplot(2, 1, 2)  # 2 filas, 1 columna, segundo gráfico
plt.plot(V1, V2, 'g', label='Histéresis')
plt.ylabel('V2: campo B')
plt.xlabel('V1: campo H')
plt.title('Curva de Histéresis')
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.show()


#%% Configuración de parámetros
"""
N1 = 
N2 =    
A =  
L =  
"""


# Cálculos físicos (ajustar según setup real)
H = (V1 / R_0) #esto mult por una cte que no conocemos
B = - cumtrapz(V2, tiempos, initial=0) #esto mult por una cte que no conocemos
#Rpt = R * (VRP / V1)
T = (Rpt - R_0) / (alpha * R_0)
"""
# Guardado 
np.savetxt('datos.csv', 
           np.column_stack((tiempos, V1, V2, VRP, H, B, T)),
           delimiter=',',
           header='Tiempo[s],V1[V],V2[V],VRP[V],H[A/m],B[T],T[°C]')
"""

#%% 
#Grafico
plt.figure(figsize=(12, 8))

# Gráfico 1: Señales de voltaje (RSE vs DIFF)
plt.subplot(2, 2, 1)
plt.plot(tiempos, V1, 'b', label='V1 (RSE) - Campo H')
plt.plot(tiempos, V2, 'r', label='V2 (DIFF) - Derivada B')
plt.xlabel('Tiempo [s]')
plt.ylabel('Voltaje [V]')
plt.title('Señales Crudas')
plt.grid(True)
plt.legend()

# Gráfico 2: Curva de Histéresis (H vs B)
plt.subplot(2, 2, 2)
plt.plot(H, B, 'k-', linewidth=0.5)
plt.xlabel('H [A/m]')
plt.ylabel('B [T]')
plt.title('Curva de Histéresis')
plt.grid(True)

# Gráfico 3: Temperatura vs Tiempo
plt.subplot(2, 2, 3)
plt.plot(tiempos, T, 'm')
plt.xlabel('Tiempo [s]')
plt.ylabel('Temperatura [°C]')
plt.title('Evolución de la Temperatura')
plt.grid(True)

# Gráfico 4: Resistencia vs Tiempo
# plt.subplot(2, 2, 4)
# plt.plot(tiempos, Rpt, 'g')
# plt.xlabel('Tiempo [s]')
# plt.ylabel('Resistencia [Ω]')
# plt.title('Resistencia del Material')
# plt.grid(True)

plt.tight_layout()
plt.show()