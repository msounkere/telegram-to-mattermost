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
    d = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z")
    # return int(d.strftime("%s")) * 1000 + d.microsecond / 1000
    return int(d.strftime("%s")) * 1000
    
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

def get_mmteam_id(mmteam_name):
    url = url_server + "/v4/teams/name/" + mmteam_name
    payload = {}
    headers = {
    'Authorization': 'Bearer ' + bearer_token,
    }
    resp = requests.request("GET", url, headers=headers, data = payload)
    mmteam = resp.json()
    if resp.status_code == 200:
        return mmteam['id']
    else:
        return False
    

def get_mmuser_id(mmusername):
    url = url_server + "/v4/users/username/" + mmusername
    payload = {}
    headers = {
    'Authorization': 'Bearer ' + bearer_token,
    }
    resp = requests.request("GET", url, headers=headers, data = payload)
    mmuser = resp.json()
    if resp.status_code == 200:
        return mmuser['id']
    else:
        return False

def get_mmchannel_id(mmteam_id,mmchannel_name):
    url = url_server + "/v4/teams/" + mmteam_id + "/channels/name/" + mmchannel_name
    payload = {}
    headers = {
    'Authorization': 'Bearer ' + bearer_token,
    }
    resp = requests.request("GET", url, headers=headers, data = payload)
    mmchannel = resp.json()
    if resp.status_code == 200:
        return mmchannel['id']
    else:
        return False

def create_mmuser(mmemail,mmusername,mmfirstname,mmlastname):
    url = url_server + "/v4/users"
    payload = "{\"email\": \"" + mmemail + "\", \"username\": \"" + mmusername + "\", \"first_name\": \"" + mmfirstname + "\", \"last_name\": \"" + mmlastname + "\", \"password\": \"Default@1545\", \"locale\": \"fr\"}"
    headers = {
    'Authorization': 'Bearer ' + bearer_token,
    'Content-Type': 'application/json'
    }
    resp = requests.request("POST", url, headers=headers, data = payload)
    if resp.status_code == 400:
        return False

def create_mmchannel(mmteam_id,mmchannel_name,mmchannel_display_name,mmtype_channel):
    url = url_server + "/v4/channels"
    payload = "{\"team_id\": \"" + mmteam_id + "\", \"name\": \"" + mmchannel_name + "\",\"display_name\": \"" + mmchannel_display_name + "\",\"type\": \"" + mmtype_channel + "\"}"
    headers = {
    'Authorization': 'Bearer ' + bearer_token,
    'Content-Type': 'application/json'
    }
    resp = requests.request("POST", url, headers=headers, data = payload)
    print(resp)
    if resp.status_code == 400:
        return False

def add_user_to_mmteam(mmteam_id, mmuser_id):
    url = url_server + "/v4/teams/" + mmteam_id + "/members"
    payload = "{\"team_id\": \"" + mmteam_id + "\", \"user_id\": \"" + mmuser_id + "\"}"
    headers = {
    'Authorization': 'Bearer ' + bearer_token,
    'Content-Type': 'application/json'
    }
    resp = requests.request("POST", url, headers=headers, data = payload)
    if resp.status_code == 400:
        return False

def add_user_to_mmchannel(mmchannel_id,mmuser_id):
    url = url_server + "/v4/channels/" + mmchannel_id + "/members"
    payload = "{\"user_id\": \"" + mmuser_id + "\"}"
    headers = {
    'Authorization': 'Bearer ' + bearer_token,
    'Content-Type': 'application/json'
    }
    resp = requests.request("POST", url, headers=headers, data = payload)
    if resp.status_code == 400:
        return False

