import ssl
import time
import json
import socket
import paho.mqtt.client as mqtt

BROKER = "127.0.0.1"         # Adresse IP du broker
PORT = 8883                     # Port MQTT sécurisé
CLIENT_ID = "raspi01"           # Modifier pour chaque Raspberry

TOPIC_COMSO = f"ems/{CLIENT_ID}/comso"
TOPIC_PROD = f"ems/{CLIENT_ID}/prod"

CA_CERT = "./certs/ca.crt"
CLIENT_CERT = "./certs/ca.crt"
CLIENT_KEY = "./certs/ca.key"


# --- Données simulées (à remplacer par tes capteurs)
def collect_data_comso():
    return {
        "raspi_id": CLIENT_ID,
        "hostname": socket.gethostname(),
        "comso": 150,
        "timestamp": int(time.time())
    }

# --- Données simulées (à remplacer par tes capteurs)
def collect_data_prod():
    return {
        "raspi_id": CLIENT_ID,
        "hostname": socket.gethostname(),
        "prod": 250,
        "timestamp": int(time.time())
    }


# --- Callback : connexion
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("🟢 Connecté au broker MQTT")
    else:
        print(f"🔴 Échec de connexion : {rc}")


# --- Callback : déconnexion
def on_disconnect(client, userdata, rc):
    print("🔔 Déconnecté du broker, tentative de reconnexion...")


# --- Configuration client MQTT
client = mqtt.Client(client_id=CLIENT_ID, clean_session=True)

client.on_connect = on_connect
client.on_disconnect = on_disconnect

# --- Paramètres TLS
client.tls_set(
    ca_certs=CA_CERT,
    certfile=CLIENT_CERT,
    keyfile=CLIENT_KEY,
    tls_version=ssl.PROTOCOL_TLSv1_2
)
client.tls_insecure_set(False)


# --- Connexion
print("⏳ Connexion au broker...")
client.connect(BROKER, PORT)

client.loop_start()   # Laisse le client MQTT tourner en arrière-plan

print("🚀 EMS local lancé. Envoi de données toutes les 15 minutes...\n")


# --- Boucle principale
while True:
    try:
        data = collect_data_comso()
        payload = json.dumps(data)

        print(f"📤 Envoi : {payload}")
        
        # QoS 1 = livré au moins une fois
        result = client.publish(TOPIC_COMSO, payload, qos=1)

        status = result[0]
        if status == 0:
            print(f"✔ Message envoyé à {TOPIC_COMSO}")
        else:
            print(f"❌ Erreur d’envoi ({status})")

        data = collect_data_prod()
        payload = json.dumps(data)

        print(f"📤 Envoi : {payload}")
        
        # QoS 1 = livré au moins une fois
        result = client.publish(TOPIC_COMSO, payload, qos=1)

        status = result[0]
        if status == 0:
            print(f"✔ Message envoyé à {TOPIC_PROD}")
        else:
            print(f"❌ Erreur d’envoi ({status})")

    except Exception as e:
        print(f"⚠ Erreur générale : {e}")

    # 15 minutes = 900 secondes
    time.sleep(900)