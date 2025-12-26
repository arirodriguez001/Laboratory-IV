from __future__ import division, unicode_literals, print_function, absolute_import
import time
import pyvisa as visa

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import threading
# from datetime import datetime
from datetime import datetime, timedelta

#%%

rm = visa.ResourceManager()
# aparatos = rm.list_resources()
# print(aparatos)

#%%

fuente = rm.open_resource('GPIB0::25::INSTR', write_termination='\n')  # Fuente

multi1 = rm.open_resource('GPIB0::24::INSTR',  write_termination='\n')  # Multi de abajo (cara inferior)
multi2 = rm.open_resource('GPIB0::22::INSTR',  write_termination='\n')  # Multi de arriba (cara superior)


#%% fuente : Agilent B2901A

fuente_name = 'GPIB0::25::INSTR'

fuente = rm.open_resource(fuente_name, write_termination='\n')

# query idn
print(fuente.query('*IDN?'))

# Ultimos valores medidos de 
# Voltage, corriente, resistencia, tiempo, status, source ouput setting
#print(inst.query_ascii_values(':READ:SCALar?'))


float(fuente.query('MEASURE:VOLT:DC?')) #para consultar el voltaje.
print(fuente.query_ascii_values(':READ:SCALar?'))

corrientedc = float(fuente.query('MEASURE:CURRent:DC?'))
print(corrientedc)


inst.write(":OUTP OFF") #Apago la salida

#%% multi 1:  Agilent 34401A (el de abajo: va a la termocupla de la derecha)
    
# Este string determina el intrumento que van a usar.
# Lo tienen que cambiar de acuerdo a lo que tengan conectado.
multi1_name = 'GPIB0::24::INSTR'

multi1 = rm.open_resource(multi1_name, write_termination='\n')

# query idn
print(multi1.query('*IDN?'))

# Ultimos valores medidos de 
# Voltage, corriente, resistencia, tiempo, status, source ouput setting
#print(multi1.query_ascii_values(':READ:SCALar?'))


float(multi1.query('MEASURE:VOLT:DC?')) #para consultar el voltaje.

"""
# parámetros para controlal la fuente
multi1.write(":SOUR:FUNC:MODE CURR") # Modo corriente
multi1.write(":SOUR:CURR 0.1") # Pone una corriente
multi1.write(":SENS:VOLT:PROT 6") #Establece el límite de voltaje

multi1.write(":SOUR:FUNC:MODE VOLT") # Modo voltaje
multi1.write(":SOUR:VOLT 5") # Pone un voltaje
multi1.write(":SENS:CURR:PROT 0.5") #Establece el límite de corrienteº

"""
multi1.write(":OUTP OFF") #Apago la salida

multi1.close()

#%% multi 2 : Agilent 34401A (el de arriba: termocupla de la izquierda)

multi2_name = 'GPIB0::22::INSTR'

multi2 = rm.open_resource(multi1_name, write_termination='\n')

# query idn
print(multi2.query('*IDN?'))

# Ultimos valores medidos de 
# Voltage, corriente, resistencia, tiempo, status, source ouput setting
#print(multi2.query_ascii_values(':READ:SCALar?'))


float(multi2.query('MEASURE:VOLT:DC?')) #para consultar el voltaje.

"""
# parámetros para controlal la fuente
multi2.write(":SOUR:FUNC:MODE CURR") # Modo corriente
multi2.write(":SOUR:CURR 0.1") # Pone una corriente
multi2.write(":SENS:VOLT:PROT 6") #Establece el límite de voltaje

multi2.write(":SOUR:FUNC:MODE VOLT") # Modo voltaje
multi2.write(":SOUR:VOLT 5") # Pone un voltaje
multi2.write(":SENS:CURR:PROT 0.5") #Establece el límite de corrienteº

"""
multi2.write(":OUTP OFF") #Apago la salida

multi2.close()

#%%


