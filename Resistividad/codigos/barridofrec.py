"""
Created on Thu Jan 30 12:03:53 2025

@author: Publico
"""

# -*- coding: utf-8 -*-
"""
LOCKIN Stanford Research SR830
Manual: http://www.thinksrs.com/downloads/PDFs/Manuals/SR830m.pdf
Manual: https://github.com/diegoshalom/labosdf/blob/master/manuales/SR830m.pdf
"""

#%%
import pyvisa as visa
import time
import numpy as np

#%%
rm = visa.ResourceManager()
instrumentos = rm.list_resources()
print("Instrumentos detectados:", instrumentos)

for i in range(len(instrumentos)):
    resource_gen = instrumentos[i]  # Identifico Generador de funciones
    fungen = rm.open_resource(resource_gen) # Conecto Generador de funciones
    print("Generador:", fungen.query('*IDN?')) # Compruebo que el Generador de funciones esta conectado
    
resource_gen = instrumentos[0]  # Identifico Generador de funciones
fungen = rm.open_resource(resource_gen) # Conecto Generador de funciones
print("Generador:", fungen.query('*IDN?')) # Compruebo que el Generador de funciones esta conectado    

#%%
class SR830:
    '''Clase para el manejo amplificador Lockin SR830 usando PyVISA de interfaz'''

    scale_values = (2e-9, 5e-9, 10e-9, 20e-9, 50e-9, 100e-9, 200e-9, 500e-9, 1e-6,
                    2e-6, 5e-6, 10e-6, 20e-6, 50e-6, 100e-6, 200e-6, 500e-6, 1e-3,
                    2e-3, 5e-3, 10e-3, 20e-3, 50e-3, 100e-3, 200e-3, 500e-3, 1) # in V

    time_constant_values = (10e-6, 30e-6, 100e-6, 300e-6, 1e-3, 3e-3, 10e-3, 30e-3, 100e-3, 300e-3,
                    1e0, 3e0, 10e0, 30e0, 100e0, 300e0, 1e3, 3e3, 10e3, 30e3) # in s

    def __init__(self, resource):
        self._lockin = visa.ResourceManager().open_resource(resource)
        #print(self._lockin.query('*IDN?')) # habria que ver si es mejor no pedir IDN. Puede que trabe la comunicacion al ppio
        self._lockin.write("LOCL 2") #Bloquea el uso de teclas del Lockin
        time.sleep(1) # tal vez ayuda a evitar errores de comunicacion del pyvisa
        self.scale = self.get_scale()
        self.time_constant = self.get_time_constant()

    def __del__(self):
        self._lockin.write("LOCL 0") #Desbloquea el Lockin
        self._lockin.close()

    def set_modo(self, modo):
        '''Selecciona el modo de medición, A, A-B, I, I(10M)'''
        self._lockin.write("ISRC {0}".format(modo))

    def set_filtro(self, sen, tbase, slope):
        '''Setea el filtro de la instancia'''
        #Página 90 (5-4) del manual
        self._lockin.write("OFLS {0}".format(slope))
        self._lockin.write("OFLT {0}".format(tbase))
        self._lockin.write("SENS {0}".format(sen))
       
    def set_aux_out(self, auxOut = 1, auxV = 0):
        '''Setea la tensión de salida de al Aux Output indicado.
        Las tensiones posibles son entre -10.5 a 10.5'''
        self._lockin.write('AUXV {0}, {1}'.format(auxOut, auxV))
           
    def set_referencia(self,isIntern, freq, voltaje = 1):
        if isIntern:
            #Referencia interna
            #Configura la referencia si es así
            self._lockin.write("FMOD 1")
            self._lockin.write("SLVL {0:f}".format(voltaje))
            self._lockin.write("FREQ {0:f}".format(freq))
        else:
            #Referencia externa
            self._lockin.write("FMOD 0")
           
    def set_scale(self, scale_number):
        self.scale = min(scale_number,len(self.scale_values))
        self._lockin.write(f'SENS {self.scale}')
        return self.scale
   
    def get_scale(self):
        self.scale = int(self._lockin.query_ascii_values('SENS ?')[0])
        return self.scale

    def set_time_constant(self, time_constant_number):
        self._lockin.write(f'OFLT {time_constant_number}')
        self.time_constant = time_constant_number
        return self.time_constant
   
    def get_time_constant(self):
        return int(self._lockin.query_ascii_values('OFLT ?')[0])

    def set_display(self, isXY):
        if isXY:
            self._lockin.write("DDEF 1, 0") #Canal 1, x
            self._lockin.write('DDEF 2, 0') #Canal 2, y
        else:
            self._lockin.write("DDEF 1,1") #Canal 1, R
            self._lockin.write('DDEF 2,1') #Canal 2, T
   
    def get_display(self):
        '''Obtiene la medición que acusa el display.
        Es equivalente en resolución a la medición de los parámetros con SNAP?'''
        orden = "SNAP? 10, 11"
        return self._lockin.query_ascii_values(orden, separator=",")

       
    def get_medicion(self,isXY = True):
        '''Obtiene X,Y o R,Ang, dependiendo de isXY'''
        orden = "SNAP? "
        if isXY:
            self._lockin.write("DDEF 1,0") #Canal 1, XY
            orden += "1, 2" #SNAP? 1,2
        else:
            self._lockin.write("DDEF 1,1") #Canal 1, RTheta
            orden += "3, 4" #SNAP? 3, 4
        return self._lockin.query_ascii_values(orden, separator=",")
    

    def auto_scale(self):
        '''
        Ajusta automáticamente la escala del Lock-in SR830 para optimizar la medición.
        Utiliza la medición en coordenadas polares (R, θ) y cartesianas (X, Y) 
        para decidir si subir o bajar la escala.
        '''
        debug = True
        sup_threshold = 1  # 100% del rango
        inf_threshold = 0.1  # 10% del rango
        
        nespera = 5  # Se recomienda esperar entre 3 y 5 veces la constante de tiempo entre ajustes
        tespera = self.time_constant_values[self.time_constant] * nespera
        time.sleep(tespera)
    
        # Obtener medición inicial en coordenadas polares (R, θ) y cartesianas (X, Y)
        r, theta = self.get_medicion(isXY=False)
        x, y = self.get_medicion(isXY=True)
    
        # Ajustar la escala si R, X o Y están fuera de los umbrales
        while ((r < self.scale_values[self.scale] * inf_threshold or 
                abs(x) < self.scale_values[self.scale] * inf_threshold or 
                abs(y) < self.scale_values[self.scale] * inf_threshold) and self.scale > 0):
            
            if debug:
                print(f'Bajando escala: R={r}, X={x}, Y={y}, oldscale={self.scale_values[self.scale]}')
            self.scale -= 1
            self.set_scale(self.scale)
            time.sleep(tespera)
            r, theta = self.get_medicion(isXY=False)
            x, y = self.get_medicion(isXY=True)
    
        while ((r > self.scale_values[self.scale] * sup_threshold or 
                abs(x) > self.scale_values[self.scale] * sup_threshold or 
                abs(y) > self.scale_values[self.scale] * sup_threshold) and 
               self.scale < (len(self.scale_values)-1)):
    
            if debug:
                print(f'Subiendo escala: R={r}, X={x}, Y={y}, oldscale={self.scale_values[self.scale]}')
            self.scale += 1
            self.set_scale(self.scale)
            time.sleep(tespera)
            r, theta = self.get_medicion(isXY=False)
            x, y = self.get_medicion(isXY=True)
    
        if debug:
            print(f'Escala ajustada: R={r}, X={x}, Y={y}, scale={self.scale_values[self.scale]}')

        return r, theta, x, y

    
    def read(self):
        return self._lockin.read('\n')
    
    def write(self,myquery):
        self._lockin.write(myquery+'\r','UTF8') # /r: ya termine; /n : nueva linea
        
    def query(self,myquery):
        self.write(myquery)
        return self.read()
    
