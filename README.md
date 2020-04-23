
# Script pour la migration de Telegram -> Mattermost
## Requirements
1. Votre server mattermost doit être installé et fonctionnel
2. Disposer des API Télegram ( [https://core.telegram.org/api/obtaining_api_id](https://core.telegram.org/api/obtaining_api_id) )
3. Diposer d'une clé Bearer Token mattermost ( [https://docs.mattermost.com/developer/personal-access-tokens.html](https://docs.mattermost.com/developer/personal-access-tokens.html) )
4. Disposer de la version 3.7 de python

## 1 -  Mise en place de l'environnement

```bash
# Dans le cas des env Docker la commande ci-dessous vous permettra de vous connecter à votre docker
shell> docker exec -it -u 2000 mattermost-docker_app_1 /bin/sh

# mise à jour du système
shell> apt update
shell> apt upgrade

# Installation du multiversion de python
shell> update-alternatives --install /usr/bin/python python /usr/bin/python2.7 1
shell> update-alternatives --install /usr/bin/python python /usr/bin/python3.6 2
shell> update-alternatives --install /usr/bin/python python /usr/bin/python3.7 3
shell> apt install python3-pip
shell> pip3 install telethon

# Choix du python par défault
shell> update-alternatives --config python
```

## 2 - Migration des données

- Déploiement du script
```bash
shell> git clone https://git.veone.net/msounkere/telegram-to-mattermost.git
```
- Préparer le fichier de mapping des comptes utilisateurs sous le format ci-dessous (list.json)

```bash
shell>  cd telegram-to-mattermost
shell>  touch list.json
```
- Preparer le contenu comme ci-dessous et l'y ajouter
```json
[
  {
    "firstname": "Firstname E.",
    "lastname": "NAME FAMILY",
    "email": "email@veone.net",
    "telegram": "username",
    "mattermost": "username"
  },
  {
    "firstname": "Firstname E.",
    "lastname": "NAME FAMILY",
    "email": "email@veone.net",
    "telegram": "username",
    "mattermost": "username"
  }
]
```

- Exécution du script

```bash
shell>  cd telegram-to-mattermost
shell> python3 migrate.py --type channel --tlusername msounkere --tlphone +2257777727 --tlchannel https://t.me/joinchat/EchPiUcTSJpNHBiI0KI0A --mmteam veone --mmchannel veone_xy

# Description des paramètres
usage: migrate.py [-h] [--type TYPE] [--tlusername TLUSERNAME]
                  [--tlphone TLPHONE] [--tlchannel TLCHANNEL]
                  [--mmteam MMTEAM] [--mmchannel MMCHANNEL]

--tlusername : compte telegram admin du channel à migrer
--tlphone : Numéro de phone telegram admin du channel à migrer

# NB : s'il s'agit d'un migration d'une conversation faire les actions suivantes :
--type chat
--tlchat username_du_correspondant
```

- Transférer les données dans Mattermost par le méthode BULK JSON
NB : si la commande mattermost n'existe pas, pour terminer executer manuellement la commande ci-dessous
```bash
>>>> shell> /mattermost/bin/mattermost import bulk /home/msounkere/projects/telegram-to-mattermost/media/1192446106/mattermost_data.json --apply
```
Vous retrouverez toutes vos conversations dans Mattermost , Vive l'Opensource !!!

  
## 3 - FIN
