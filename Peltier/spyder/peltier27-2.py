# -*- coding: utf-8 -*-
"""
Created on Thu Feb 27 10:25:58 2025

@author: Publico
"""

#%%


from __future__ import division, unicode_literals, print_function, absolute_import

import pyvisa as visa
import numpy as np
import matplotlib.pyplot as plt

print(__doc__)
#%%

#------------------------- Agilent B2901A-------------------------
# Este string determina el intrumento que van a usar.
# Lo tienen que cambiar de acuerdo a lo que tengan conectado.
resource_name = 'GPIB0::25::INSTR'


rm = visa.ResourceManager()

mult = rm.open_resource(resource_name)

print(mult.query('*IDN?'))

voltajedc = float(mult.query('MEASURE:VOLTAGE:DC?'))
print(voltajedc)

corrientedc = float(mult.query('MEASURE:CURRent:DC?'))
print(corrientedc)

mult.close()
#%%

#------------------------- HP34401 -------------------------

# Este string determina el intrumento que van a usar.
# Lo tienen que cambiar de acuerdo a lo que tengan conectado.
resource_name = 'GPIB0::24::INSTR'


rm = visa.ResourceManager()

mult = rm.open_resource(resource_name)

print(mult.query('*IDN?'))

voltajedc = float(mult.query('MEASURE:VOLTAGE:DC?'))
print(voltajedc)

corrientedc = float(mult.query('MEASURE:CURRent:DC?'))
print(corrientedc)

mult.close()
#%%
#------------------------- Agilent 34401A -------------------------

# Este string determina el intrumento que van a usar.
# Lo tienen que cambiar de acuerdo a lo que tengan conectado.
resource_name = 'GPIB0::23::INSTR'

rm = visa.ResourceManager()

inst = rm.open_resource(resource_name, write_termination='\n')

# query idn
print(inst.query('*IDN?'))

# Ultimos valores medidos de 
# Voltage, corriente, resistencia, tiempo, status, source ouput setting
#print(inst.query_ascii_values(':READ:SCALar?'))


float(inst.query('MEASURE:VOLT:DC?')) #para consultar el voltaje.

"""
# parámetros para controlal la fuente
inst.write(":SOUR:FUNC:MODE CURR") # Modo corriente
inst.write(":SOUR:CURR 0.1") # Pone una corriente
inst.write(":SENS:VOLT:PROT 6") #Establece el límite de voltaje

inst.write(":SOUR:FUNC:MODE VOLT") # Modo voltaje
inst.write(":SOUR:VOLT 5") # Pone un voltaje
inst.write(":SENS:CURR:PROT 0.5") #Establece el límite de corrienteº

"""
inst.write(":OUTP OFF") #Apago la salida

inst.close()

#%%

datos = []

# Hacer 10 mediciones con un intervalo de 1 segundo
for i in range(10):
    inst.write(":MEAS:VOLT?")
    voltaje = float(inst.read())  # Convertir a número
    
    inst.write(":MEAS:CURR?")
    corriente = float(inst.read())  # Convertir a número
    
    datos.append([voltaje, corriente])  # Guardar en la lista
    
    time.sleep(1)  # Esperar 1 segundo entre mediciones


# Crear un DataFrame con los datos
df = pd.DataFrame(datos, columns=["Voltaje (V)", "Corriente (A)"])

# Mostrar en formato de tabla
print(df)

[V_prom, I_prom] = df.mean()
[err_V_prom, err_I_prom] = df.std()/np.sqrt(len(df['Voltaje (V)']))
print('Voltaje promedio:', V_prom,'+/-', err_V_prom, '[V]')
print('Corriente promedio:', I_prom,'+/-', err_I_prom,'[A]')

#%%

inst.write(":OUTP OFF") #Apago la salida

#%%

def TC_K_volt2temp_interp(mV): # en mV 
    data = np.loadtxt('termocupla_k_mv2T.csv',delimiter=',')
    temperature_vals = data[:,0] # en K 
    voltage_vals = data[:,1] # en mV 
    return np.interp(mV, voltage_vals, temperature_vals)

# funcion utiliza polinomio
def TC_K_volt2temp_poli(mV): # en mV 
    #  The coefficients for Temperature range -200 deg C to 0 deg C 
    #  Voltage range -5.891 mV to 0 mV
    #  Error Range .04 deg C to -.02 deg C are:    
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

    #  The coefficients for Temperature range 0 deg C to 500 deg C
    #  Voltage range 0 mV to 20.644 mV
    #  Error range .04 deg C to -.05 deg C are:    
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

# Grafico ambas
mV = np.linspace(-5.891,20.643,100)
plt.plot(mV, TC_K_volt2temp_poli(mV))
plt.plot(mV, TC_K_volt2temp_interp(mV))
plt.ylabel('Temperatura [K]')
plt.xlabel('Voltaje Termocupla K [mV]')
plt.legend(('Poli','Interp'))
plt.grid(True)

#%% t0 = time.time() para guardar el tiempo de la compu 