from browser import Browser
from browser import lgFilters
import time
from datetime import datetime, timedelta
import shutil
import re
import os
import json

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
                   
    def get_info_markets_elements(self,debug, tiempo_actualizacion = 0):   
        num_guardados = 0
        num_guardados_reset = 5   
        if debug:
            print("")
            print(f"[INFO] GET_INFO_MARKETS_ELEMENTS()")
            
        ruta_etoro = "data/ia_info"
        carpetas_etoro = [nombre for nombre in os.listdir(ruta_etoro) if os.path.isdir(os.path.join(ruta_etoro, nombre))]
        for carpeta_etoro in carpetas_etoro:
            path_carpeta_etoro = os.path.join(ruta_etoro,carpeta_etoro)
            carpetas_market = [nombre for nombre in os.listdir(path_carpeta_etoro) if os.path.isdir(os.path.join(path_carpeta_etoro, nombre))]    
            for carpeta_market in carpetas_market:
                links_analizados = []        
                ruta_carpeta = os.path.join(path_carpeta_etoro,carpeta_market)
                #COMPROBAR SI ES NECESARIO ACTUALIZAR
                path_update = os.path.join(ruta_carpeta,"update_etoro.json")
                if os.path.exists(path_update):
                    with open(path_update, "r") as file:
                        data = json.load(file)
                        ultima_actualizacion_str = data.get("ultima_actualizacion")
                        links_analizados = data.get("links_analizados", [])
                    ultima_actualizacion = datetime.strptime(ultima_actualizacion_str, "%Y-%m-%d %H:%M:%S")
                    tiempo_actual = datetime.now()
                    nueva_actualizacion = ultima_actualizacion + timedelta(seconds=tiempo_actualizacion)     
                    if nueva_actualizacion > tiempo_actual:
                        if any("ERROR" == link_analizado for link_analizado in links_analizados):
                            if debug:
                                print(f"         - Carpeta: {os.path.join(path_carpeta_etoro,carpeta_market)}. Actualizando: Sucedio un error en la anterior actualizacion, {len(links_analizados) } elementos analizados")    
                            links_analizados = [link.replace("https://www.etoro.com/", "") for link in links_analizados if link != "ERROR"]
                            links_analizados = set(links_analizados)
                        elif any("FIN" == link_analizado for link_analizado in links_analizados):
                            if debug:
                                print(f"         - Carpeta: {os.path.join(path_carpeta_etoro,carpeta_market)}. Actualizada: {len(links_analizados) - 1} elementos")      
                            continue 
                        else:
                            if debug:
                                print(f"         - Carpeta: {os.path.join(path_carpeta_etoro,carpeta_market)}. Actualizando: {len(links_analizados) } elementos analizados")      
                                links_analizados = [link.replace("https://www.etoro.com/", "") for link in links_analizados]
                                links_analizados = set(links_analizados)               
                    else:
                        links_analizados = {}
                else:
                    links_analizados = {}
                #COMPROBAMOS EL ARCHIVO info_etoro.json
                path_info_json = os.path.join(ruta_carpeta,"info_etoro.json")
                if os.path.exists(path_info_json):
                    #INFORMACION DE LA CARPETA
                    nombre = ""
                    link = ""
                    estado = False
                    #ruta_carpeta
                    
                    #ASIGNACION DE VALORES
                    with open(path_info_json, 'r') as archivo_json:
                        datos_json = json.load(archivo_json)
                        nombre = datos_json['nombre']
                        link = datos_json['link']
                        estado = datos_json['estado']                    
                    
                    #CARPETA QUE ESTA ACTIVA Y NECESITA SER ACTUALIZADA
                    if estado:
                        if debug:
                            print(f"[INFO] Carpeta: {ruta_carpeta}. Link: {link}")
                    
                        #ELEMENTOS HACE REFERENCIA A TODOS LOS MERCADOS QUE HAY                  
                        self.browser.url(link)
                        
                        if debug:
                            print(f"[INFO] Extrayendo elementos de {nombre}: {link}")

                        #AUTOSAVE V2
                        CANTIDAD_PARA_GUARDAR = 120
                        aux_guardar = False
                        links_mercado = []
                        autosave_intentos = 100
                        xpath_link = "//et-instrument-trading-row//et-card-avatar//a"
                        contador_id = 1
                        bool_links = True
                        while autosave_intentos > 0 or aux_guardar:
                            #Obtenemos los elementos de la pagina
                            elementos_pagina = self.browser.get_elements(xpath=xpath_link,maximo_intentos=10,debug=False)     
                            maximo_intentos = 20
                            while maximo_intentos > 0:
                                if not elementos_pagina:
                                    elementos_pagina = self.browser.get_elements(xpath=xpath_link,maximo_intentos=10,debug=False)       
                                    maximo_intentos -= 1 
                                else:
                                    break
                            if maximo_intentos == 0:
                                print(f"[ERROR] No se pudo obtener elementos")
                                autosave_intentos -= 1
                                url_actual = self.browser.current_url()
                                self.browser.close()
                                self.browser = Browser()
                                self.browser.url(url_actual)
                                break                                 
                            
                            
                            #Controlamos si es necesario pulsar al boton siguiente (si existe)
                            siguiente_pagina = True
                            for elemento in elementos_pagina:
                                try:
                                    link_elemento = elemento.get_attribute("href")
                                    if not any(link_elemento in "https://www.etoro.com/" + link_analizado for link_analizado in links_analizados) and not any(link_elemento in link_mercado for link_mercado in links_mercado):
                                        if bool_links and debug:
                                            print(" -------------------- [INFO] EXTRAYENDO LINKS --------------------")
                                            bool_links = False
                                        siguiente_pagina = False
                                        if CANTIDAD_PARA_GUARDAR > len(links_mercado):
                                            links_mercado.append(link_elemento)
                                            if debug:
                                                print(f" ({contador_id}) - Link: {link_elemento}")  
                                        else: #No hemos sobrepasado el limite
                                            siguiente_pagina = True
                                        contador_id += 1    
                                except:
                                    contador_id = -1
                                    break
                                
                            if contador_id == -1:
                                autosave_intentos -= 1
                                continue
                            
                            #Hemos llegado al limite del autosave
                            if CANTIDAD_PARA_GUARDAR == len(links_mercado) or aux_guardar:
                                bool_links = True
                                #Guardamos la url porque vamos a analizar uno a uno
                                url_actual = self.browser.current_url()
                                contador_id = 1
                                #ANALIZAMOS CADA LINK DEL MERCADO
                                info_mercado_json = []
                                contador_info = 1
                                if debug:
                                    print(" --------------------- [INFO] EXTRAYENDO API ---------------------")
                                
                                processed_links = []
                                
                                for link_mercado in links_mercado:                                
                                    try:
                                        #SI NO LO ES LA ACTUALIZAMOS
                                        self.browser.url(link_mercado + "/chart")
                                        
                                        elemento_nombre = self.browser.get_element(xpath="//h1[contains(@automation-id,'header-instrument-name')]",maximo_intentos=10,debug=False)
                                        elemento_full_nombre = self.browser.get_element(xpath="//h1[contains(@automation-id,'header-instrument-name')]//span",maximo_intentos=10,debug=False)
                                        enombre = elemento_nombre.text
                                        efullnombre = elemento_full_nombre.text
                                        enombre = enombre.replace(efullnombre,"").replace("\n","").strip()
                                        efullnombre = efullnombre.replace("Future","").replace("Before","").strip()
                                        
                                        if enombre == "":
                                            enombre = efullnombre
                                        
                                        elemento = {
                                            'carpeta':re.sub(r'[^a-zA-Z0-9]', '_', enombre),
                                            'siglas':enombre,
                                            'nombre':efullnombre,
                                            'link':link_mercado,
                                            'linkWS':"",
                                            'estado':True,
                                        }
                                        #elemento_grafica = self.browser.get_element(xpath="//a[contains(@automation-id,'et-tab-chart')]",maximo_intentos=10,debug=False)
                                        #if not elemento_grafica and not self.browser.click(element=elemento_grafica,debug=debug,name="elemento_grafica"):
                                        #    elemento['estado'] = False
                                        #else:
                                        #    self.browser.url(elemento_grafica.get_attribute("href"))
                                        elemento['linkWS'] = self.get_url_for_data().replace("OneDay","OneMinute")                      
                                        if debug:   
                                            print(f" ({contador_info}/{len(links_mercado)}) - {elemento['carpeta']}: {elemento['siglas']} ({elemento['nombre']}). Estado {elemento['estado']} LinkWS: {elemento['linkWS']}")
                                            contador_info+=1
                                            
                                        info_mercado_json.append(elemento)    
                                        processed_links.append(link_mercado)
                                    
                                    except Exception as e:
                                        self.browser.close()
                                        self.browser = Browser()
                                        print(f"[WARNING] Error autosolucionable: {e}")
                                
                                #Lo hago para liberar memoria cada 10 guardados:
                                if num_guardados >= num_guardados_reset:
                                    self.browser.close()
                                    self.browser = Browser()
                                    num_guardados = 0
                                else:
                                    num_guardados += 1
                                
                                #Volvemos a la pagina antes de guardar
                                self.browser.url(url=url_actual)
                                
                                # Eliminar los enlaces procesados de la lista principal
                                for link in processed_links:
                                    links_mercado.remove(link)
                                
                                if debug:
                                    print(" -------------------- [INFO] GUARDANDO PROGRESO -------------------")
            
                                #GUARDAMOS EL JSON 
                                contador_json = 1
                                for elemento_info in info_mercado_json:
                                    ruta_info_json = os.path.join(ruta_carpeta,elemento_info['carpeta'])
                                    os.makedirs(ruta_info_json,exist_ok=True)
                                    ruta_info_json = os.path.join(ruta_info_json,"info_etoro.json")      
                                    # Escribir el diccionario en el archivo JSON
                                    try:
                                        with open(ruta_info_json, 'w') as f:
                                            json.dump(elemento_info, f, indent=4)
                                        if debug:   
                                            print(f" ({contador_json}/{len(info_mercado_json)}) - {elemento_info['carpeta']}/info_etoro.json")
                                            contador_json += 1    
                                        links_analizados.add(elemento_info['link'].replace("https://www.etoro.com/",""))
                                    except Exception as e:
                                        if debug:
                                            print(f"[WARNING] Error autosolucionable {e}")
                                        links_mercado.append(elemento_info['link'])                        
                                
                                # GUARDAMOS ACTUALIZACION
                                try:
                                    path_update = os.path.join(ruta_carpeta,"update_etoro.json")
                                    tiempo_actual = datetime.now()
                                    data = {
                                        "ultima_actualizacion": tiempo_actual.strftime("%Y-%m-%d %H:%M:%S"),
                                        "links_analizados": ["https://www.etoro.com/" + link for link in links_analizados]
                                    }
                                    with open(path_update, "w") as file:
                                        json.dump(data, file)    
                                except:
                                    pass  
                                
                                #Limpiamos la lista mercado
                                info_mercado_json.clear()
                   
                            #Pulsamos el boton siguiente
                            if siguiente_pagina:
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
                                    
                                #NO HAY NEXT BUTTON GUARDAMOS Y FINALIZAMOS
                                if not next_button:
                                    autosave_intentos = 0
                                    if len(links_mercado) > 0:
                                        aux_guardar = True
                                    else:
                                        aux_guardar = False
                                    if debug:
                                        if aux_guardar == False and debug:    
                                            print(f"[INFO] Extraccion completada, no existe next_button")
                                else:
                                    if "disabled" in next_button.get_attribute("class"):
                                        autosave_intentos = 0
                                        if len(links_mercado) > 0:
                                            aux_guardar = True
                                        else:
                                            aux_guardar = False
                                        if debug:
                                            print(f"[INFO] Extraccion completada, no hay mas elementos")
                                    else:
                                        aux_guardar = False
                                        try:
                                            link_anterior = elementos_pagina[0].get_attribute("href")
                                            if self.browser.click(next_button,debug=False,name="next_button"):
                                                #Obtenemos los elementos de la pagina
                                                elementos_pagina = self.browser.get_elements(xpath=xpath_link,maximo_intentos=10,debug=False)     
                                                maximo_intentos = 20
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
                                                print(f"[ERROR] Next button obtuvo un error fatal")             
                      
                        # GUARDAMOS ACTUALIZACION
                        try:
                            elemento_number = self.browser.get_element(xpath="//span[contains(@automation-id,'discover-market-results-num')]",maximo_intentos=10,debug=False)
                            if str(len(links_analizados)) == elemento_number.text.replace(" ","") and not any("ERROR" == link_analizado for link_analizado in links_analizados):
                                if debug:
                                    print(f"[FIN] {len(links_analizados)} elementos en la carpeta")
                                links_analizados.add("FIN")
                                
                            else:
                                if debug:
                                    print("[WARNING] No se extrajeron todos los elementos correctamente")
                                links_analizados.add("ERROR")
                        except Exception as e:
                            if debug:
                                print(f"[WARNING] Error obteniendo cantidad elmentos: {e}")
                            links_analizados.add("FIN")
                            
                        path_update = os.path.join(ruta_carpeta,"update_etoro.json")
                        tiempo_actual = datetime.now()
                        data = {
                            "ultima_actualizacion": tiempo_actual.strftime("%Y-%m-%d %H:%M:%S"),
                            "links_analizados":  ["https://www.etoro.com/" + link if link not in {"ERROR", "FIN"} else link for link in links_analizados]
                        }
                        with open(path_update, "w") as file:
                            json.dump(data, file)                             
                    #LA CARPETA SE ENCUENTRA CON EL ESTADO EN FALSE
                    else:
                        if debug:
                            print(f"[INFO] Carpeta: {ruta_carpeta}. Estado: {estado}")
                #NO HAY ARCHIVO JSON DENTRO DE LA CARPETA
                else:
                    if debug:
                        print(f"[INFO] Carpeta: {ruta_carpeta}. No contiene el archivo info_etoro.json")
            
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
            maximo_intentos -= 1
            self.browser.esperar(1)    
        return ""
    
    def get_data(self,debug):
        pass
        