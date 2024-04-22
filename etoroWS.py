from browser import Browser
from browser import lgFilters
import time
from datetime import datetime, timedelta
import shutil
import re
import os
import json
import random
import string

class etoro_ws: 
    def __init__(self,login=False,debug=True):
        start_time = time.time()
        
        self.browser = Browser()
        
        if login:
            self.browser.url("https://www.etoro.com/login")
            if not self.browser.esperar_url("etoro.com/home",debug=debug,lgFilterKeysMatch=lgFilters.KeysMatch.CONTAINS,lgFilterKeysSensitive=lgFilters.KeysSensitive.NO):
                return    
        
        #Tiempo de actualizacion = Tiempo en segundo para actualizar la base de datos
        tiempo_actualizacion = 120 * (24*60*60) #Actualizamos cada 120 dias
        self.get_markets(debug=debug, tiempo_actualizacion=tiempo_actualizacion)
        tiempo_actualizacion = 60 * (24*60*60) #Actualizamos cada 60 dias
        self.get_info_markets(debug=debug,  tiempo_actualizacion=tiempo_actualizacion)
        tiempo_actualizacion = 30 * (24*60*60) #Actualizamos cada 30 dias
        self.get_info_markets_elements(debug=debug, tiempo_actualizacion=tiempo_actualizacion)
        self.get_data(debug=debug)
        
        self.browser.close()
        
        elapsed_time_seconds = time.time() - start_time  # Calcula el tiempo transcurrido en segundos
        elapsed_time_timedelta = timedelta(seconds=elapsed_time_seconds)  # Convierte el tiempo transcurrido a un objeto timedelta
        elapsed_time_str = str(elapsed_time_timedelta)  # Convierte el objeto timedelta a una cadena de texto
        print(f"[INFO] El proceso tomó {elapsed_time_str}.")    
         
    def get_markets(self,debug,tiempo_actualizacion = 0):
        if debug:
            print("")
            print("[INFO] GET_MARKETS()")
            

        #CONTROL DEL DIRECTORIO data/etoro
        os.makedirs("data",exist_ok=True)
        path_etoro = os.path.join("data", "ia_info")
        os.makedirs(path_etoro, exist_ok=True)      
        
        #COMPROBAR SI ES NECESARIO ACTUALIZAR
        path_update = os.path.join(path_etoro,"update_etoro.json")
        if os.path.exists(path_update):
            with open(path_update, "r") as file:
                data = json.load(file)
                ultima_actualizacion_str = data.get("ultima_actualizacion")
            ultima_actualizacion = datetime.strptime(ultima_actualizacion_str, "%Y-%m-%d %H:%M:%S")
            tiempo_actual = datetime.now()
            nueva_actualizacion = ultima_actualizacion + timedelta(seconds=tiempo_actualizacion)     
            if nueva_actualizacion > tiempo_actual:
                if debug:
                    print("         - ACTUALIZADO")
                    print("")        
                return
    
        if debug:
            print("         - ACTUALIZANDO...")
            print("")  
        self.browser.url("https://www.etoro.com/discover")          

        #OBTENEMOS TODOS LOS MERCADOS              
        elements_markets = self.browser.get_elements("//a[contains(@href, '/discover/markets/')]", debug=debug) 
        if not elements_markets:
            print("[ERROR] No se encontraron los mercados en ia_info")
            return    

        #CREAMOS EL DICCIONARIO DE MERCADOS
        markets = []
        for element in elements_markets:
            link = element.get_attribute("href")
            
            #Eliminamos los links que no nos interesan
            if "/market-movers" in link:
                break
            
            #Comprobamos que es un mercado que no esta en la lista
            market_exist = False
            if len(markets) > 0:
                market_exist = any(link == market['link'] for market in markets)
            
            #Si es un market nuevo
            if not market_exist:
                nombre = link.split("/")[-1].lower().strip().replace(" ", "")
                markets.append(
                    {
                        'nombre':nombre,
                        'link':link,
                        'estado':True
                    }
                )     
                if debug:
                    print(f"[INFO] Mercado encontrado: Nombre {nombre}. Url: {link}.")                    
            
        #Control de mercados que ya no estan activos
        carpetas_existentes = os.listdir(path_etoro)
        for carpeta_existente in carpetas_existentes:
            #Si no existe la carpeta en los mercados activos
            if not any(market['nombre'] == carpeta_existente for market in markets):
                path_completo = os.path.join(path_etoro,carpeta_existente)
                if debug:
                    print(f"[INFO] La carpeta '{carpeta_existente}' no coincide con ningún mercado activo.")               
                json_path = os.path.join(path_etoro,carpeta_existente,'info_etoro.json')
                #Si la carpeta tiene el archivo info_etoro.json
                if os.path.exists(json_path):
                     # Marcar la carpeta como inactiva actualizando el estado en el archivo info_etoro.json
                    with open(json_path, 'r+') as file:
                        data = json.load(file)
                        data['estado'] = False
                        file.seek(0)
                        json.dump(data, file, indent=4)
                        file.truncate()
                    if debug:
                        print(f"[INFO] Se ha marcado la carpeta '{path_completo}' como inactiva.")                    
                else:
                    # Eliminar la carpeta si no tiene un archivo info_etoro.json
                    if debug:
                        print(f"[INFO] La carpeta '{path_completo}' no tiene un archivo 'info_etoro.json'. Se eliminará la carpeta.")
                    shutil.rmtree(path_completo)
                    if debug:
                        print(f"[INFO] La carpeta '{path_completo}' ha sido eliminada.")
                    
        #Establecer el valor de los nuevos mercados
        for market in markets:
            path_completo = os.path.join(path_etoro,market['nombre'])
            os.makedirs(path_completo, exist_ok=True)
            #Escribir los datos json
            with open(os.path.join(path_completo, "info_etoro.json"), "w") as f:
                json.dump(market, f, indent=4)
            if debug:
                print(f"[INFO] Carpeta: {path_completo}. Link: {market['link']}. Estado: {market['estado']}")                           
        
        
        # GUARDAMOS ACTUALIZACION
        tiempo_actual = datetime.now()
        data = {
            "ultima_actualizacion": tiempo_actual.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(path_update, "w") as file:
            json.dump(data, file)
        
    def get_info_markets(self,debug, tiempo_actualizacion = 0):
        if debug:
            print("")
            print(f"[INFO] GET_INFO_MARKETS()")
        
        ruta_etoro = "data/ia_info"
        carpetas_etoro = [nombre for nombre in os.listdir(ruta_etoro) if os.path.isdir(os.path.join(ruta_etoro, nombre))]
        #CARPETAS DENTRO DE LA CARPETA ETORO QUE ESTAN ACTIVAS Y NECESITAN SER ACTUALIZADAS
        carpetas = []
        for carpeta_etoro in carpetas_etoro:
            #COMPROBAR SI ES NECESARIO ACTUALIZAR
            path_update = os.path.join(ruta_etoro, carpeta_etoro,"update_etoro.json")
            if os.path.exists(path_update):
                with open(path_update, "r") as file:
                    data = json.load(file)
                    ultima_actualizacion_str = data.get("ultima_actualizacion")
                ultima_actualizacion = datetime.strptime(ultima_actualizacion_str, "%Y-%m-%d %H:%M:%S")
                tiempo_actual = datetime.now()
                nueva_actualizacion = ultima_actualizacion + timedelta(seconds=tiempo_actualizacion)     
                if nueva_actualizacion > tiempo_actual:
                    if debug:
                        print(f"         - Carpeta: {os.path.join(ruta_etoro,carpeta_etoro)}. Actualizada")       
                    continue
                        
            #LINKS ALMACENADOS EN CARPETAS[] QUE SON NECESARIO ESTUDIA
            ruta_link_info = os.path.join(ruta_etoro, carpeta_etoro, "info_etoro.json")
            if os.path.exists(ruta_link_info):
                # Leer los datos del archivo JSON
                with open(ruta_link_info, "r") as f:
                    datos_json = json.load(f)
                            
                # Extraer el nombre, el enlace y el estado del archivo JSON
                nombre = datos_json.get("nombre", "")
                link = datos_json.get("link", "")
                estado = datos_json.get("estado", "")     
                if estado == True:
                    carpetas.append(
                        {
                            'nombre':nombre,
                            'link':link,
                            'estado':estado
                        }
                    )   
                if debug:
                    print(f"         - Carpeta: {os.path.join(ruta_etoro,carpeta_etoro)}. Link: {link}. Estado: {estado}.") 
        if debug:
            print("") 

        #ACTUALIZAMOS CARPETAS        
        for carpeta in carpetas:                   
            #Info de cada carpeta
            carpetas_internas = []
            
            #Entramos en el link
            self.browser.url(carpeta['link'])
            if debug:
                print(f"[INFO] Extrayendo datos de {carpeta['link']}")   
            
            #NAVEGAMOS HASTA LA PÁGINA DE EXTRACCION DE DATOS
            div_subcategorias = self.browser.get_element(xpath="//et-sub-categories", maximo_intentos=10, debug=False)
            if div_subcategorias:
                if debug:
                    print("[INFO] Buscando pagina de extraccion de datos.")
                lista_mercado = self.browser.get_element(xpath="//et-sub-categories//et-select", maximo_intentos=10, debug=False)
                if lista_mercado:
                    self.browser.click(lista_mercado,debug=False)
                    if debug:         
                        print("[INFO] Modo de extraccion de datos mediante listado")
                else:
                    if debug:
                        print("[INFO] No se encontro un listado, probando mediante enlaces")
                    
                enlace = self.browser.get_element(maximo_intentos=10,debug=False,xpath=f"//et-sub-categories//a")
                if enlace:
                    if debug:
                        print("[INFO] Url de extraccion de datos encontrado")
                    self.browser.url(enlace.get_attribute("href"))
                    if debug:
                        print("[INFO] Redireccion a la pagina de extraccion de datos completada")
                else:
                    print("[ERROR] No se encontraron los enlaces a la pagina de extraccion")
            else:
                if debug:
                    print("[INFO] Pagina de extraccion de datos encontrada.")            
            
            
            path_carpeta  = os.path.join(ruta_etoro, carpeta["nombre"])
            #Comprobamos si solo hay un mercado o varios                
            xpath_nombres = "//et-select[contains(@automation-id,'discover') and not(contains(@automation-id,'instrument'))]//a"
            xpath_click_nombres = "//et-select[contains(@automation-id,'discover') and not(contains(@automation-id,'instrument'))]//et-select-header"
            lista_mercados_element = self.browser.get_element(maximo_intentos=10,debug=False,xpath=xpath_click_nombres)
            link = self.browser.current_url()
            #Hay varios mercados
            if lista_mercados_element:
                if debug:
                    print(f"[INFO] {link}: Tiene varios mercados.")

                maximo_intentos = 50
                contador = 1
                while maximo_intentos > 0:                
                    #OBTENEMOS LOS VALORES DEL MERCADO ACTUAL
                    try:
                        element_market = self.browser.get_element(maximo_intentos=10,debug=False,xpath="//et-select[contains(@automation-id,'discover') and not(contains(@automation-id,'instrument'))]//et-select-header//*[contains(@automation-id,'select-header-text')]")
                        nombre_market = element_market.get_attribute("innerHTML").lower().strip().replace(" ", "")
                        link_market = self.browser.current_url()
                                
                        if len(carpetas_internas) < 1 or not any(nombre_market == carpeta_int['nombre'] for carpeta_int in carpetas_internas):
                            carpetas_internas.append({
                                'carpeta': path_carpeta,
                                'nombre':nombre_market,
                                'link':link_market,
                                'estado': True,      
                            })
                            if nombre_market == "all":
                                nombre_market = "todo"
                                if debug:
                                    print(f" ({contador}) all --> {nombre_market}") 
                            else:                                       
                                if debug:
                                    print(f" ({contador}) {nombre_market}")     
                            contador += 1                     
                    except:
                        self.browser.esperar(1)
                        maximo_intentos -= 1
                        continue
                    
                    #Desplegamos los mercados
                    try:
                        lista_mercados_element = self.browser.get_element(maximo_intentos=5,debug=False,xpath=xpath_click_nombres)
                        if lista_mercados_element:
                            if not self.browser.click(element=lista_mercados_element,debug=False,name="lista_mercados_element"):
                                maximo_intentos -= 1
                                continue
                    except:
                        maximo_intentos -= 1
                        continue
                    
                    #Obtenemos la lista de mercados
                    try:
                        lista_de_mercados  = self.browser.get_elements(maximo_intentos=5,debug=False,xpath=xpath_nombres)
                        if lista_de_mercados:
                            link_aux = self.browser.current_url()
                            elemento_encontrado = False
                            for element in lista_de_mercados:
                                nombre_element = element.get_attribute("innerHTML").lower().strip().replace(" ", "")
                                if not any(nombre_element == carpeta_int['nombre'] for carpeta_int in carpetas_internas):
                                    if not self.browser.click(element=element,debug=False,name=nombre_element):
                                        maximo_intentos -= 1
                                    else:
                                        elemento_encontrado = True
                                        aux_maximos_intentos = 15
                                        while link_aux == self.browser.current_url() and aux_maximos_intentos > 0:
                                            self.browser.esperar(1)
                                            aux_maximos_intentos -= 1
                                        if aux_maximos_intentos == 0:
                                            elemento_encontrado = False
                                        else:
                                            self.browser.esperar(1)
                            if not elemento_encontrado:
                                maximo_intentos -= 1
                    except:
                        maximo_intentos -= 1
                    
            #Solo hay un mercado
            else:
                if debug:
                    print(f"[INFO] {link}: Solo tiene un mercado.")
                carpetas_internas.append({
                    'carpeta': path_carpeta,
                    'nombre':'todo',
                    'link':link,
                    'estado': True,      
                })
            
            #CREO EL ARCHIVO JSON    
            for carpeta in carpetas_internas:
                ruta_carpeta = os.path.join(carpeta['carpeta'],carpeta['nombre'])
                os.makedirs(ruta_carpeta, exist_ok=True)
                my_json = {
                    'nombre':carpeta['nombre'],
                    'link':carpeta['link'],
                    'estado':carpeta['estado']
                }
                ruta_json = os.path.join(ruta_carpeta,"info_etoro.json")
                with open(ruta_json, 'w') as archivo_json:
                    json.dump(my_json, archivo_json)
                if debug:
                    print(f"[INFO] Nueva carpeta: {ruta_carpeta}. Link: {carpeta['link']}. Estado: {carpeta['estado']}.")
        
            #ANALIZO SI HAY ALGUNA QUE NO ESTA ACTIVA
            carpetas_etoro_internas = [nombre for nombre in os.listdir(path_carpeta) if os.path.isdir(os.path.join(path_carpeta,nombre))]    
            for nombre_carpeta in carpetas_etoro_internas:
                ruta_completa = os.path.join(path_carpeta,nombre_carpeta)
                if not any(ruta_completa == os.path.join(car_int['carpeta'],car_int['nombre']) for car_int in carpetas_internas):
                    if os.path.exists(os.path.join(ruta_completa, "info_etoro.json")):
                        if debug:
                            print(f"[INFO] La carpeta {ruta_completa} se ha marcado como incativa")
                        # Si tiene archivo json, marcarlo con estado = False
                        with open(os.path.join(ruta_completa, "info_etoro.json"), 'r+') as archivo_json:
                            data = json.load(archivo_json)
                            data['estado'] = False
                            archivo_json.seek(0)
                            json.dump(data, archivo_json, indent=4)
                            archivo_json.truncate()
                    else:
                        if debug:
                            print(f"[INFO] La carpeta {ruta_completa} se ha eliminado")
                        # Si no tiene archivo json, borrar la carpeta
                        shutil.rmtree(ruta_completa)
            
            # GUARDAMOS ACTUALIZACION
            path_update = os.path.join(path_carpeta,"update_etoro.json")
            tiempo_actual = datetime.now()
            data = {
                "ultima_actualizacion": tiempo_actual.strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(path_update, "w") as file:
                json.dump(data, file)                
    
    def get_info_markets_elements(self,debug,tiempo_actualizacion = 0):
        #VARIABLES DE REINICIO DE BROWSER (Para no saturar la memoria)
        num_guardados = 0 #Contador de veces que he guardado
        num_guardados_reset = 5 #Cada cuantas veces se resetea el navegador
        
        if debug:
            print("")
            print(f"[INFO] GET_INFO_MARKETS_ELEMENTS()")
    
        #RUTA DE LOS ELEMENTOS
        ruta_etoro = "data/ia_info"
        carpetas_etoro = [nombre for nombre in os.listdir(ruta_etoro) if os.path.isdir(os.path.join(ruta_etoro, nombre))]
        for carpeta_etoro in carpetas_etoro:
            path_carpeta_etoro = os.path.join(ruta_etoro,carpeta_etoro)
            carpetas_market = [nombre for nombre in os.listdir(path_carpeta_etoro) if os.path.isdir(os.path.join(path_carpeta_etoro, nombre))]    
            for carpeta_market in carpetas_market:
                ruta_carpeta = os.path.join(path_carpeta_etoro,carpeta_market)      
                cantidad_elementos = "" #Variable global que dice los elementos que deben haber en el market             
                
                #INFORMACION DE LA CARPETA
                link_market = ""
                nombre_market = ""
                estado_market = True
                
                path_info_etoro = os.path.join(ruta_carpeta,"info_etoro.json")
                if os.path.exists(path_info_etoro):
                    with open(path_info_etoro, "r") as file:
                        data = json.load(file)
                        link_market = data.get("link","")
                        nombre_market = data.get("nombre","")
                        estado_market = data.get("estado",False)    

                if link_market == "":
                    print(f"[ERROR] La carpeta {path_info_etoro} no contiene el link del mercado.")
                    continue
                
                #COMPROBAR SI ES NECESARIO ACTUALIZAR     
                siguiente_actualizacion = None #Fecha de la siguiente actualizacion
                estado = False #Si existe estado se pondre True, al no ser que un link interno se haya desactivado
                links_analizados = set() #Lista de links extraidos
                
                path_update = os.path.join(ruta_carpeta,"update_etoro.json")
                if os.path.exists(path_update):
                    with open(path_update, "r") as file:
                        data = json.load(file)
                        ultima_actualizacion = data.get("ultima_actualizacion")
                        links_analizados = set(data.get("links_analizados", [])) #Lo guardamos como array pero por tema de memoria lo manejamos como {}
                        estado = data.get("estado",True) #Si no existe estado lo manejamos como si existiera, esto se debe a que es un nuevo mercado o lo estamos actualizando en las primeras versiones                   
                        #Formateo de las fechas
                        ultima_actualizacion = datetime.strptime(ultima_actualizacion, "%Y-%m-%d %H:%M:%S")
                        siguiente_actualizacion = ultima_actualizacion + timedelta(seconds=tiempo_actualizacion)  

                self.browser.url(link_market) #Vamos a la pagina web del mercado
                
                if not estado: #Quiere decir que update_etoro no existe o hay un link que no esta correcto
                    if debug:
                        print(f"         - Carpeta: {ruta_carpeta}. Actualizando...")
                    links_analizados = set()
                else:
                    tiempo_actual = datetime.now()
                    #OBTENEMOS LA CANTIDAD DE ELEMENTOS
                    try:          
                        elemento_number = self.browser.get_element(xpath="//span[contains(@automation-id,'discover-market-results-num')]",maximo_intentos=10,debug=False)
                        cantidad_elementos = elemento_number.text.replace(" ","") 
                    except:
                        pass
                    
                    #NO HEMOS SOBREPASADO EL TIEMPO PARA LA ACTUALIZACION OBLIGATORIA
                    if siguiente_actualizacion > tiempo_actual:                        
                        #COMPROBAMOS SI HAY ALGUN ERROR EN LA ULTIMA ACTUALIZACION
                        if any("ERROR" == link_analizado for link_analizado in links_analizados):
                            links_analizados = {link.replace("https://www.etoro.com/", "") for link in links_analizados if link != "ERROR" and link != "FIN"}
                            if debug:
                                print(f"         - Carpeta: {os.path.join(path_carpeta_etoro,carpeta_market)}. Actualizando: Sucedio un error en la anterior actualizacion, {len(links_analizados)}/{cantidad_elementos} elementos analizados")    
                        #SI NO HAY ERROR, COMPROBAMOS SI YA HEMOS LLEGADO AL FINAL
                        elif any("FIN" == link_analizado for link_analizado in links_analizados):
                            links_analizados = {link.replace("https://www.etoro.com/", "") for link in links_analizados if link != "ERROR" and link != "FIN"}
                            if cantidad_elementos != str(len(links_analizados)): #Si no es la misma cantidad no esta actualizada
                                if debug:
                                    print(f"         - Carpeta: {os.path.join(path_carpeta_etoro,carpeta_market)}. No actualizada: {len(links_analizados)}/{cantidad_elementos} elementos")                
                            else: #Si es la misma cantidad esta actualizada
                                if debug:
                                    print(f"         - Carpeta: {os.path.join(path_carpeta_etoro,carpeta_market)}. Actualizada: {len(links_analizados)}/{cantidad_elementos} elementos")      
                                continue 
                        #NO HAY ERRORES NI FIN, SEGUIMOS ACTUALIZANDO
                        else:
                            links_analizados = {link.replace("https://www.etoro.com/", "") for link in links_analizados if link != "ERROR" and link != "FIN"}  
                            if debug:
                                print(f"         - Carpeta: {os.path.join(path_carpeta_etoro,carpeta_market)}. Actualizando: {len(links_analizados)}/{cantidad_elementos} elementos analizados")              
                    #ACTUALIZACION OBLIGATORIA
                    else:
                        links_analizados = {link.replace("https://www.etoro.com/", "") for link in links_analizados if link != "ERROR" and link != "FIN"}  
                        if debug:
                            print(f"         - Carpeta: {os.path.join(path_carpeta_etoro,carpeta_market)}. Actualizando: Buscando nuevos elementos: {len(links_analizados)} elementos analizados.")    


                #ANALIZAMOS LA CARPETA SI ESTA ACTIVA
                if not estado_market:
                    if debug:
                        print(f"            - [INFO] NO ESTA ACTIVA LA CARPETA: {ruta_carpeta}. LINK: {link_market}.")    
                    continue
                
                if debug:
                        print(f"            - [INFO] Extrayendo elementos de {nombre_market}: {link_market}")


                #PARAMETROS AUTOSAVE
                CANTIDAD_PARA_GUARDAR = 120 #Cantidad de elementos que almacena antes de guardar
                links_mercado = set() #Links para guardar
                aux_guardar = False #Auxiliar que indica que hemos llegado al final y guarda
                autosave_intentos = 50 #Limita el bucle para posibles fallos
                xpath_link = "//et-instrument-trading-row//et-card-avatar//a" #XPath para obtener los links
                contador_id = 1 #Sirve para que el debug sea mas visual
                bool_links = True #Sirve para mostrar el mensaje EXTRAYENDO LINKS y que sea mas visual el debug
                first_save = True #Sirve para hacer el primer guardado aunque no haya elementos nuevos (Esto es para cuando ha pasado el tiempo de actualziacion)
               
                #AUTOSAVE v3
                while autosave_intentos > 0 or aux_guardar:
                    #OBTENEMOS LOS ELEMENTOS QUE NOS DAN LINKS
                    elementos_pagina = self.browser.get_elements(xpath=xpath_link,maximo_intentos=10,debug=False)     
                    maximo_intentos = 20
                    while maximo_intentos > 0:
                        if not elementos_pagina:
                            elementos_pagina = self.browser.get_elements(xpath=xpath_link,maximo_intentos=10,debug=False)       
                            maximo_intentos -= 1 
                        else:
                            break
                    if maximo_intentos == 0:
                        autosave_intentos -= 1
                        if autosave_intentos == 0:
                            print(f"            - [ERROR] No se pudo obtener elementos_pagina")
                        url_actual = self.browser.current_url()
                        self.browser.close()
                        self.browser = Browser()
                        self.browser.url(url_actual)
                        break    
                    
                    #CONTROLAMOS SI ES NECESARIO PULSAR EL BOTON SIGUIENTE (si existe)
                    siguiente_pagina = True
                    
                    for elemento in elementos_pagina:
                        try:
                            link_elemento = elemento.get_attribute("href")
                            #SI NO ESTA EN LINKS MERCADOS NI LINKS ANALIZADOS SE TRATA DE UN NUEVO ELEMENTOS
                            if not any(link_elemento in "https://www.etoro.com/" + link_analizado for link_analizado in links_analizados) and not any(link_elemento in link_mercado for link_mercado in links_mercado):
                                if bool_links and debug:
                                    print("              -------------------- [INFO] EXTRAYENDO LINKS --------------------")
                                    bool_links = False
                                    
                                #AÑADIMOS AL MERCADO SIEMPRE QUE NO SUPERE LA CANTIDAD A GUARDAD
                                if CANTIDAD_PARA_GUARDAR > len(links_mercado):
                                    links_mercado.add(link_elemento)
                                    if debug:
                                        print(f"            - ({contador_id}) - Link: {link_elemento}")  
                                        contador_id += 1 
                                #HEMOS LLEGADO AL LIMITE, NO DAMOS A LA SIGUIENTE PAGINA
                                else:
                                    siguiente_pagina = False
                        except:
                            contador_id = -1                            
                            break
                    
                    #CONTROL DE ERRORES PARA BOTON SIGUIENTE
                    if contador_id == -1:
                        autosave_intentos -= 1
                        continue
                            

                    #GUARDAMOS LA INFORMACION (limite alcanzado, o fin con aux_guardar)
                    if CANTIDAD_PARA_GUARDAR <= len(links_mercado) or aux_guardar:
                        if debug and len(links_mercado) > 0:
                            print("              --------------------- [INFO] EXTRAYENDO API ---------------------")  
                        bool_links = True #Sirve para volver luego a mostrar EXTRAYENDO LINKS en el debug
                        
                        #PARAMETROS DE LA API
                        info_mercado_json = set()
                        procesed_links = set()
                        contador_info = 1                      
                        
                        #ANALIZAMOS CADA ELEMENTO DE LA API
                        for link_mercado in links_mercado:
                            #NOS DIRIGIMO A LA GRAFICA DEL MERCADO
                            try:
                                self.browser.url(link_mercado + "/chart")
                            except:
                                try:
                                    self.browser.url(link_mercado)
                                    elemento_grafica = self.browser.get_element(xpath="//a[contains(@automation-id,'et-tab-chart')]",maximo_intentos=10,debug=False)
                                    if not elemento_grafica and not self.browser.click(element=elemento_grafica,debug=debug,name="elemento_grafica"):
                                        autosave_intentos -= 1
                                        if autosave_intentos == 0:
                                            print(f"[ERROR] No se pudo extraer la grafica de {link_mercado}")
                                            break
                                    else:
                                        self.browser.url(elemento_grafica.get_attribute("href"))
                                except:
                                    autosave_intentos -= 1
                                    if autosave_intentos <= 0:
                                        print(f"[ERROR] No se pudo extraer la grafica de {link_mercado}")
                                        break                                
                            
                            #INFORMACION DE LA API
                            try:
                                elemento_nombre = self.browser.get_element(xpath="//h1[contains(@automation-id,'header-instrument-name')]",maximo_intentos=10,debug=False)
                                elemento_full_nombre = self.browser.get_element(xpath="//h1[contains(@automation-id,'header-instrument-name')]//span",maximo_intentos=10,debug=False)
                                enombre = elemento_nombre.text
                                efullnombre = elemento_full_nombre.text
                                enombre = enombre.replace(efullnombre,"").replace("\n","").strip()
                                efullnombre = efullnombre.replace("Future","").replace("Before","").strip()
                                    
                                if efullnombre == "" and enombre == "":
                                    efullnombre = '_'.join(random.choices(string.ascii_letters + string.digits, k=5))
                                elif efullnombre == "":
                                    efullnombre = enombre
                                elif enombre == "":
                                    enombre = efullnombre   
                                    
                                elemento = {
                                    'carpeta':re.sub(r'[^a-zA-Z0-9]', '_', enombre),
                                    'siglas':enombre,
                                    'nombre':efullnombre,
                                    'link':link_mercado,
                                    'linkWS':"",
                                    'estado':True,
                                }    
                                                             
                                elemento['linkWS'] = self.get_url_for_data().replace("OneDay","OneMinute")                      
                                
                                
                                if elemento['linkWS'] == "":
                                    autosave_intentos -= 1
                                    print(f"            - [WARNING] {elemento['carpeta']}: {elemento['siglas']} ({elemento['nombre']}). Estado {elemento['estado']} LinkWS: No se pudo extraer")
                                else:        
                                    if debug:   
                                        print(f"            - ({contador_info}/{len(links_mercado)}) - {elemento['carpeta']}: {elemento['siglas']} ({elemento['nombre']}). Estado {elemento['estado']} LinkWS: {elemento['linkWS']}")
                                    contador_info+=1
                                    info_mercado_json.add(tuple(elemento.items()))    
                                    procesed_links.add(link_mercado)
                                                                    
                            except Exception as e:
                                autosave_intentos -= 1
                                self.browser.close()
                                self.browser = Browser()
                                print(f"            - [WARNING] Error autosolucionable: {e}")
                                                            
                        #LIBERACION DE RECURSOS
                        if num_guardados >= num_guardados_reset:
                            self.browser.close()
                            self.browser = Browser()
                            num_guardados = 0
                        else:
                            num_guardados += 1
                        
                        for link in procesed_links:
                            if link in links_mercado:
                                links_mercado.remove(link)
                                
                        #Volvemos a la pagina antes de guardar
                        self.browser.url(link_market)
                                
                             
                        #GUARDANDO PROGRESO   
                        if debug and len(info_mercado_json) > 0:
                            print("              -------------------- [INFO] GUARDANDO PROGRESO -------------------")
            
                        #PARAMETROS
                        contador_json = 1
                        
                        #FUNCION DE GUARDADO INFO_ETORO.JSON
                        for info_mercado in info_mercado_json:
                            elemento_info = dict(info_mercado)
                            #Ruta del info_etoro.json del elemento
                            ruta_info_json = os.path.join(ruta_carpeta,elemento_info['carpeta'])
                            os.makedirs(ruta_info_json,exist_ok=True) #Creamos directorio si no existe
                            ruta_info_json = os.path.join(ruta_info_json,"info_etoro.json")  
                            #GUARDAMOS INFO_ETORO.JSON
                            try:
                                with open(ruta_info_json, 'w') as f:
                                    json.dump(elemento_info, f, indent=4)
                                if debug:   
                                    print(f"            - ({contador_json}/{len(info_mercado_json)}) - {elemento_info['carpeta']}/info_etoro.json")
                                contador_json += 1    
                                links_analizados.add(elemento_info['link'].replace("https://www.etoro.com/",""))

                            except Exception as e:
                                autosave_intentos -= 1
                                if debug:
                                    print(f"            - [WARNING] Error autosolucionable info_etoro.json: {e}")
                                if autosave_intentos <= 0:
                                    print(f"            - [ERROR] FIN")
                                    break
                                links_mercado.add(elemento_info['link'])    #Se vuelve a añadir para volver a estudiarlo                     
                        info_mercado_json.clear()
                        #FUNCION DE GUARDADO UPDATE_ETORO.JSON
                        try:
                            path_update = os.path.join(ruta_carpeta,"update_etoro.json")
                            tiempo_actual = datetime.now()
                            data = {
                                "ultima_actualizacion": tiempo_actual.strftime("%Y-%m-%d %H:%M:%S"),
                                "estado": True,
                                "links_analizados": ["https://www.etoro.com/" + link for link in links_analizados]
                            }
                            with open(path_update, "w") as file:
                                json.dump(data, file)    
                        except Exception as e:
                            autosave_intentos -= 1
                            if debug:
                                print(f"            - [WARNING] Error autosolucionable update_etoro.json: {e}")
                            if autosave_intentos <= 0:
                                print(f"            - [ERROR] FIN")
                                break 
                                            
                    #PULSAMOS BOTON SIGUIENTE
                    if siguiente_pagina:
                        #ENCONTRAMOS EL BUTTON
                        maximo_intentos_next = 2
                        xpath_next_button = "//*[contains(@class,'menu-button-hp discover-page')]//*[contains(@automation-id,'next-button')]"
                        next_button = self.browser.get_element(xpath=xpath_next_button,maximo_intentos=3,debug=False)
                        while maximo_intentos_next > 0:
                            if not next_button:
                                next_button = self.browser.get_element(xpath=xpath_next_button,maximo_intentos=3,debug=False)
                                if not next_button:
                                    maximo_intentos_next -= 1
                                else:
                                    break
                            else:
                                break
                        #NO HAY NEXT BUTTON GUARDAMOS Y FINALIZAMOS
                        if not next_button:
                            autosave_intentos = 0
                            if first_save:
                                aux_guardar = True
                                first_save = False
                            else:
                                aux_guardar = False
                                first_save = True #Reseteamos el primer guardado
                                if debug:
                                    if aux_guardar == False and debug:    
                                        print(f"            - [INFO] Extraccion completada, no existe next_button")
                        else:
                            if "disabled" in next_button.get_attribute("class"):
                                autosave_intentos = 0
                                if first_save:
                                    aux_guardar = True
                                    first_save = False
                                else:
                                    aux_guardar = False
                                    first_save = True
                                    if debug:
                                        print(f"            - [INFO] Extraccion completada, no hay mas elementos")
                            else:
                                aux_guardar = False
                                try:
                                    #Obtenemos el link anterior para ver que al dar siguiente obtenemos otro link
                                    link_anterior = elementos_pagina[0].get_attribute("href")
                                    if self.browser.click(next_button,debug=False,name="next_button"):
                                        #Obtenemos los elementos de la pagina
                                        elementos_pagina = self.browser.get_elements(xpath=xpath_link,maximo_intentos=10,debug=False)     
                                        maximo_intentos = 5
                                        while maximo_intentos > 0:
                                            if not elementos_pagina:
                                                elementos_pagina = self.browser.get_elements(xpath=xpath_link,maximo_intentos=10,debug=False)    
                                                maximo_intentos -= 1   
                                            else:
                                                if elementos_pagina[0].get_attribute("href") != link_anterior:
                                                    break
                                except:
                                    autosave_intentos -= 1
                                    if autosave_intentos == 0:
                                        links_analizados.add("ERROR")  
                                        print(f"            - [ERROR] Next button obtuvo un error fatal")             
                      
                # GUARDAMOS ACTUALIZACION
                if str(len(links_analizados)) == cantidad_elementos and not any("ERROR" == link_analizado for link_analizado in links_analizados):
                    if debug:
                        print(f"            - [FIN] {len(links_analizados)} elementos en la carpeta")
                    links_analizados.add("FIN")                
                else:
                    if debug:
                        print(f"            - [WARNING] No se encontraron todos los elementos ({len(links_analizados)}/{cantidad_elementos}).")
                    links_analizados.add("ERROR")
    
                path_update = os.path.join(ruta_carpeta,"update_etoro.json")
                tiempo_actual = datetime.now()
                data = {
                    "ultima_actualizacion": tiempo_actual.strftime("%Y-%m-%d %H:%M:%S"),
                    "estado": True,
                    "links_analizados":  ["https://www.etoro.com/" + link if link not in {"ERROR", "FIN"} else link for link in links_analizados],
                }
                with open(path_update, "w") as file:
                    json.dump(data, file)                             
    
            
    #GET MARKETS
    def get_url_for_data(self):
        eventos = []
        maximo_intentos = 10
        while maximo_intentos > 0:
            eventos = self.browser.get_log(
                lgFilterMode=lgFilters.Mode.OR,
                filters= [lgFilters.LogKeys.REQUEST_URL,
                lgFilters.KeysMatch.CONTAINS,
                lgFilters.KeysSensitive.NO,
                "candle.etoro.com/candles/asc.json/O"])

            for evento in eventos:
                url = evento[lgFilters.LogKeys.REQUEST_URL]
                if url and url.startswith("https:"):
                    parts = url.split("?")
                    if len(parts) > 1:
                        return parts[0]
                
                if maximo_intentos == 5:
                    self.browser.url(self.browser.current_url())
                    
            maximo_intentos -= 1
            self.browser.esperar(1)    
        return ""
    
    def get_data(self,debug):
        pass
        