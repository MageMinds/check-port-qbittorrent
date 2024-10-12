# Dockerfile pour le container de vérification de port

FROM python:3.9-slim

# Installer les dépendances
RUN pip install requests

# Copier le script Python et le rendre exécutable
COPY check_port_qbittorrent.py /usr/local/bin/check_port_qbittorrent.py
RUN chmod +x /usr/local/bin/check_port_qbittorrent.py

CMD ["python", "/usr/local/bin/check_port_qbittorrent.py"]
