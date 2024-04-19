from etoroWS import etoro_ws
import sys

import os
import json

def cambiar_update():
    ruta = "data/ia_info"
    ruta_carpeta = ruta
    lista_carpetas = [elemento for elemento in os.listdir(ruta_carpeta) if os.path.isdir(os.path.join(ruta_carpeta, elemento))]
    for carpeta in lista_carpetas:
        ruta_mercado = os.path.join(ruta,carpeta)
        lista_mercados = [elemento for elemento in os.listdir(ruta_mercado) if os.path.isdir(os.path.join(ruta_mercado, elemento))]
        for mercado in lista_mercados:
            #ruta_elementos = os.path.join(ruta,carpeta,mercado)
            #lista_elementos = [elemento for elemento in os.listdir(ruta_elementos) if os.path.isdir(os.path.join(ruta_elementos, elemento))]
            #for elemento in lista_elementos:
            ruta_json = os.path.join(ruta,carpeta,mercado,"update_etoro.json")
            if os.path.exists(ruta_json):
                with open(ruta_json, "r") as archivo_json:
                    datos_json = json.load(archivo_json)
                    ultima_actualizacion = datos_json.get("ultima_actualizacion", None)
                    links_analizados = datos_json.get("links_analizados", [])
                    links_analizados_dos = [link for link in links_analizados if link not in ["FIN", "ERROR"]]
                    new_data = {
                        "ultima_actualizacion":ultima_actualizacion,
                        "links_analizados":links_analizados_dos
                    }
                    with open(ruta_json, "w") as archivo_json:
                        json.dump(new_data,archivo_json, indent=4)
            else:
                print(f"El archivo update_etoro.json no existe en {ruta_json}")

def esperar_presionar_x():
    while True:
        entrada = input("[USER] Presione 'x' para salir: ")
        if entrada.lower() == 'x':
            break

try:
    etoro = etoro_ws()
    esperar_presionar_x()
except Exception as e:
    print(f"[ERROR]: {e}")

print("[INFO] Saliendo del programa...")