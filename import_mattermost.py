import os
import configparser
import json
import os
import datetime
import requests
from export_telegram import DateTimeEncoder

# Reading Configs
config = configparser.ConfigParser()
config.read("config.ini")

# Setting configuration values
url_server = config['Mattermost']['url_server']
bearer_token = config['Mattermost']['bearer_token']

media_files = config['Telegram']['media_files']

def timestamp_from_date(date):
    d = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ %f")
    return int(d.strftime("%s")) * 1000 + d.microsecond / 1000
    
def get_attachments(pathdir):
    attachements = []
    dirs = os.listdir(pathdir)
    for attachement in dirs:
        attachements.append({
            "path": pathdir + '/' + attachement,
        })
    return attachements

def get_mmuser_from_file(tl_user):
    with open("list.json") as tlusers_file:
        tlusers = json.load(tlusers_file)
        for tluser in tlusers:
            if tluser['telegram'] == tl_user:
                return tluser['mattermost']

def get_tl_username_from_file(dir_users,id):
    with open(dir_users + '/user_data.json') as tlusers_file:
        tlusers = json.load(tlusers_file)
        for tluser in tlusers:
            if tluser['id'] == id:
                return tluser['user']

def get_mmteam_id(team_name):
    url = url_server + "/v4/teams/name/" + team_name
    payload = {}
    headers = {
    'Authorization': 'Bearer ' + bearer_token,
    }
    resp = requests.request("GET", url, headers=headers, data = payload)
    team = resp.json()
    if resp.status_code == 200:
        return team['id']
    else:
        return False
    

def get_mmuser_id(username):
    url = url_server + "/v4/users/username/" + username
    payload = {}
    headers = {
    'Authorization': 'Bearer ' + bearer_token,
    }
    resp = requests.request("GET", url, headers=headers, data = payload)
    user = resp.json()
    if resp.status_code == 200:
        return user['id']
    else:
        return False

def get_mmchannel_id(team_id,channel_name):
    url = url_server + "/v4/teams/" + team_id + "/channels/name/" + channel_name
    payload = {}
    headers = {
    'Authorization': 'Bearer ' + bearer_token,
    }
    resp = requests.request("GET", url, headers=headers, data = payload)
    channel = resp.json()
    if resp.status_code == 200:
        return channel['id']
    else:
        return False

def create_mmuser(email,username,firstname,lastname):
    url = url_server + "/v4/users"
    payload = "{\"email\": \"" + email + "\", \"username\": \"" + username + "\", \"first_name\": \"" + firstname + "\", \"last_name\": \"" + lastname + "\", \"password\": \"Default@1545\", \"locale\": \"fr\"}"
    headers = {
    'Authorization': 'Bearer ' + bearer_token,
    'Content-Type': 'application/json'
    }
    resp = requests.request("POST", url, headers=headers, data = payload)
    if resp.status_code == 400:
        return False

def create_mmchannel(team_id,channel_name,channel_display_name,type_channel):
    url = url_server + "/v4/channels"
    payload = "{\"team_id\": \"" + team_id + "\", \"name\": \"" + channel_name + "\",\"display_name\": \"" + channel_display_name + "\",\"type\": \"" + type_channel + "\"}"
    headers = {
    'Authorization': 'Bearer ' + bearer_token,
    'Content-Type': 'application/json'
    }
    resp = requests.request("POST", url, headers=headers, data = payload)
    if resp.status_code == 400:
        return False

def add_user_to_mmteam(team_id, user_id):
    url = url_server + "/v4/teams/" + team_id + "/members"
    payload = "{\"team_id\": \"" + team_id + "\", \"user_id\": \"" + user_id + "\"}"
    headers = {
    'Authorization': 'Bearer ' + bearer_token,
    'Content-Type': 'application/json'
    }
    resp = requests.request("POST", url, headers=headers, data = payload)
    if resp.status_code == 400:
        return False

def add_user_to_mmchannel(channel_id,user_id):
    url = url_server + "/v4/channels/" + channel_id + "/members"
    payload = "{\"user_id\": \"" + user_id + "\"}"
    headers = {
    'Authorization': 'Bearer ' + bearer_token,
    'Content-Type': 'application/json'
    }
    resp = requests.request("POST", url, headers=headers, data = payload)
    if resp.status_code == 400:
        return False

