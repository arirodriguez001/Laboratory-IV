# -*- coding: utf-8 -*-
#%%Librerías
import pyvisa as visa
import numpy as np

#%%Lock In
class SR830:
    '''
    Clase para el manejo amplificador Lockin SR830 usando PyVISA de interfaz.
    Manual: https://www.thinksrs.com/downloads/pdfs/manuals/SR830m.pdf

    ...
    
    Parámetros
    -------
    direccion : str
        Dirección del dispositivo en la PC.
    **config
        Parámetros opcionales de configuración inicial:
            medicion_modo : {'A', 'A-B', 'I1', 'I100'}
            display_modo : {'XY', 'RT'}
            sens : int, str
            slope : int, str
            t_int : int, str
    
    Atributos
    -------
    direccion : str
        Dirección del dispositivo en la PC.
    '''

    def __init__(self, direccion, **config):

        self._lockin = visa.ResourceManager().open_resource(direccion)
        print(self._lockin.query('*IDN?'))
        self.direccion = direccion

        #ConfiguraciÃ³n inicial del Lock In

        #Modo de mediciÃ³n
        self.setModo(config['medicion_modo'])

        #Display del panel frontal
        self.setDisplay(config['display_modo'])

        #Sensibilidad
        self.setSensibility(config['sens'])

        #Slope del filtro
        self.setFilterSlope(config['slope'])

        #Tiempo de integraciÃ³n del filtro
        self.setIntegrationTime(config['t_int'])

    def __del__(self,):
        self._lockin.close()
        
    def setVoltage(self,ch,x):
        ch = str(ch)
        if ch not in ['1', '2', '3', '4']:
            raise TypeError('El canal introducido no es válido.')
        else:
            self._lockin.write(f'AUXV {ch}, {x}')

    def setModo(self, modo):
        '''
        Establece la configuración de entrada.

        Parámetros
        ----------
        modo : {'A', 'A-B', 'I1', 'I100'}
            Configuraciones válidas:
                - A
                - A-B
                - I1    (1 MOhm)
                - I100  (100 MOhm)
        '''
        ref = {'A':0, 'A-B':1, 'I1':2, 'I100':3}
        try:
            n = ref[modo]
        except:
            raise TypeError('El modo introducido no es válido.')
        self._lockin.write(f'ISRC {n}')

    def setSensibility(self, sens):
        '''
        Establece la sensibilidad.

        Parámetros
        ----------
        sens : int, string
            Sensibilidad máxima. Para que el string sea válido debe contener el
            valor máximo seguido de la unidad (nV, uV, mV o V), con o sin
            espacio. Ejemplo: 50uV. En caso de ser un número entre 0 y 26 usa
            identificador según la tabla del manual.
        '''
        
        sensibilidades = [f'{i}{u}' for u in ['nv','uv','mv','v'] for i in 
                          [j*k for k in [1,10,100]
                           for j in [1,2,5]]][1:-8]
        
        if sens in range(27):
            s = sens
        elif sens.replace(' ','').lower() in sensibilidades:
            s = sensibilidades.index(sens.replace(' ','').lower())
        else:
            raise TypeError('La sensibilidad ingresada es inválida.')
        self._lockin.write(f'SENS {s}')    

    def setIntegrationTime(self, temp):
        '''
        Establece el tiempo de integración del filtro.

        Parámetros
        ----------
        sens : int, string
            Para que el string sea válido debe contener el valor máximo seguido
            de la unidad (us, ms, s o ks), con o sin espacio. Ejemplo: 100us.
            En caso de ser un número entre 0 y 19 usa el identificador según la
            tabla del manual.
        '''
        tiempos = [f'{i}{u}' for u in ['us','ms','s','ks'] for i in 
                          [j*k for k in [1,10,100]
                           for j in [1,3]]][2:-2]
        
        if temp in range(20):
            t = temp
        elif temp.replace(' ','').lower() in tiempos:
            t = tiempos.index(temp)
        else:
            raise TypeError('El tiempo ingresado es inválido.')
        self._lockin.write(f'OFLT {t}')

    def setFilterSlope(self, slope):
        '''
        Establece la pendiente del filtro pasabajos.

        Parámetros
        ----------
        slope : int, str
            Las pendientes válidas del filtro, en decibeles por octava, son:
            6dB, 12dB, 18dB, 24dB; sin importar las mayúsculas ni el espacio.
            Si es un entero entre 0 y 3 se usa el identificador de la tabla del
            manual.
        '''
        slopes = [6,12,18,24]
        strs = [f'{s}db' for s in slopes]
        
        if slope in range(4):
            s = slope
        elif slope in slopes:
            s = slopes.index(slope)
        elif slope.replace(' ','').lower() in strs:
            s = strs.index(slope.replace(' ','').lower())
        else:
            raise TypeError('La pendiente del filtro no es válidaa.')
        self._lockin.write(f'OFSL {s}')

    def setReferencia(self, estado=True, f=None, V=None):
        '''
        Configura la señal de referencia interna.
        
        Parámetros
        ----------
        estado : bool, int. Opcional.
            Verdadero (1) si se desea usar la referencia interna, falso (0) en
            caso contrario. True por defecto
        f : float, None. Opcional.
            Frecuencia de referencia interna en Hz (máximo 102000Hz). None por defecto.
        V : float, None. Opcional. 
            Amplitud de referencia interna en Volts. None por defecto.
        '''
        #prender o apagar referencia interna
        if estado in range(2):
            i = estado
        elif type(estado)==bool:
            i = int(estado)
        else:
            raise TypeError('El estado de la referencia interna debe ser un boolean (1 o 0).')
        self._lockin.write(f'FMOD {i}')
        
        #frecuencia
        if f is None:
            pass
        elif f<+102000:
            self._lockin.write(f'FREQ {f}')
        else:
            raise TypeError('La frecuencia de referencia debe ser un número real menor a 102e3')
            
        #amplitud
        if V is None:
            pass
        elif V>=0.004 and V<=5:
            self._lockin.write(f'SLVL {V}')
        else:
            raise TypeError('El voltaje de referencia debe ser un número real entre 0.004 y 5')

    def setDisplay(self, modo):
        '''
        Setea el display del panel frontal del Lock-In:

        Parámetros
        ----------
        modo : {'XY', 'RT'}
            -'XY': modo X-Y
            -'RT': modo R-Theta.
        '''
        if modo=='XY':
            self._lockin.write('DDEF 1, 0') #Canal 1, x
            self._lockin.write('DDEF 2, 0') #Canal 2, y
        elif modo=='RT':
            self._lockin.write('DDEF 1,1') #Canal 1, R
            self._lockin.write('DDEF 2,1') #Canal 2, Theta
        else:
            raise TypeError('No entendí lo que querés ver en el display')
            
    def getModo(self):
        '''
        Devuelve la configuración de salida.

        Devuelve
        ----------
        modo : {'A', 'A-B', 'I1', 'I100'}
            Configuraciones válidas:
                - A
                - A-B
                - I1    (1 MOhm)
                - I100  (100 MOhm)
        '''
        ref = ('A', 'A-B', 'I1', 'I100')
        iden = int(self._lockin.write('ISRC?'))
        return ref[iden]

    def getDisplay(self):
        '''
        Obtiene las mediciones para cada canal que acusa el display.

        Devuelve
        -------
        CH1 : float
            Medición del canal 1.
        CH2 : TYPE
            Medición del canal 2.

        '''
        CH1, CH2 = self._lockin.query_ascii_values('SNAP? 10, 11', separator=",")
        return CH1, CH2

    def getMedicion(self, modo):
        '''
        Obtiene las mediciones instantáneas según el modo.

        Parámetros
        ----------
        modo : str
            Define las mediciones a tomar y el orden. Los valores válidos son:
            -'XY': Valores XY
            -'RT': Valores RT

        Devuelve
        -------
        Mediciones : float
            Devuelve las mediciones solicitadas separadamente.

        '''
        if modo=='XY':
            snap = 'SNAP? 1, 2'
        elif modo=='RT':
            snap = 'SNAP? 3, 4'
        else:
            raise TypeError('El modo introducido no es válido. Ver referencia.')
        return self._lockin.query_ascii_values(snap, separator=',')
    
    def getIntegrationTime(self):
        '''
        Obtiene el tiempo de integración, tanto la identificación proporcionada
        por la tabla del manual como su correspondiente traducción a segundos.

        Devuelve
        -------
        n : int
            Identificador según tabla.
        t : TYPE
            Tiempo de integración en segundos.

        '''
        n = int(self._lockin.query('OFLT?'))

        #Lo siguiente convierte a tiempo el parámetro i de la sección 5-6
        if n % 2 == 0:
            t = 1 * 10**(n/2-5)
        else:
            t = 3 * 10**((n-1)/2 - 5)

        return n, t
    
    def getSensibility(self):
        '''
        Obtiene la sensibilidad (valor máximo), tanto la identificación proporcionada
        por la tabla del manual como su correspondiente traducción a Volts.

        Devuelve
        -------
        s : int (entre 0 y 19)
            Identificador según tabla.
        S : float
            Sensibilidad (valor máximo) en Volts.
        modo : str
            Escala de voltaje o corriente.

        '''
        modo = self.getModo()
        s = int(self._lockin.query('SENS?'))
        if modo in ['A', 'A-B']:
            sens = [i*10**j for j in range(-9,0) for i in [2,5,10]]
        elif modo in ['I1', 'I100']:
            sens = [i*10**j for j in range(-15,-6) for i in [2,5,10]]
        S = sens[s]
        return s, S
    
    def getFilterSlope(self):
        '''
        Obtiene la pendiente del filtro pasabajos según los identificadores
        proporcionados por la tabla del manual.

        Devuelve
        -------
        s : int (entre 0 y 3)
            Identificador según tabla.

        '''
        s = int(self._lockin.query('OFSL?'))
        return s
    
   

