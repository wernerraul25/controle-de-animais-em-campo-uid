import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

# Desativa avisos chatos do GPIO
GPIO.setwarnings(False)

reader = SimpleMFRC522()

print("Script de Leitura de UID")
print("Aproxime uma tag do leitor...")
print("Pressione CTRL+C para sair.")

try:
    while True:
        # A função read() bloqueia o script até ler
        uid, text = reader.read()
        
        print("\n--- TAG DETECTADA! ---")
        print(f"UID (Número): {uid}")
        print(f"UID (String): '{uid}'")
        print("----------------------")
        print("Aproxime a próxima tag...")
        
        # Espera 2 segundos para evitar ler a mesma tag múltiplas vezes
        time.sleep(2) 

except KeyboardInterrupt:
    print("\nPrograma interrompido.")
finally:
    GPIO.cleanup()