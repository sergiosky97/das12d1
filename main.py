from etoroWS import etoro_ws
import sys


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