#%%Generador de Funciones
class AFG3021B:
    
    def __init__(self, name):
        self._generador = visa.ResourceManager().open_resource(name)
        print(self._generador.query('*IDN?'))
        
        #Activa la salida
        self._generador.write('OUTPut1:STATe on')
        # self.setFrequency(1000)
        
    def __del__(self):
        self._generador.close()
        
    def setFrequency(self, freq):
        self._generador.write(f'FREQ {freq}')
        
    def getFrequency(self):
        return self._generador.query_ascii_values('FREQ?')
        
    def setAmplitude(self, freq):
        print('falta')
        
    def getAmplitude(self):
        print('falta')
        return 0

#%%Osciloscopio
class TDS1002B:
    """Clase para el manejo osciloscopio TDS2000 usando PyVISA de interfaz
    """
    
    def __init__(self, name):
        self._osci = visa.ResourceManager().open_resource(name)
        print(self._osci.query("*IDN?"))

    	#Configuración de curva
        
        # Modo de transmision: Binario positivo.
        self._osci.write('DAT:ENC RPB') 
        # 1 byte de dato. Con RPB 127 es la mitad de la pantalla
        self._osci.write('DAT:WID 1')
        # La curva mandada inicia en el primer dato
        self._osci.write("DAT:STAR 1") 
        # La curva mandada finaliza en el Ãºltimo dato
        self._osci.write("DAT:STOP 2500") 

        #Adquisición por sampleo
        self._osci.write("ACQ:MOD SAMP")
				
        #Bloquea el control del osciloscopio
        self._osci.write("LOC")
    	
    def __del__(self):
        self._osci.close()			

    def config(self):
        #Seteo de canal
        self.set_channel(channel=1, scale=20e-3)
        self.set_channel(channel=2, scale=20e-3)
        self.set_time(scale=1e-3, zero=0)

    def unlock(self):
         #Desbloquea el control del osciloscopio
        self._osci.write("UNLOC")

    def setChannel(self, channel, scale, zero=0):
    	#if coup != "DC" or coup != "AC" or coup != "GND":
    	    #coup = "DC"
    	#self._osci.write("CH{0}:COUP ".format(canal) + coup) #Acoplamiento DC
    	#self._osci.write("CH{0}:PROB 
        self._osci.write("CH{0}:SCA {1}".format(channel, scale))
        self._osci.write("CH{0}:POS {1}".format(channel, zero))
	
    def getChannel(self, channel):
        return self._osci.query("CH{0}?".format(channel))
    
    def getScale(self, channel):
        if channel==1 or channel==2:
            pass
        else:
            raise TypeError('Fuente no válida')
        return self._osci.query_ascii_values(f'CH{channel}:SCA?')[0]
		
    def setTime(self, scale, zero=0):
        self._osci.write("HOR:SCA {0}".format(scale))
        self._osci.write("HOR:POS {0}".format(zero))	
	
    def getTime(self):
        return self._osci.query_ascii_values('HOR:MAI:SCA?')[0]
	
    def readData(self, channel):
        # Hace aparecer el canal en pantalla. Por si no está¡ habilitado
        self._osci.write("SEL:CH{0} ON".format(channel)) 
        # Selecciona el canal
        self._osci.write("DAT:SOU CH{0}".format(channel)) 
    	#xze primer punto de la waveform
    	#xin intervalo de sampleo
    	#ymu factor de escala vertical
    	#yoff offset vertical
        xze, xin, yze, ymu, yoff = self._osci.query_ascii_values('WFMPRE:XZE?;XIN?;YZE?;YMU?;YOFF?;', 
                                                                 separator=';') 
        data = (self._osci.query_binary_values('CURV?', datatype='B', 
                                               container=np.array) - yoff) * ymu + yze        
        tiempo = xze + np.arange(len(data)) * xin
        return tiempo, data
    
    def getRange(self, channel):
        xze, xin, yze, ymu, yoff = self._osci.query_ascii_values('WFMPRE:XZE?;XIN?;YZE?;YMU?;YOFF?;', 
                                                                 separator=';')         
        rango = (np.array((0, 255))-yoff)*ymu +yze
        return rango   
    
    def getState(self):
        return self._osci.query('ACQ:STATE?')
    
    def setState(self, st='ON'):
        st = st.upper()
        self._osci.write(f'ACQ:STATE {st}') 
        while int(self.getState())==1:
            pass
        
    def getStopa(self):
        return self._osci.query('ACQ:STOPA?')
    
    def setStopa(self, st='RUNST'):
        st = st.upper()
        self._osci.write(f'ACQ:STOPA {st}')
        
    def getMeasure(self, i=1):
        return float(self._osci.query(f'MEASU:MEAS{i}:VAL?'))
    
    def setMeasure(self, n, source, tipo):
        if source==1 or source==2:
            source = f'CH{source}'
        elif source=='MATH':
            source = 'MATH'
        else:
            raise TypeError('La fuente es inválida')
        self._osci.write(f'MEASU:MEAS{n}:SOU {source}')
        self._osci.write(f'MEASU:MEAS{n}:TYP {tipo}')
    
    def setAvg(self, num=4):
        self._osci.write('ACQ:MOD AVE')
        self._osci.write('ACQ:NUMAV 128')