#%%
    
lockin = SR830('GPIB0::8::INSTR')
#lockin.get_display()
#a = lockin.query('*IDN?')
#print(a)
#lockin.get_medicion()


#%%

x_valores = []
y_valores = []
r_valores = []
theta_valores = []
frecuencias = []

for freq in np.linspace(500, 50000, 10):  # Barrido frecuencias de 1 Hz a 10 kHz
    fungen.write(f'SOURCE1:FREQ {freq}')
    #fungen.write("FREQUENCY 10E3")

    print(f"Frecuencia ajustada a: {freq} Hz")
    
    #set_referencia(self,isIntern, freq, voltaje = 0.5)
    
    # Esperar para estabilizar la medición (tiempo recomendado: 3-5 veces la constante de tiempo)
    time.sleep(lockin.time_constant_values[lockin.get_time_constant()] * 5)
    
    # Ajustar la escala automáticamente
    r, theta, x, y = lockin.auto_scale()
    
    # Guardar los datos en listas
    frecuencias.append(freq)
    x_valores.append(x)
    y_valores.append(y)
    r_valores.append(r)
    theta_valores.append(theta)
    

datos = np.column_stack((frecuencias, x_valores, y_valores, r_valores, theta_valores))


nombre_archivo = "medicion_lockin.csv"
np.savetxt(nombre_archivo, datos, delimiter=',', header='Frecuencia,X,Y,R,Theta', comments='')

print(f"Captura y guardado finalizados. Datos guardados en '{nombre_archivo}'")



#%%

fungen.write('SOURCE1:FREQ 2000')
