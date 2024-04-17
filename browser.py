from time import sleep
import shutil
import socket
import sys
import os
import subprocess
import requests
from datetime import datetime
import random

from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from enum import Enum
import json
import socket
import base64

def search_file(ruta, empieza, mayusSensible=False):
    for elemento in os.listdir(ruta):
        ruta_elemento = os.path.join(ruta, elemento)
        if os.path.isdir(ruta_elemento):
            # Si el elemento es una carpeta, buscar dentro de ella de forma recursiva
            resultado = search_file(ruta_elemento, empieza, mayusSensible)
            if resultado:
                return resultado
        else:
            # Si el elemento es un archivo, comprobar si empieza por 'empieza' (mayúsculas o minúsculas según mayusSensible)
            if mayusSensible:
                if elemento.startswith(empieza):
                    return ruta_elemento
            elif elemento.upper().startswith(empieza.upper()):
                return ruta_elemento
    return None

def copy_directory(origen, destino):
    # Verificar si el destino no existe, entonces crearlo
    if not os.path.exists(destino):
        os.makedirs(destino)

    # Recorrer los archivos en la carpeta de origen
    for archivo in os.listdir(origen):
        ruta_origen = os.path.join(origen, archivo)
        if os.path.isfile(ruta_origen):
            # Copiar el archivo a la carpeta de destino con el mismo nombre
            ruta_destino = os.path.join(destino, archivo)
            shutil.copy2(ruta_origen, ruta_destino)
        elif os.path.isdir(ruta_origen):
            # Si es una carpeta, copiar recursivamente
            copy_directory(ruta_origen, os.path.join(destino, archivo))

def wait_to_internet_connected(debug=False):
    intentos_maximos = 300
    tiempo_espera = 2
    while intentos_maximos > 0:          
        try:
            # Intenta crear un socket para verificar la conexión a Internet
            socket.setdefaulttimeout(3)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            if debug:
                print(f"[INFO] Conexion a internet establecida.")
                if intentos_maximos < 300:
                    sleep(10)
            return True
        except Exception as e:
            print(f"[INFO] Intento {300 - intentos_maximos + 1}/{300}: No hay conexion a internet. Esperando {tiempo_espera} segundos...")
            sleep(tiempo_espera)
            intentos_maximos -= 1
    print(f"[ERROR] No se puede continuar sin conexion a internet")
    return False

# Obtener la ruta chromedrive
current_directory = os.getcwd()
chromedriver_folder = 'chromedriver'
chromedriver_path = os.path.join(current_directory, chromedriver_folder)
chromedrive_file = None

def is_chromedrive_installed():
    # Verificar si la carpeta chromedriver ya existe
    if not os.path.exists(chromedriver_path):
        return False
    
    archivos = os.listdir(chromedriver_path)
    for archivo in archivos:
        if 'chromedriver' in archivo.lower():  
            chromedrive_file = os.path.join(chromedriver_path,archivo)
            print(f"[INFO] Chromedrive esta instalado {chromedrive_file}")
            return True
    return False