T_ref_K = 273
def TC_K_volt2temp_poli(mV): # en mV 

    C0 = 273
    C1 = 2.5173462 * 10**1
    C2 = -1.1662878
    C3 = -1.0833638
    C4 = -8.9773540 * 10**-1
    C5 = -3.7342377 * 10**-1
    C6 = -8.6632643 * 10**-2
    C7 = -1.0450598 * 10**-2
    C8 = -5.1920577 * 10**-4
    C9 = 0            
    T1 = C0 + C1*mV + C2*mV**2 + C3*mV**3 + C4*mV**4 + C5*mV**5 + C6*mV**6 + C7*mV**7 +  C8*mV**8 + C9*mV**9                
   
    C0 = 273
    C1 = 2.508355 * 10**1
    C2 = 7.860106 * 10**-2
    C3 = -2.503131 * 10**-1
    C4 = 8.315270 * 10**-2
    C5 = -1.228034 * 10**-2
    C6 = 9.804036 * 10**-4
    C7 = -4.413030 * 10**-5
    C8 = 1.057734 * 10**-6
    C9 = -1.052755 * 10**-8
    T2 = C0 + C1*mV + C2*mV**2 + C3*mV**3 + C4*mV**4 + C5*mV**5 + C6*mV**6 + C7*mV**7 +  C8*mV**8 + C9*mV**9        
    
    return T1 * (mV<0) + T2 * (mV>=0) * (mV<20.644) #Kelvin


#%%
def error_volt_multimetro(v):
    return (0.0002*v + 0.0001*0.1) / 100

#%%


T1 = []
T2 = []
current_measure = []
voltage_measure_a = []
voltage_measure_b = []
error_voltage_measure_a = []
error_voltage_measure_b = []
tiempos = []
voltage_peltier = []

corrientes = []

#Se enciende la fuente de corriente y se establece un límite de voltaje de 16V.
fuente.write(":OUTP ON")
fuente.write(":SENS:VOLT:PROT 6")

# corrientes_y_puntos = [
#     [0, 1],
#     [1.5, 50],
#     [0, 30],
#     ]

# corrientes_y_tiempos = [
#     [0, 15],
#     [0, 2],
#     [0.15, 15],
#     [0, 2],
#     [0.30, 15],
#     [0, 2],    
#     [0.45, 15],
#     [0, 2],
#     ]

corrientes_y_tiempos = [
    [0, 300],
    [0, 2],
    [0.15, 300],
    [0, 2],
    [0.30, 300],
    [0, 2],    
    [0.45, 300],
    [0, 2],
    [0.60, 300],
    [0, 2],
    [0.75, 300],
    [0, 2],
    [0.90, 300],
    [0, 2],
    [1.05, 300],
    [0, 2],
    [1.20, 300],
    [0, 2],
    [1.35, 300],
    [0, 2],
    [1.50, 300],
    [0, 2],
    ]


t_0 = time.time()

# cant_corrientes = len(corrientes)

# print("\n#########################\n")

# print(f"Corrientes: {corrientes} A\n({cant_corrientes} saltos de {corrientes[1] - corrientes[0]} A) (contando el salto final a 0 A)\n")


# now = datetime.now()
# print(now.strftime("%H_%M_%S"))
# 
# datetime.now().strftime("%H:%M:%S")

hora_inicio = datetime.now().strftime("%H_%M_%S")

carpeta = r"C:\Users\publico\Desktop\l4g6\mediciones peltier"
#nombre_archivo = f"\mediciones_{hora_inicio}_{corrientes_y_tiempos}.csv"


nombre_archivo = f"\mediciones_{hora_inicio}_aber6.csv"


ruta_total = carpeta + nombre_archivo


print("\n#########################\n")

print(f"Guardando archivo {nombre_archivo}\n(en {carpeta})\n")

print("\n#########################\n")

dt_aprox = 1.156
print(f"Tiempo entre mediciones: {dt_aprox}seg")



# duracion_aprox = dt_aprox * cant_corrientes *  CANT_MEDICIONES_POR_CORRIENTE
# print(f"Tiempo total: aprox. {round(duracion_aprox)}seg = {round(duracion_aprox/60)}min")


# hora_fin_ = datetime.now() + timedelta(minutes=duracion_aprox)  
# hora_fin = hora_fin_.strftime("%H_%M_%S")

# hora_fin = 
# print(f"Hora actual: {hora_inicio}")
# print(f"Hora fin: {hora_fin}")


print("\n#########################\n")

temperaturas_graficar = []
volt_peltier_grafi = []


print("Se medira")


for corriente, duracion_una_medicion in corrientes_y_tiempos:
    
    cant_puntos = int(duracion_una_medicion * dt_aprox)

    print(f"{corriente}A durante {duracion_una_medicion}seg ")