def import_mattermost(channel_name,args):

    # Check if channel exists
    team_id = get_mmteam_id(args.mmteam)
    if not team_id:
        print("Error : Team: " + args.mmteam + " Introuvable")
        exit(0)

    if args.mmchannel == "False":
        channel = False
    else:
        channel_id = get_mmchannel_id(team_id,args.mmchannel)
        channel = True

    print("------------------------------------------------------------------------------------------------")
    print(">> Import des données du groupe tl " + channel_name + " dans MM " + args.mmchannel)
    print("------------------------------------------------------------------------------------------------\n")

    ## Control de l'existance du groupe de destination/ Creer le groupe si inexistant
    if channel:
        if not channel_id:
            channel = True
            # Creation du canal
            print(">>>> Creation du channel car inexistant ...")
            state = create_mmchannel(team_id,args.mmchannel,args.mmchannel,"P")
            if not state:
                print(">>>> La création automatique du groupe " + args.mmchannel + " à échouée pour une raison inconnue")
                exit(0)
            else:
                channel_id = get_mmchannel_id(team_id,args.mmchannel)
                if not channel_id:
                    print(">>>> Echec lors de la création du channel : " + args.mmchannel)
                    exit(0)

    ## Traitement des utilisateurs pour importation
    print(">> Migration des Utilisateurs pour importation des données du channel")
    print("------------------------------------------------------------------------------------------------\n")
    srcdir = media_files + "/" + channel_name
    with open(srcdir + '/user_data.json') as tlusers_file:
        tlusers = json.load(tlusers_file)


    with open("list.json") as mmusers_file:
        mmusers = json.load(mmusers_file)

    for mmuser in mmusers:
        for tluser in tlusers:
            if mmuser['telegram'] == tluser['user']:
                # Create required users
                print(">>>> Verification ou création du compte : " + mmuser['email'])
                create_mmuser(mmuser['email'],mmuser['mattermost'],mmuser['firstname'],mmuser['lastname'])
                # get userid
                user_id = get_mmuser_id(mmuser['mattermost'])
                # join User to Team
                print(">>>> Contrôle / Ajout de l'utilisateur " + mmuser['mattermost'] + " à la TEAM : " + args.mmteam)
                add_user_to_mmteam(team_id, user_id)
                # join User to group
                if channel:
                    print(">>>> Contrôle / Ajout de l'utilisateur " + mmuser['mattermost'] + " au channel : " + args.mmchannel)
                    add_user_to_mmchannel(channel_id, user_id)

    print(">> Done")
    print("------------------------------------------------------------------------------------------------\n\n")

    ## Traitement des conversations pour importation
    print(">> Migration des conversations et  medias vers le channel/chat Mattermost : " + args.mmchannel)
    print("------------------------------------------------------------------------------------------------\n")
    
    with open(srcdir + '/channel_messages.json') as tlmsg_file:
        tlmsgs = json.load(tlmsg_file)
        listmsgs = tlmsgs 

    msg = 0
    total_messages = len(tlmsgs)
    all_posts = []
    for tlmsg in tlmsgs:
        post = ""
        msg += 1
    # Generation du fichier JSON d'import des données

        ## recuperation des medias du message
        attached_files_msg = []

        if tlmsg['media'] == True:
            pathdir = srcdir + '/' + str(tlmsg['id'])
            attached_files_msg = get_attachments(pathdir)


        ## recuperation des reponses en liaison avec le message
        replies_msg = []

        for reply_msg in listmsgs:
            if reply_msg['reply_to_msg_id'] == tlmsg['id']:

                reply_attached_files = []

                if reply_msg['media'] == True:
                    reply_pathdir = srcdir + '/' + str(reply_msg['id'])
                    reply_attached_files = get_attachments(reply_pathdir)

                tl_user = get_tl_username_from_file(srcdir,reply_msg['from_id'])

                replies_msg.append({
                    "user": get_mmuser_from_file(tl_user),
                    "message": reply_msg['message'],
                    "create_at": 140012352049,
                    "attachments": reply_attached_files
                })
        
        ## Mattermost final structure for importations

        if tlmsg['reply_to_msg_id'] == None and tlmsg['action'] == False:

            post_user = get_tl_username_from_file(srcdir,tlmsg['from_id'])

            post = {
                "team": args.mmteam,
                "channel": args.mmchannel,
                "user": get_mmuser_from_file(post_user),
                "message": tlmsg['message'],
                "create_at": 140012340013,
                "replies": replies_msg,
                "attachments": attached_files_msg
            }

            all_posts.append({
                "type": "post",
                "post": post
            })
            
        # "id": tlmsg['id'],
        # "date": tlmsg['date'],
        # "message": tlmsg['message'],
        # "from_id": tlmsg['from_id'],
        # "fwd_from": tlmsg['fwd_from'],
        # "reply_to_msg_id": tlmsg['reply_to_msg_id'],
        # "media": tlmsg['media']
        # create_post(channel_id, message, props={"from_webhook":"true"}, filepaths=[], root_id=None,
        
        print(">>>> Transfer du message : " + str(msg) + "/" + str(total_messages))

    ## Generation du fichier d'import!
    # with open(srcdir + '/mattermost_data.json', 'w') as outfile:
    #     print(all_posts)

    with open(srcdir + '/mattermost_data.json', 'w') as filehandle:
        filehandle.writelines('{"type":"version","version":1}\n')
        filehandle.writelines("%s\n" % json.dumps(post) for post in all_posts)

    print("\n------------------------------------------------------------------------------------------------")
    print(">> Fin de la migration")
    print("------------------------------------------------------------------------------------------------\n")



    # print(mm.get_channels_for_user(user_id,team_id))