def install_chromedrive():
    # Verificar si la carpeta chromedriver ya existe
    if not os.path.exists(chromedriver_path):
        print(f"[INFO] Carpeta creada {chromedriver_path}")
        os.makedirs(chromedriver_path) 

    print(f"[INFO] Instalando ChromeDrive.")
    # Establecer la variable de entorno WDM_LOG_LEVEL para especificar la ubicación de la instalación de chromedriver
    os.environ['WDM_LOG_LEVEL'] = '0'
    os.environ['WDM_LOCAL'] = 'True'
    os.environ['WDM_PRINT_FIRST_LINE'] = 'False'
    os.environ['WDM_TARGET_PATH'] = chromedriver_path
    try:
        ChromeDriverManager().install()
    except Exception as e:
        print(f"[ERROR] ChromeDriveManager.install() no funciono correctamente, pruebe a actualizar chrome o instale de forma manual chromedrive para continuar: {e}")
        return False
    ruta_chromedrive = search_file(current_directory,"license")
    if ruta_chromedrive == None:
        print(f"[ERROR] Instale chromedrive de forma manual!")
        return False
    carpeta_chromedrive = os.path.dirname(ruta_chromedrive)
    print(f"[INFO] ChromeDrive instalado: {carpeta_chromedrive}")
    print(f"[INFO] Configurando chromedrive en el proyecto.")
    try:
        # Copiar el contenido de la carpeta origen a la carpeta destino
        copy_directory(carpeta_chromedrive, chromedriver_path)
        print(f"[INFO] Contenido copiado con éxito: {carpeta_chromedrive} >> {chromedriver_path}")
        print(f"[INFO] Modificando binario para no ser detectable...")
        for file in os.listdir(chromedriver_path):
            if file.lower().startswith("chromedrive"):
                datos_binarios = None
                with open(os.path.join(chromedriver_path, file), "rb") as archivo:
                    datos_binarios = archivo.read()
                    indice = datos_binarios.find("cdc_".encode())
                    if indice == -1:
                        print(f"[INFO] La variable 'cdc_' no se encontró en los datos binarios.")
                    else:
                        # Reemplaza el nombre original con el nombre nuevo
                        datos_binarios = datos_binarios[:indice] + 'xay_'.encode() + datos_binarios[indice+len("cdc_"):]
                        print(f"[INFO] Se modifico la variable 'cdc_' por 'xay_'")
                    indice = datos_binarios.find("wdc_".encode())
                    if indice == -1:
                        print(f"[INFO] La variable 'wdc_' no se encontró en los datos binarios.")
                    else:
                        # Reemplaza el nombre original con el nombre nuevo
                        datos_binarios = datos_binarios[:indice] + 'dqo_'.encode() + datos_binarios[indice+len("wdc_"):]
                        print(f"[INFO] Se modificó la variable 'wdc_' por 'dqo_'")
                    if datos_binarios != None:
                        with open(os.path.join(chromedriver_path, file), "wb") as archivo:
                            archivo.write(datos_binarios)
                            print(f"[INFO] Datos binarios de {os.path.join(chromedriver_path, file)} modificados.")    
                    else:
                            print(f"[INFO] No fue necesario modificar los datos binarios de {os.path.join(chromedriver_path, file)}.")                 
    except Exception as e:
        print(f"[ERROR] No se pudo copiar el contenido: {carpeta_chromedrive} >> {chromedriver_path}\n ERROR MSG: {e}")
        return False
                
    carpeta_basura = os.path.join(current_directory, os.path.relpath(ruta_chromedrive, current_directory).split(os.sep)[0])
    try:                    
        #Eliminando archivos basura
        shutil.rmtree(carpeta_basura) 
        print(f"[INFO] Se ha eliminado '{carpeta_basura}'")
    except Exception as e:
        print(f"[ERROR] No se pudo eliminar la carpeta {carpeta_basura}\n ERROR MSG: {e}")
        print(f"[INFO] Proyecto configurado")
    return True

url_certificado = "https://raw.githubusercontent.com/wkeeling/selenium-wire/master/seleniumwire/ca.crt"
    
def is_cert_installed():
    try:
        if sys.platform.startswith('linux'):
            return is_cert_installed_linux("ca.crt")
        elif sys.platform.startswith('win'):
            return is_cert_installed_windows("ca.crt")
        else:
            print("Sistema operativo no compatible.")
            return False
    except Exception as e:
        print(f"[ERROR] Error al verificar si el certificado está instalado: {e}")
        return False

def is_cert_installed_linux(cert_subject):
    try:
        # Obtener la lista de certificados instalados en el sistema
        certs = os.listdir('/etc/ssl/certs/')
        # Comprobar si el certificado está en la lista
        return cert_subject in certs
    except Exception as e:
        print(f"[ERROR] Error al verificar si el certificado está instalado en Linux: {e}")
        return False

def is_cert_installed_windows(cert_subject):
    try:
        # Ejecutar el comando para obtener la lista de certificados instalados en Windows
        output = subprocess.check_output(["certutil", "-store", "Root"], stderr=subprocess.STDOUT)
        # Decodificar la salida utilizando diferentes codecs
        try:
            decoded_output = output.decode('utf-8')
        except UnicodeDecodeError:
            decoded_output = output.decode('latin-1')  # Intentar con otro codec si falla UTF-8
        # Verificar si el certificado está en la lista
        return cert_subject in decoded_output
    except Exception as e:
        print(f"[ERROR] Error al verificar si el certificado está instalado en Windows: {e}")
        return False
    
