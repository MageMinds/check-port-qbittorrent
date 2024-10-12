Script qui permet de surveiller le port assigné sur un tunnel Wireguard par PIA sur un routeur OPNsense à l'aide du script de FingerlessGlov3s/OPNsensePIAWireguard

Après avoir cloné le ce code compilez l'image docker comme suit:
```bash
docker build -t check-port-qbittorrent .
```

Vous devez accorder le droit de se connecter à qBittorent WebUI en localhost sans mot de passe
![](https://i.imgur.com/S0UanUe.png)

Ensuite vous devez modifier le compose qui démarre votre qbittorrent pour ajouter un nouveau container qui exécutera ce script et pilotera qBittorrent pour ajuster son port
Voici qui suit mon compose. Je n'expose aucun port car le réseau DockerNet est un macvlan qui ne nécessite pas d'Exposer des ports sur l'hôte. D'ailleur cette méthode de faire pour passer qBittorrent par un VPN géré par OPNsense nécessite un VLAN car je ne crois pas qu'il est possible de dynamiquement changer les ports exposés à l'hôte docker sans redémarrer le container au complet.

```yaml
services:
  qbittorrent-dockernet:
    image: lscr.io/linuxserver/qbittorrent:latest
    container_name: qbittorrent-dockernet
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=America/Toronto
      - WEBUI_PORT=8080
    volumes:
      - ./config:/config
      - ./download:/downloads
    networks:
      DockerNet:
        ipv4_address: 10.100.64.21
    restart: unless-stopped

  check-port-qbittorrent:
    image: check-port-qbittorrent
    container_name: check-port-qbittorrent
    environment:
      - ROUTER_IP=10.100.64.1        # Adresse IP de OPNsense
      - WG_INTERFACE=wg5             # Interface wireguard de PIA dans OPNsense
      - CHECK_INTERVAL=5m            # Défaut à 5m
      - QBITTORRENT_WEBUI_PORT=8080  # Défaut à 8080
      - TZ=America/Toronto
    network_mode: service:qbittorrent-dockernet   # Très important cas les appels API sont fait via localhost et sans login ni mot de passe. Il faut donc permettre cela dans qBittorrent
    depends_on:
      - qbittorrent-dockernet
    restart: unless-stopped

networks:
  DockerNet:
    external: true
```
