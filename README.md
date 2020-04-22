
# Script pour la migration de Telegram -> Mattermost
## 1 - Installation des dépendances
Requirements
 1. Votre server mattermost doit être installé et fonctionnel  
 2. Disposer des API Télegram ( [https://core.telegram.org/api/obtaining_api_id](https://core.telegram.org/api/obtaining_api_id) )
 3. Diposer  d'une clé Bearer Token mattermost ( [https://docs.mattermost.com/developer/personal-access-tokens.html](https://docs.mattermost.com/developer/personal-access-tokens.html) )
 4. Disposer de la version 3.7 de python

- Mise en place de l'environnement
```bash
# mise à jour du système
shell> sudo apt update
shell> sudo apt upgrade

# Installation du multiversion de python
shell> sudo update-alternatives --install /usr/bin/python python /usr/bin/python2.7 1
shell> sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.6 2
shell> sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.7 3
shell> sudo apt install python3-pip
shell> sudo pip3 install telethon

# Choix du python par défault
shell> sudo update-alternatives --config python
```
## 2 - Migration des données
- Déploiement du script
```bash
shell> git clone https://git.veone.net/msounkere/telegram-to-mattermost.git
```
- Exécution du script
```bash
shell> cd telegram-to-mattermost
shell> python3 migrate.py --tlusername msounkere --tlphone +2257777727 --tlchannel https://t.me/joinchat/EchPiUcTSJpNHBiI0KI0A --mmteam veone --mmchannel veone_xy
# Description des paramètres
usage: migrate.py [-h] [--tlusername TLUSERNAME] [--tlphone TLPHONE]
                  [--tlchannel TLCHANNEL] [--mmteam MMTEAM]
                  [--mmchannel MMCHANNEL]
                  
--tlusername : compte telegram admin du channel à migrer
--tlphone : Numéro de phone telegram admin du channel à migrer

# NB : s'il s'agit d'un migration d'une conversation faire les actions suivantes :

--tlchannel username_du_correspondant
--mmchannel False
  
```
- Transférer les données dans Mattermost par le méthode BULK JSON
```bash
shell> /mattermost/bin/mattermost import bulk /opt/telegram-to-mattermost/media/1192446106/mattermost_data.json --appl
```
Vous retrouverez toutes vos conversations dans Mattermost
Vive l'Opensource !!!

## 3 - FIN