def install_cert():
    try:
        # Obtener el certificado desde la URL
        cert_respuesta = requests.get(url_certificado, timeout=5,verify=False)
        cert_data = cert_respuesta.content
        
        # Guardar el certificado en un archivo temporal
        cert_path = os.path.join(chromedriver_path, "ca.crt")
        with open(cert_path, 'wb') as archivo_certificado:
            archivo_certificado.write(cert_data)
        
        # Instalar el certificado en el sistema
        if sys.platform.startswith('linux'):
            if not install_cert_linux(cert_path):
                return False
        elif sys.platform.startswith('win'):
            if not install_cert_windows(cert_path):
                return False
        else:
            print("[ERROR] Sistema operativo no compatible.")
            return False
        
        print(f"[INFO] Certificado instalado correctamente en el sistema.")
        return True
    
    except Exception as e:
        print(f"[ERROR] No se pudo instalar el certificado: {e}")
        return False

def install_cert_linux(cert_path):
    try:
        # Copiar el certificado al directorio de certificados de confianza
        shutil.copy(cert_path, '/usr/local/share/ca-certificates/')
        # Actualizar el almacén de certificados
        os.system('update-ca-certificates')
        return True
    except Exception as e:
        print(f"[ERROR] No se pudo instalar el certificado en Linux: {e}")
        return False

def install_cert_windows(cert_path):
    try:
        # Ejecutar el comando para instalar el certificado en Windows
        subprocess.run(["certutil", "-addstore", "Root", cert_path], check=True)
        return True
    except Exception as e:
        print(f"[ERROR] No se pudo instalar el certificado en Windows: {e}")
        return False
        
def get_options():
    options = uc.ChromeOptions()
    options.add_argument('--allow-insecure-localhost') #Permitir certificados locales
    options.add_argument('--disable-popup-blocking') 
    options.add_argument('--start-maximized')  # Iniciar maximizado
    options.add_argument('--blink-settings=imagesEnabled=false')
    options.add_argument('--no-first-run')
    options.add_argument('--no-service-autorun')
    options.add_argument('--password-store=0')
    options.add_argument('--incognito')
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    return options
    
def getWait(time, positive = True):
    if positive:
        aux = time - 0.25
        if aux < 0:
            aux = 0
        return (aux) + random.uniform(0, 0.5)
    return (time - 0.25) + random.uniform(0, 0.5)

class lgFilters:
    class Mode(Enum):
        OR = "OR"
        AND = "AND"
            
    class LogKeys(Enum):
        NIVEL = 'nivel'
        HORA = 'hora'
        METODO = 'metodo'
        ID = 'id'
        URL = 'url'
        REQUEST_URL = 'request_url'
        TIPO = 'tipo'
        BODY = 'body'
        
    class KeysMatch(Enum):
        EQUAL = 'equal'
        START = 'starts'
        CONTAINS = 'in'

    class KeysSensitive(Enum):
        NO = 'lower'
        YES = 'normal'
            

