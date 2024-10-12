import os
import time
import logging
import requests
import urllib3

# Désactiver uniquement les avertissements de vérification SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =========================
# Configuration du logging
# =========================

logging.basicConfig(
    level=logging.INFO,  # Permet de gérer différents niveaux : DEBUG, INFO, WARNING, ERROR, etc.
    format='%(asctime)s - %(levelname)s - %(message)s',  # Format des messages (avec timestamp)
    datefmt='%Y-%m-%d %H:%M:%S',
)

# Charger les variables d'environnement
router_ip = os.getenv('ROUTER_IP')
wg_interface = os.getenv('WG_INTERFACE')
check_interval = os.getenv('CHECK_INTERVAL', '5m')

# Charger le port WebUI (par défaut 8080)
qbittorrent_webui_port = os.getenv('QBITTORRENT_WEBUI_PORT', '8080')

# Convertir l'intervalle de temps en secondes
def get_seconds_from_intervals(interval_str):
    if interval_str.endswith('m'):
        return int(interval_str[:-1]) * 60
    elif interval_str.endswith('h'):
        return int(interval_str[:-1]) * 60 * 60
    else:
        return 60  # Par défaut, 1 minute

check_interval_in_seconds = get_seconds_from_intervals(check_interval)

# Fonction pour récupérer les préférences actuelles de qBittorrent, dont le listen_port
def get_qbittorrent_current_port():
    try:
        preferences_url = f"http://localhost:{qbittorrent_webui_port}/api/v2/app/preferences"
        response = requests.get(preferences_url)

        if response.status_code == 200:
            preferences = response.json()
            listen_port = preferences.get('listen_port', None)
            logging.info(f"Port actuel de qBittorrent : {listen_port}")
            return listen_port
        else:
            logging.error(f"Erreur lors de la récupération des préférences - Code réponse: {response.status_code}")
            return None

    except Exception as e:
        logging.error(f"Erreur lors de la récupération des préférences : {e}")
        return None

# Fonction pour obtenir le SID depuis l'API de qBittorrent (session de login)
def get_sid():
    try:
        login_url = f"http://localhost:{qbittorrent_webui_port}/api/v2/auth/login"
        headers = {'Referer': f'http://localhost:{qbittorrent_webui_port}'}
        response = requests.post(login_url, data='', headers=headers)

        if 'SID' in response.cookies:
            return response.cookies['SID']
        else:
            logging.error(f"Erreur : SID introuvable dans la réponse")
            return None

    except Exception as e:
        logging.error(f"Erreur lors de la récupération du SID : {e}")
        return None

# Fonction pour modifier le port dans qBittorrent via l'API avec le SID
def update_qbittorrent_port(new_port, sid):
    try:
        api_url = f"http://localhost:{qbittorrent_webui_port}/api/v2/app/setPreferences"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        cookies = {'SID': sid}

        preferences = f'json=%7B%22listen_port%22%3A{new_port}%7D'

        response = requests.post(api_url, data=preferences, headers=headers, cookies=cookies)

        if response.status_code == 200:
            logging.info(f"Port de qBittorrent mis à jour avec succès à {new_port}")
        else:
            logging.error(f"Erreur lors de la mise à jour du port de qBittorrent. Code réponse: {response.status_code}")

    except Exception as e:
        logging.error(f"Erreur lors de la mise à jour du port de qBittorrent : {e}")

# Fonction pour récupérer le port du routeur
def get_port_from_router():
    try:
        url = f"https://{router_ip}/{wg_interface}_port.txt"
        response = requests.get(url, verify=False)  # Désactivation de la vérification SSL
        if response.status_code == 200:
            port = response.text.strip()
            return int(port)
        else:
            logging.error(f"Erreur: Impossible de récupérer le port. Code réponse: {response.status_code}")
    except Exception as e:
        logging.error(f"Erreur lors de la récupération du port : {e}")
    return None

# Programme principal
if __name__ == "__main__":
    logging.info("Démarrage du script de vérification de port")

    while True:
        # Récupérer le port configuré dans qBittorrent
        current_qbittorrent_port = get_qbittorrent_current_port()

        if current_qbittorrent_port is not None:
            # Récupérer le port du routeur
            new_port = get_port_from_router()

            if new_port and new_port != current_qbittorrent_port:
                logging.info(f"Le port a changé, mise à jour nécessaire : {current_qbittorrent_port} -> {new_port}")

                # Récupérer le SID pour authentification
                sid = get_sid()

                if sid:
                    # Mettre à jour le port de qBittorrent
                    update_qbittorrent_port(new_port, sid)
            else:
                logging.info(f"Le port n'a pas changé, aucune mise à jour nécessaire (actuel: {current_qbittorrent_port}, nouveau: {new_port})")

        # Temporisation avant la prochaine vérification
        logging.info(f"Attente de {check_interval_in_seconds} secondes avant la prochaine vérification")
        time.sleep(check_interval_in_seconds)
