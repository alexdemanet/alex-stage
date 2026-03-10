import ssl
import time
import json
import paho.mqtt.client as mqtt

BROKER = "127.0.0.1"          # Adresse du broker Mosquitto (ici en local)
PORT = 8883                      # Port TLS
TOPIC = "ems/#"    
SERVER_ID = "EMS_GLOBAL_SERVER"

CA_CERT = "./certs/ca.crt"
SERVER_CERT = "./certs/server.crt"
SERVER_KEY = "./certs/server.key"


# --- Callback : connexion au broker
def on_connect(client, userdata, flags, rc, properties=None):
    # paho mqtt 1.6+ passes an additional 'properties' argument when using MQTT v5
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
def on_disconnect(client, userdata, rc, properties=None):
    # MQTT v5 may supply properties parameter as well
    print("🔔 Déconnecté du broker, tentative de reconnexion...")
    time.sleep(2)
    try:
        client.reconnect()
    except:
        print("⏳ En attente du retour du broker...")


# --- Configuration du client MQTT
cclient = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=SERVER_ID)

cclient.on_connect = on_connect
cclient.on_message = on_message
cclient.on_disconnect = on_disconnect

# --- Configuration TLS
cclient.tls_set(
    ca_certs=CA_CERT,
    certfile=SERVER_CERT,
    keyfile=SERVER_KEY,
    keyfile_password="0idee",
    tls_version=ssl.PROTOCOL_TLSv1_2
)

cclient.tls_insecure_set(False)

print("🔐 Paramètres TLS chargés")

# --- Connexion au broker
print("⏳ Connexion au broker...")
cclient.connect(BROKER, PORT)

# --- Boucle principale
print("🚀 Serveur EMS Global actif. En attente de données...")
cclient.loop_forever()