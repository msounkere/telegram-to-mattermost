import os
import configparser
import json
import os
import mattermost
import datetime
from export_telegram import DateTimeEncoder

# Reading Configs
config = configparser.ConfigParser()
config.read("config.ini")

# Setting configuration values
username = config['Mattermost']['username']
password = config['Mattermost']['password']
url_server = config['Mattermost']['url_server']
bearer_token = config['Mattermost']['bearer_token']

media_files = config['Telegram']['media_files']

mm = mattermost.MMApi(url_server)
#mm.login(username, password)

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
    for team in mm.get_teams():
        if team['name'] == team_name and team['delete_at'] == 0:
            return team['id']

def get_mmuser_id(username):
    for user in mm.get_users():
        if user['username'] == username and user['delete_at'] == 0:
            return user['id']

def get_mmchannel_id(team_id,user_id,channel_name):
    for channel in mm.get_channels_for_user(user_id,team_id):
        if channel['name'] == channel_name and channel['delete_at'] == 0 and channel['type'] != 'D':
            return channel['id']

def create_mmuser(email,username,firstname,lastname):

    import requests
    url = url_server + "/v4/users"
    payload = "{\"email\": \"" + email + "\", \"username\": \"" + username + "\", \"first_name\": \"" + firstname + "\", \"last_name\": \"" + lastname + "\", \"password\": \"Default@1545\", \"locale\": \"fr\"}"
    headers = {
    'Authorization': 'Bearer ' + bearer_token,
    'Content-Type': 'application/json'
    }
    requests.request("POST", url, headers=headers, data = payload)

def import_mattermost(channel_name,args):
    mm.login(args.mmusername, args.mmpassword)
    # Check if channel exists
    team_id = get_mmteam_id(args.mmteam)
    user_id = get_mmuser_id(args.mmusername)

    if args.mmchannel == "False":
        channel = False
    else:
        channel_id = get_mmchannel_id(team_id,user_id,args.mmchannel)
        channel = True

    print("------------------------------------------------------------------------------------------------")
    print(">> Import des données du groupe tl " + channel_name + " dans MM " + args.mmchannel)
    print("------------------------------------------------------------------------------------------------\n")

    ## Control de l'existance du groupe de destination/ Creer le groupe si inexistant
    if channel:
        if channel_id == None:
            channel = True
            # Creation du canal
            print(">>>> Creation du channel car inexistant ...")
            data = mm.create_channel(team_id, args.mmchannel, args.mmchannel, purpose="", header="", type="P")
            if data['id'] == "store.sql_channel.save_channel.exists.app_error":
                print(">>>> La création automatique du groupe " + args.mmchannel + " à échouée pour une raison inconnue")
                exit(0)
            else:
                channel_id = get_mmchannel_id(team_id,user_id,args.mmchannel)
                if channel_id == None:
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
                mm.add_user_to_team(team_id, user_id)
                # join User to group
                if channel:
                    print(">>>> Contrôle / Ajout de l'utilisateur " + mmuser['mattermost'] + " au channel : " + args.mmchannel)
                    mm.add_user_to_channel(channel_id, user_id)

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