def import_mattermost(channel_info,args):

    tlchannel_name = channel_info['tlchannel_name']
    tlchannel_id = channel_info['tlchannel_id']

    # Check if channel exists
    mmteam_id = get_mmteam_id(args.mmteam)
    if not mmteam_id:
        print("Error : Team: " + args.mmteam + " Introuvable")
        exit(0)

    if args.mmchannel == "False":
        mmchannel = False
    else:
        mmchannel_id = get_mmchannel_id(mmteam_id,args.mmchannel)
        mmchannel = True

    print("------------------------------------------------------------------------------------------------")
    print(">> Import des données du groupe tl " + tlchannel_name + " dans MM " + args.mmchannel)
    print("------------------------------------------------------------------------------------------------\n")

    ## Control de l'existance du groupe de destination/ Creer le groupe si inexistant
    if mmchannel:
        if not mmchannel_id:
            mmchannel = True
            # Creation du canal
            print(">>>> Creation du channel car inexistant ...")
            state = create_mmchannel(mmteam_id,args.mmchannel,args.mmchannel,"P")
            print(state)
            if not state:
                print(">>>> Error: La création automatique du groupe " + args.mmchannel + " à échouée pour une raison inconnue")
                exit(0)
            else:
                mmchannel_id = get_mmchannel_id(mmteam_id,args.mmchannel)
                if not mmchannel_id:
                    print(">>>> Error: lors de la création du channel : " + args.mmchannel)
                    exit(0)

    ## Traitement des utilisateurs pour importation
    print(">> Migration des Utilisateurs pour importation des données du channel")
    print("------------------------------------------------------------------------------------------------\n")
    srcdir = media_files + "/" + str(tlchannel_id)
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
                mmuser_id = get_mmuser_id(mmuser['mattermost'])
                # join User to Team
                print(">>>> Contrôle / Ajout de l'utilisateur " + mmuser['mattermost'] + " à la TEAM : " + args.mmteam)
                add_user_to_mmteam(mmteam_id, mmuser_id)
                # join User to group
                if mmchannel:
                    print(">>>> Contrôle / Ajout de l'utilisateur " + mmuser['mattermost'] + " au channel : " + args.mmchannel)
                    add_user_to_mmchannel(mmchannel_id, mmuser_id)

    print(">> Done")
    print("------------------------------------------------------------------------------------------------\n\n")

    ## Traitement des conversations pour importation
    print(">> Migration des conversations et  medias vers le channel/chat Mattermost : " + args.mmchannel)
    print("------------------------------------------------------------------------------------------------\n")
    
    with open(srcdir + '/channel_messages.json') as tlmsg_file:
        tlmsgs = json.load(tlmsg_file)
        listmsgs = tlmsgs 

    mmmsg = 0
    mmtotal_messages = len(tlmsgs)
    mmall_posts = []
    for tlmsg in tlmsgs:
        mmpost = ""
        mmmsg += 1
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
                    "create_at": timestamp_from_date(reply_msg['date']),
                    "attachments": reply_attached_files
                })
        
        ## Mattermost final structure for importations

        if tlmsg['reply_to_msg_id'] == None and tlmsg['action'] == False:

            mmpost_user = get_tl_username_from_file(srcdir,tlmsg['from_id'])

            mmpost = {
                "team": args.mmteam,
                "channel": args.mmchannel,
                "user": get_mmuser_from_file(mmpost_user),
                "message": tlmsg['message'],
                "create_at": timestamp_from_date(tlmsg['date']),
                "replies": replies_msg,
                "attachments": attached_files_msg
            }

            mmall_posts.append({
                "type": "post",
                "post": mmpost
            })
        
        print(">>>> Transfer du message : " + str(mmmsg) + "/" + str(mmtotal_messages))

    ## Generation du fichier d'import!
    with open(srcdir + '/mattermost_data.json', 'w') as filehandle:
        filehandle.writelines('{"type":"version","version":1}\n')
        filehandle.writelines("%s\n" % json.dumps(mmpost) for mmpost in mmall_posts)
    
    os.system('sed -i "$ d" {0}'.format(srcdir + '/mattermost_data.json'))

    print("\n------------------------------------------------------------------------------------------------")
    print(">> Fin de la migration")
    print("------------------------------------------------------------------------------------------------\n")


    # print(mm.get_channels_for_user(user_id,team_id))