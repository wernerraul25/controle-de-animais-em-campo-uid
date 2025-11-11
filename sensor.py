from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
import time
import requests

# --- Configurações ---
FLASK_SERVER_IP = "127.0.0.1" 
FLASK_URL = f"http://{FLASK_SERVER_IP}:5000/api/scan"

# Tempo de espera (em segundos) antes de registrar a MESMA tag novamente
SCAN_COOLDOWN_SEC = 10

# --- Configurações de Hardware (LEDs e Grupos) ---
PIN_LED_A = 22 # GPIO para o LED A (Bezerros)
PIN_LED_B = 23 # GPIO para o LED B (Vacas)

GROUP_A_UIDS = ['219085403461'] # Bezerros
GROUP_B_UIDS = ['703695879170'] # Vacas

# --- Setup ---
GPIO.setmode(GPIO.BCM)
reader = SimpleMFRC522() 
GPIO.setup([PIN_LED_A, PIN_LED_B], GPIO.OUT) 
GPIO.output([PIN_LED_A, PIN_LED_B], GPIO.LOW)
print(f"Leitor RFID iniciado. Cooldown por tag: {SCAN_COOLDOWN_SEC} segundos.")

# Dicionário para armazenar o último scan de CADA tag
# Formato: { 'UID_DA_TAG_1': 1234567.89, 'UID_DA_TAG_2': 1234569.00 }
last_scan_times = {}

def enviar_scan_api(uid_str):
    """Envia o UID da tag para o servidor Flask."""
    try:
        payload = {"uid": uid_str}
        requests.post(FLASK_URL, json=payload, timeout=3)
        print(f"EVENTO: Tag {uid_str} detectada. API notificada.")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao conectar com a API: {e}")

# --- Loop Principal (Lógica de Cooldown Corrigida) ---
try:
    while True:
        uid = reader.read_id_no_block()
        uid_str = str(uid) if uid else None
        
        # 1. Lógica de LED (Sempre acende em tempo real)
        if uid_str in GROUP_A_UIDS:
            GPIO.output(PIN_LED_A, GPIO.HIGH)
            GPIO.output(PIN_LED_B, GPIO.LOW)
        elif uid_str in GROUP_B_UIDS:
            GPIO.output(PIN_LED_A, GPIO.LOW)
            GPIO.output(PIN_LED_B, GPIO.HIGH)
        else:
            # Apaga ambos os LEDs se a tag for desconhecida ou não houver tag
            GPIO.output(PIN_LED_A, GPIO.LOW)
            GPIO.output(PIN_LED_B, GPIO.LOW)
        
        # 2. Lógica de Log (Usa o Cooldown por tag)
        if uid:
            current_time = time.time()
            
            # Pega o último horário que esta tag específica foi lida
            # Se for a primeira vez, 'last_seen' será 0
            last_seen = last_scan_times.get(uid_str, 0)
            
            # Já passou o tempo de cooldown para ESTA tag?
            if (current_time - last_seen) > SCAN_COOLDOWN_SEC:
                # Sim. Envia o scan para a API.
                enviar_scan_api(uid_str)
                
                # Atualiza o horário de scan SOMENTE desta tag
                last_scan_times[uid_str] = current_time
                pass

        time.sleep(0.2) # Pausa do loop

except KeyboardInterrupt:
    print("\nPrograma finalizado.")
finally:
    GPIO.cleanup()