print("\n#########################\n")

plt.clf()

# Before the main measurement loop, set up the plot
plt.figure()
plt.plot([], [], '.', color="k", label="DT = T_abajo - T_arriba")
plt.plot([], [], '.', color="red", label="V_fuente")
plt.plot([], [], '.', color="blue", label="I")


# , label="DT = T_abajo - T_arriba"
# , label="V_fuente"
# Add legend only once
plt.legend()


for corriente, duracion_una_medicion in corrientes_y_tiempos:

    cant_puntos = int(duracion_una_medicion * dt_aprox)
    
    print(f"\nMidiendo a corriente {corriente}A durante {duracion_una_medicion}seg [{cant_puntos} puntos]")
        
    fuente.write(":SOUR:FUNC:MODE CURR")
    fuente.write(":SOUR:CURR {}".format(corriente))
    
    plt.xlabel("t (s)")
    plt.ylabel("DT = T_abajo - T_arriba")
    plt.title("Temperature Difference vs Time")
    plt.grid(True)


    t_inicial = time.time()
        
    num_medicion = 0
    
    while (time.time() - t_inicial) < duracion_una_medicion:
        num_medicion += 1
    
    # for num_medicion in range(cant_puntos):        
        
        # print(f"Medición {num_medicion + 1} de {cant_puntos}")
        
        volt_a = multi1.query_ascii_values('MEASURE:VOLTAGE:DC?')[0]
        volt_b = multi2.query_ascii_values('MEASURE:VOLTAGE:DC?')[0]
        
        voltage_fuente = float(fuente.query('MEASURE:VOLT:DC?'))

        corriente = float(fuente.query('MEASURE:CURRENT:DC?'))
        
        corrientes.append(corriente)

        voltage_measure_a.append(volt_a)
        voltage_measure_b.append(volt_b)

        error_volt_a_inst = error_volt_multimetro(volt_a)
        error_volt_b_inst = error_volt_multimetro(volt_b)

        error_voltage_measure_a.append(error_volt_a_inst)
        error_voltage_measure_b.append(error_volt_b_inst)

        tiempo_actual = time.time() - t_0
        tiempos.append(tiempo_actual)
        tiempos_graf = np.array(tiempos)
        
        

        T1.append(TC_K_volt2temp_poli(volt_a*1000))  
        T2.append(TC_K_volt2temp_poli(volt_b*1000))
        
        # T1_graf = np.array(T1)
        # T2_graf = np.array(T2)


        voltage_peltier.append(voltage_fuente)

        volt_peltier_grafi.append(voltage_fuente)

        # plt.plot(tiempo_actual, T2[-1] - T1[-1] ,'.', color="k")

        temperaturas_graficar.append(T2[-1] - T1[-1])
        
        
        print(f"Tiempo actual: t = {round(tiempo_actual, 3)} seg")
        print(f"Medicion {num_medicion} de {cant_puntos}: Voltaje fuente: {round(voltage_fuente/1000, 4)} mV\n")

        diccionario_datos_Peltier =  {'Volt_abajo_Peltier' : voltage_measure_b,
                              'Volt_arriba_Peltier' : voltage_measure_a,
                              'err_Volt_abajo_Peltier' : error_voltage_measure_b,
                              'err_Volt_arriba_Peltier' : error_voltage_measure_a,
                              'tiempos' : tiempos, 'T1': T1, 'T2': T2, 'voltajes_posta': voltage_peltier}

        
        plt.plot(tiempo_actual, corriente, '.', color="blue", label="Current Fuente")
        plt.plot(tiempos, corrientes, color="blue")

        
        plt.plot(tiempo_actual, T2[-1] - T1[-1] ,'.', color="k")
        plt.plot(tiempos, temperaturas_graficar, color="k", alpha=0.25)
        
        
        plt.plot(tiempo_actual, voltage_fuente ,'.', color="red")
        plt.plot(tiempos, volt_peltier_grafi, color="red", alpha=0.25)
        
        plt.pause(min(0.1, dt_aprox / 10))        
        
        
        plt.show()
  
        datos_Peltier = pd.DataFrame(data = diccionario_datos_Peltier)

        datos_Peltier.to_csv(ruta_total)                    
    
    print("\n#########################\n")
    
    
    
    
    
fuente.close()
multi2.close()
multi1.close()




