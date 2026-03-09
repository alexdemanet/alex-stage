import ssl
import time
import json
import paho.mqtt.client as mqtt

BROKER = "192.168.2.20"          # Adresse du broker Mosquitto
PORT = 8883                      # Port TLS
TOPIC = "ems/#"    
CLIENT_ID = "EMS_GLOBAL_SERVER"

CA_CERT = "/certs/ca.crt"
CLIENT_CERT = "/certs/server.crt"
CLIENT_KEY = "/certs/server.key"


# --- Callback : connexion au broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("🟢 Connecté au broker MQTT")
        client.subscribe(TOPIC)
        print(f"📡 Abonnement au topic : {TOPIC}")
    else:
        print(f"🔴 Erreur de connexion : {rc}")


# --- Callback : message reçu
def on_message(client, userdata, msg):
    print(f"\n📥 Message reçu sur {msg.topic}")
    payload = msg.payload.decode()

    try:
        data = json.loads(payload)
    except:
        data = payload

    print("Données : ", data)

    # --- EXEMPLE : Sauvegarde dans fichier
    with open("ems_data.log", "a") as f:
        f.write(f"{time.time()} | {msg.topic} | {data}\n")


# --- Callback : déconnexion
def on_disconnect(client, userdata, rc):
    print("🔔 Déconnecté du broker, tentative de reconnexion...")
    time.sleep(2)
    try:
        client.reconnect()
    except:
        print("⏳ En attente du retour du broker...")


# --- Configuration du client MQTT
client = mqtt.Client(client_id=CLIENT_ID)

client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

# --- Configuration TLS
client.tls_set(
    ca_certs=CA_CERT,
    certfile=CLIENT_CERT,
    keyfile=CLIENT_KEY,
    tls_version=ssl.PROTOCOL_TLSv1_2
)

client.tls_insecure_set(False)

print("🔐 Paramètres TLS chargés")

# --- Connexion au broker
print("⏳ Connexion au broker...")
client.connect(BROKER, PORT)

# --- Boucle principale
print("🚀 Serveur EMS Global actif. En attente de données...")
client.loop_forever()