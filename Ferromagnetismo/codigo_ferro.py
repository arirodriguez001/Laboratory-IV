
	

# -*- coding: utf-8 -*-
"""
Created on Wed Apr 24 16:06:37 2024

@author: Publico
"""

import matplotlib.pyplot as plt
import numpy as np
import nidaqmx
import math
import pandas as pd
import time
import os 

os.chdir(r'C:\Users\publico\Desktop\LABO4-G2')


#para saber el ID de la placa conectada (DevX)
system = nidaqmx.system.System.local()
for device in system.devices:
    print(device)
#%%
## Medicion por tiempo/samples de una sola vez

#%%
#para setear (y preguntar) el modo y rango de un canal analógico

with nidaqmx.Task() as task:
    ai1_channel = task.ai_channels.add_ai_voltage_chan("Dev1/ai1",max_val=10,min_val=-10)
    ai2_channel = task.ai_channels.add_ai_voltage_chan("Dev1/ai2",max_val=10,min_val=-10)
    ai3_channel = task.ai_channels.add_ai_voltage_chan("Dev1/ai3",max_val=10,min_val=-10)
#    print(ai_channel.ai_term_cfg)    
#   print(ai_channel.ai_max)
#   print(ai_channel.ai_min)	
	
def medicion_una_vez2(duracion, fs):
    cant_puntos = int(duracion*fs)
    with nidaqmx.Task() as task:
        modo= nidaqmx.constants.TerminalConfiguration.DIFF
        # modo= nidaqmx.constants.TerminalConfiguration.RSE
        task.ai_channels.add_ai_voltage_chan("Dev1/ai1", terminal_config = modo ,max_val=1,min_val=-1)
        task.ai_channels.add_ai_voltage_chan("Dev1/ai2", terminal_config = modo ,max_val=10,min_val=-10)
        task.ai_channels.add_ai_voltage_chan("Dev1/ai4", terminal_config = modo ,max_val=10,min_val=-10)


               
        task.timing.cfg_samp_clk_timing(fs,samps_per_chan = cant_puntos,
                                        sample_mode = nidaqmx.constants.AcquisitionType.FINITE)
        
        datos = task.read(number_of_samples_per_channel=nidaqmx.constants.READ_ALL_AVAILABLE, timeout=duracion+0.1)           
    
    Tension_I = datos[0]
    Tension_b = datos[1]
    Tension_R = datos[2]
    
    return Tension_I,Tension_b,Tension_R

def inte(t,a,dt):
    I=[0]
    for i in range(1,len(a)-1):
        I.append((a[i]+a[i+1])*dt/2+I[i-1])
    return I

def inte2(t,a,dt):
    I=[(a[0]+a[1])*dt/2]
    for i in range(1,len(a)-1):
        I.append((a[i]+a[i+1]/2)*dt/2)
    return I

#%%
duracion = 180 #segundos
fs = 10000 #Frecuencia de muestreo

for i in range(1):
    tension_int,tension_en,tension_r = medicion_una_vez2(duracion, fs)
    tiempo= np.linspace(0,duracion,int(fs*duracion))
    h=0
    #DF=pd.DataFrame({'tiempo':tiempo,"tension_entrada":x,"tension_integrada":y,"tension_r":z})
    #DF.attrs["fs"] = fs
    #DF.attrs["duracion"] = duracion
    #DF.attrs["t_0"] = 2*i
    #DF.to_pickle(f'Datos_hiteresisDAC2_{i}.pd')
    #np.savetxt('prueba_final.txt',np.transpose([tiempo,tension_int,tension_en,tension_r]), delimiter=",", header='tiempo,tension_inte,tension_prima,tension_resis')
    
    #np.save('ejemplo.npy', [tiempo,tension_int,tension_en,tension_r])
    
    np.savez_compressed('medicion4.npz', datos=[tiempo,tension_int,tension_en,tension_r])
    

# data=pd.read_pickle(r"C:\Users\publico\Desktop\Grupo 1_miercolesMañana\Datos_hiteresisDAC2_1.pd")
# plt.plot(data['tension_i'][:len(tiempo)-1],inte(data['tiempo'],data['tension_b'],1/data.attrs["fs"])-np.mean(inte(data['tiempo'],data['tension_b'],1/data.attrs["fs"])))