class Browser:
    def __init__(self):
        self.driver = None
        use_seleniumwire = False
        # Verificamos la instalación de Chromedriver
        if not is_chromedrive_installed():
            if wait_to_internet_connected(debug=True):
                if not install_chromedrive():
                    return
                
        # Verificamos la instalación del certificado
        if use_seleniumwire:
            if not is_cert_installed():
                if wait_to_internet_connected(debug=True):
                    if not install_cert():
                        return
        wait_to_internet_connected(debug=True)
        
        # Creamos opciones
        options = get_options()
        caps = DesiredCapabilities.CHROME.copy()
        caps['goog:loggingPrefs'] = {'performance': 'ALL'}
        # Creamos el driver
        self.driver = uc.Chrome(driver_executable_path=chromedrive_file,desired_capabilities=caps, options=options)
        self.reset_log()
        
    #FUNCIONES TIEMPO
    def tiempo_espera(self,tiempo=5):
        return getWait(tiempo)   
    def esperar(self,tiempo=5):
        sleep(getWait(tiempo))

    #FUNCIONES DRIVER
    def close(self):
        if self.driver != None:
            self.driver.close()

    #FUNCIONES URL
    def current_url(self):
        if self.driver != None:
            return self.driver.current_url
        else:
            return ""
    
    def url(self, url):
        if self.driver != None:
            if wait_to_internet_connected():
                self.driver.get(url)
                # Esperar hasta que el estado del documento sea "complete"
                WebDriverWait(self.driver, self.tiempo_espera()).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, 'body'))
                )
                return True
            else:
                return False
    def esperar_url(self,url,debug=False, lgFilterKeysMatch=lgFilters.KeysMatch.EQUAL, lgFilterKeysSensitive=lgFilters.KeysSensitive):
        maximo_intentos = 300
        if self.driver != None:
            while maximo_intentos >= 0:
                try:
                    url_navegador = self.driver.current_url
                except Exception as e:
                    print("[ERROR] No se pudo obtener la URL del navegador:", e)
                    return False
                url_comprobar = url
                if lgFilterKeysSensitive == lgFilters.KeysSensitive.NO:
                    url_navegador = url_navegador.lower()
                    url_comprobar = url_comprobar.lower()
                
                if lgFilterKeysMatch == lgFilters.KeysMatch.EQUAL:
                    if url_navegador == url_comprobar:
                        return True
                elif lgFilterKeysMatch == lgFilters.KeysMatch.START:
                    if url_navegador.startswith(url_comprobar):
                        return True
                else:
                    if url_comprobar in url_navegador:
                        return True
                
                if debug:
                    print(f"[INFO] Esperando a la página web: {url}, intento {301 - maximo_intentos} de {300}")    
                
                maximo_intentos -= 1
                self.esperar(1)  # Espera 1 segundo entre intentos
                
            if debug:
                print("[INFO] Se alcanzó el número máximo de intentos")
            return False
        else:
            if debug:
                print("[ERROR] El controlador del navegador no está disponible")
            return False
    
    #FUNCIONES ELEMENTOS
    def get_elements(self, xpath=None, maximo_intentos=30, debug=False):
        if not xpath or self.driver is None:
            if debug:
                print("[ERROR] No existe el driver o el xpath en la funcion get_elements()")
            return None
        
        try:
            # Utilizando WebDriverWait para esperar hasta que al menos un elemento sea visible
            elements = WebDriverWait(self.driver, 1).until(
                EC.visibility_of_any_elements_located((By.XPATH, xpath))
            )
            return elements
        
        except:
            if maximo_intentos > 0:
                if debug:
                    print(f"[ERROR] Elementos no encontrados con xpath {xpath} después de esperar, {maximo_intentos} intentos restantes")
                return self.get_elements(xpath=xpath,maximo_intentos=maximo_intentos-1,debug=debug)
            else:
                if debug:
                    print(f"[ERROR] No se encontraron elementos con xpath {xpath}")
                return None
                
    def get_element(self,xpath=None, maximo_intentos=30, debug=False):
        if not xpath or self.driver is None:
            if debug:
                print(f"[ERROR] No existe el driver o el xpath en la funcion get_elements()")
            return None
        try:
            # Utilizando WebDriverWait para esperar hasta que el elemento sea visible
            element = WebDriverWait(self.driver, 1).until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )
            return element
        except:
            if maximo_intentos > 0:
                if debug:
                    print(f"[ERROR] Elemento no encontrado con xpath {xpath} después de esperar, {maximo_intentos} intentos restantes")
                return self.get_element(xpath=xpath,maximo_intentos=maximo_intentos-1,debug=debug)
            else:
                print(f"[ERROR] No se encontró el elemento con xpath {xpath}")
                return None
         
    def get_inside_elements(self,element,xpath,debug=False):
        try:
            if not xpath or not element:
                if debug:
                    print(f"[INFO] No se encontró el elemento ni el xpath para la funcion get_inside_elements()")
                return None
            return element.find_elements(By.XPATH, xpath)
        except Exception as e:
            if debug:
                print(f"[INFO] No se encontró el elemento con xpath {xpath} dentro de el elemento padre: {e}")
            return None         

    def get_inside_element(self,element,xpath,debug=False):
        try:
            if not xpath or not element:
                if debug:
                    print(f"[INFO] No se encontró el elemento ni el xpath para la funcion get_inside_elements()")
                return None
            return element.find_element(By.XPATH, xpath)
        except Exception as e:
            if debug:
                print(f"[INFO] No se encontró el elemento con xpath {xpath} dentro de el elemento padre: {e}")
            return None     
         
         
    def click(self,element,debug=False, name=""):
        try:
            if element:
                element.click()
                return True
            else:
                if debug:
                    print(f"[INFO] No existe el elemento {name} para hacer click")          
                return False      
        except Exception as e:
            if debug:
                print(f"[INFO] No se pudo hacer click en el elemento {name} {e}")
            return False
            
    def text(self,element,debug=False,name=""):
        try:
            if element:
                if hasattr(element, 'text'):
                    return element.get_attribute("text")
                elif hasattr(element, 'innerText'):
                    return element.get_attribute("innerText")
                elif hasattr(element, 'textContent'):
                    return element.get_attribute("textContent")
                else:
                    return element.get_attribute("outerHTML")
            else:
                if debug:
                    print(f"[INFO] No existe el elemento {name} para extraer el texto")          
                return "NotFound" 
        except Exception as e:
            if debug:
                print(f"[INFO] No se pudo extraer el texto en el elemento {name} {e}")
            return "NotFound"
              
    #FUNCIONES LOG/DEVTOOLS
    def reset_log(self):
        if self.driver != None:
            self.driver.get_log('performance')           
    def process_log_entry(self,entry):
        nivel = entry['level']
        hora = entry['timestamp']
        mensaje = json.loads(entry['message'])['message']
        metodo = "missing_data"
        id = 0
        url =  "missing_data"
        request_url =  "missing_data"
        tipo = "missing_data"
        body =  [{ 'status': 'missing_data' }]
        if "method" in mensaje:
            metodo = mensaje["method"]
        
        if metodo.startswith("Network."):
            if metodo == "Network.requestWillBeSent":
                if "params" in mensaje:
                    if "documentURL" in mensaje["params"]:
                        url= mensaje["params"]["documentURL"]
                    if "request" in mensaje["params"]:
                        if "url" in mensaje["params"]["request"]:
                            request_url = mensaje["params"]["request"]["url"]
                    if "type" in mensaje["params"]:
                        tipo= mensaje["params"]["type"]
                    if "requestId" in mensaje["params"]:
                        id=mensaje["params"]["requestId"]

            if metodo == "Network.requestWillBeSentExtraInfo":
                if "params" in mensaje:
                    if "requestId" in mensaje["params"]:
                        id=mensaje["params"]["requestId"]
                    if "associatedCookies" in mensaje["params"]:
                        associated_cookies = mensaje["params"].get("associatedCookies", [])
                        if len(associated_cookies) > 0 and "cookie" in associated_cookies[0]:
                            body = []
                            for cookie in associated_cookies:
                                name = "missing_data"
                                if "name" in cookie["cookie"]:
                                    name = cookie["cookie"]["name"]
                                domain = "missing_data"
                                if "domain" in  cookie["cookie"]:
                                    domain = cookie["cookie"]["domain"]
                                value = "missing_data"
                                if "value" in  cookie["cookie"]:
                                    value = cookie["cookie"]["value"]
                                
                                aux_cookie = {
                                    'status': "OK",
                                    'body': "cookie",
                                    'nombre':name,
                                    'domain':domain,
                                    'value':value
                                }
                                body.append(aux_cookie)
                    if "headers" in mensaje["params"]:
                        headers = mensaje["params"]["headers"]
                        if "Connection" in headers:
                            if "Connection" in  headers:
                                tipo = headers["Connection"]
                            if "Host" in headers:
                                request_url = headers["Host"]
                            if "Origin" in headers:
                                url = headers["Origin"]
                        else: 
                            if ":authority" in headers:
                                url = headers[":authority"]
                            if ":path" in headers:
                                request_url =  headers[":path"]
                            if ":method" in headers:
                                tipo = headers[":method"]
                                
            if metodo == "Network.responseReceived":
                if "params" in mensaje:
                    if "requestId" in mensaje["params"]:
                        id=mensaje["params"]["requestId"]
                    if "response" in mensaje["params"]:
                        response = mensaje["params"]["response"]
                        if "mimeType" in response:
                            if "mimeType" in  response:
                                tipo = response["mimeType"]
                            if "remoteIPAddress" in response:
                                request_url = str(response["remoteIPAddress"])
                                if "remotePort" in response:
                                    request_url += ":" + str(response["remotePort"])
                            if "url" in response:
                                url = response["url"]


            if metodo.startswith("Network.responseReceivedExtraInfo"):
                if "params" in mensaje:
                    if "requestId" in mensaje["params"]:
                        id=mensaje["params"]["requestId"]
                    if "cookiePartitionKey" in mensaje["params"]:
                        url=mensaje["params"]["cookiePartitionKey"]
                    if "headers" in mensaje["params"]:
                        headers = mensaje["params"]["headers"]
                        if "content-type"in headers:
                            tipo = headers["content-type"]
                        if "server" in headers:
                            request_url = headers["server"]
                        else:
                            request_url = "localdata"
                        if "set-cookie" in headers:
                            body = [{
                                "status": "OK",
                                "body" : "set-cookie",
                                "value": headers["set-cookie"]
                            }]
                            
            if metodo == "Network.dataReceived" or metodo == "Network.loadingFinished":
                if "params" in mensaje:
                    if "requestId" in mensaje["params"]:
                        id=mensaje["params"]["requestId"]
            
        return {
            lgFilters.LogKeys.NIVEL:nivel,
            lgFilters.LogKeys.HORA:hora,
            lgFilters.LogKeys.METODO:metodo,
            lgFilters.LogKeys.ID:id,
            lgFilters.LogKeys.URL:url,
            lgFilters.LogKeys.REQUEST_URL:request_url,
            lgFilters.LogKeys.TIPO:tipo,
            lgFilters.LogKeys.BODY:body
            #'mensaje':mensaje
        }
    def proccess_body_log_entry(self,id):
        body = [{ 'status': 'missing_data' }]
        try:
            body_aux=self.driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': id})
            if "base64Encoded" in body_aux:
                if body_aux["base64Encoded"] == True:
                    body = [{
                        "status": "OK",
                        "body": base64.b64decode(body_aux["body"]).decode('utf-8')
                    }]
                else:
                    body = [{
                        "status": "OK",
                        "body": body_aux["body"]
                    }]
            else:
                if "body" in body_aux:
                    body = [{
                       "status": "OK",
                        "body": body_aux["body"]
                        }]
                else:
                    body = [{
                        "status": "ERROR",
                        "body": body_aux
                    }]
        except:
            pass
        return body
    #EJEMPLO ARGS, [[LogKeys.URL, LogKeysMatch.CONTAINS, LogKeysSensitive.NO, "valor_a_probar"],[LogKeys.URL, LogKeysMatch.CONTAINS, LogKeysSensitive.NO, "valor_a_probar"]]        
    def get_log(self, ignore_body=True, lgFilterMode=lgFilters.Mode.AND, filters=None):
        if self.driver is not None:
            logs = self.driver.get_log('performance') 
            eventos_filtro = []
                        
            for log in logs:
                event = self.process_log_entry(log)
                if not ignore_body:
                    if event[lgFilters.LogKeys.BODY] ==  [{ 'status': 'missing_data' }]:
                        event[lgFilters.LogKeys.BODY] = self.proccess_body_log_entry(event["id"])
                
                if filters is None:
                    eventos_filtro.append(event)
                    break
                if isinstance(filters, list) and not isinstance(filters[0], list):
                    filters = [filters]
                comprobar = True
                for kwarg in filters:
                    if comprobar:
                        key = kwarg[0]
                        match_type = kwarg[1]
                        sensitive = kwarg[2]
                        value = kwarg[3]
                   
                        event_value = event[key]
                        if event_value is None:
                            if lgFilterMode == lgFilters.Mode.AND:
                                comprobar = False
                                break
                                           
                        elif sensitive == lgFilters.KeysSensitive.NO:
                            event_value = event_value.lower()
                            value = value.lower()
                            
                        match = False
                        if match_type == lgFilters.KeysMatch.EQUAL:
                            match = event_value == value
                        elif match_type == lgFilters.KeysMatch.START:
                            match = event_value.startswith(value)
                        else:
                            match = value in event_value
                                
                        if match:
                            if lgFilterMode == lgFilters.Mode.AND:
                                continue
                            else:
                                eventos_filtro.append(event) 
                                break                           
                        else:
                            if lgFilterMode == lgFilters.Mode.AND:
                                comprobar = False
                                break
                
                if comprobar and lgFilters.Mode.AND == lgFilterMode:
                    eventos_filtro.append(event)
                    
            return eventos_filtro