#%%
N = 5
for j in range (N):
    tn = int((len(tiempo)/N)*j)
    plt.plot(tension_en[tn:tn+200],tension_int[tn:tn+200],'.-')

plt.gca().axvline(0, ls=':')
plt.gca().axhline(0, ls=':')

#%%



#plt.plot(tension_en,tension_int)
plt.plot(tension_int)


#%% Leer datos

datos = np.load('ejemplo.npy')
tiempo,tension_int,tension_en,tension_r = datos


#%% Leer datos npz

datos = np.load('ejemplo2.npy.npz')

tiempo,tension_int,tension_en,tension_r = datos['datos']
plt.plot(tension_int)
#%%

from scipy.optimize import curve_fit
datos_resistencia = np.loadtxt('Pt100_resistencia_temperatura.csv',delimiter=',')

temperatura = datos_resistencia[0][:240]
ohms = datos_resistencia[1][:240]

plt.plot(ohms, temperatura)

def lineal(x,a,b):
    return a*x+b

par, var = curve_fit(lineal,ohms,temperatura)

plt.plot(ohms,lineal(ohms,*par))

pendiente = par[0]
ordenada = par[1]
print(pendiente, ordenada)
#%%
for i in range(1):
    fase=600000

    a=i*200+fase
    b=(i+1)*200+fase
    plt.plot(tiempo[a:b],tension_en[a:b])
    plt.plot(tiempo[a:b],tension_int[a:b])


def encontrar_M (H):
    A=int(len(H)/2)
    r1=10000
    r2=10000
    for i in range(A):
        if abs(H[i])<r1:
            r1=abs(H[i])
            idx1=i
        if abs(H[A+i])<r2:
            r2=abs(H[A+i])
            idx2=A+i

    return r1,idx1,r2,idx2

IDX=[]

for i in range(6000):
  a=i*200
  b=(i+1)*200
  _,id1,_,id2 = encontrar_M(np.array(tension_en[a:b])) #busco y encuentro los puntos donde tengo +-M
  id1 = id1 + i*200
  id2 = id2 + i*200

  IDX.append([id1,id2])
IDX=np.array(IDX)

#%%
def M_mas_menos1(x,tiempo,idx):
  V_mas=[]
  V_menos=[]
  t1=[]
  t2=[]

  dy = np.gradient(x, tiempo)

  for i in range(len(idx)):

    if dy[idx[i][0]] < 0 :

        V_mas.append(x[idx[i][0]])
        t1.append(tiempo[idx[i][0]])
        t2.append(tiempo[idx[i][1]])
        V_menos.append(x[idx[i][1]])

    else:

        V_mas.append(x[idx[i][1]])
        t1.append(tiempo[idx[i][1]])
        t2.append(tiempo[idx[i][0]])
        V_menos.append(x[idx[i][0]])

  V_mas=np.array(V_mas)
  V_menos=np.array(V_menos)
  t1=np.array(t1)
  t2=np.array(t2)

  return V_mas,V_menos,t1,t2

def M_mas_menos2(x,tiempo,idx):
  V_mas=[]
  V_menos=[]
  t1=[]
  t2=[]

  for i in range(len(idx)):
    V_mas.append(x[idx[i][0]])
    t1.append(tiempo[idx[i][0]])
    t2.append(tiempo[idx[i][1]])
    V_menos.append(x[idx[i][1]])

  V_mas=np.array(V_mas)
  V_menos=np.array(V_menos)
  t1=np.array(t1)
  t2=np.array(t2)
  return V_mas,V_menos,t1,t2

ten_b_mas,ten_b_menos,t1,t2 = M_mas_menos1(tension_en,datos['tiempo'],IDX)
# ten_b_mas,ten_b_menos,t1,t2 = M_mas_menos2(datos['tension_int'],datos['tiempo'],IDX)


plt.plot(t1,ten_b_mas)
plt.plot(t2,ten_b_menos)
plt.legend()
plt.ylabel("$V_{int}$ [V] $(\propto M)$")
plt.xlabel("Tiempo [s]")
plt.grid()
plt.show()
