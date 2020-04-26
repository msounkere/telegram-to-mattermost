import configparser
import json
import os
import shutil
import requests
import subprocess

from datetime import date, datetime
from telethon import TelegramClient , events, sync
from telethon.errors import SessionPasswordNeededError
from telethon import utils
from telethon.tl.types import (
    PeerUser
)

# Reading Configs
config = configparser.ConfigParser()
config.read("config.ini")

currentdir = os.getcwd()
current_list_dir = currentdir + "/list.json"

# Setting configuration values
tlapi_id = config['Telegram']['api_id']
tlapi_hash = config['Telegram']['api_hash']
tlapi_hash = str(tlapi_hash)
media_files = currentdir + "/" + config['Telegram']['media_files']
limit = config['Telegram']['limit']
tltotal_count_limit = config['Telegram']['total_count_limit']

# Setting configuration values
url_server = config['Mattermost']['url_server']
bearer_token = config['Mattermost']['bearer_token']
mattermost_cli = config['Mattermost']['mattermost_cli']

class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):   # pylint: disable=E0202
        if isinstance(o, datetime):
            return o.isoformat()

        if isinstance(o, bytes):
            return list(o)

        return json.JSONEncoder.default(self, o)
        
def init_dir(destdir,args):
    if args.force:
        for root, dirs, files in os.walk(destdir):
            for f in files:
                os.unlink(os.path.join(root, f))
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))

    if not os.path.exists(destdir):
        os.makedirs(destdir)

def init_tl_user(args):
    tlphone = args.tlphone
    tlusername = args.tlusername

    # Create the client and connect
    client = TelegramClient(tlusername, tlapi_id, tlapi_hash)
    if client.start(phone=tlphone):
        client.takeout()
        print("\n>> Authentification reussie pour le user : " + tlusername)
        print("------------------------------------------------------------------------------------------------\n")
    else:
        print("\n>> Echec de l'authentification pour le user : " + tlusername)
        print("------------------------------------------------------------------------------------------------\n")

    # Ensure you're authorized
    if not client.is_user_authorized():
        client.send_code_request(tlphone)
        try:
            client.sign_in(tlphone, input('Enter the code: '))
        except SessionPasswordNeededError:
            client.sign_in(password=input('Password: '))

    return client

def callback(current, total):
    print('>>>>>>>> Downloaded', current, 'out of', total,
          'bytes: {:.2%}'.format(current / total))

def load_tl_users(dir_users):
    current_channel_dir = dir_users + "/user_data.json"
    if os.path.isfile(current_channel_dir):
        with open(current_channel_dir) as tlusers_file:
            tlusers = json.load(tlusers_file)
    
        return tlusers
    else:
        print(">> Error : Fichier user_data.json introuvable !")
        exit(0)

def load_mm_users():
    if os.path.isfile(current_list_dir):
        with open(current_list_dir) as mmusers_file:
            mmusers = json.load(mmusers_file)
    
        return mmusers
    else:
        print(">> Error : Fichier list.json introuvable !")
        exit(0)
    
def run_mmbulk_commands(srcdir):

    ## Get mmchannel list json file
    current_channel_dir = srcdir   
    if os.path.isdir(current_channel_dir):
        current_channel_jsonfile = current_channel_dir + "/mattermost_data.json"
        if os.path.isfile(current_channel_jsonfile):
            
            print(">> Lancement de l'importation des données dans Mattermost")
            print("------------------------------------------------------------------------------------------------")

            status, result = subprocess.getstatusoutput("mattermost version")
            if status == False:
                cmd = "mattermost import bulk "
                result = subprocess.getstatusoutput(cmd + current_channel_jsonfile + " --apply")
                print(result)
            else:
                cmd = "%s import bulk --worker 4 " % mattermost_cli 
                print(">>>> Pour terminer executer manuellement la commande ci-dessous")
                print(">>>> shell> " + cmd + current_channel_jsonfile + " --apply")
        else:
            print(">>>> FIchier mattermost_data.json introuvable !")

def timestamp_from_date(date):
    d = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z")
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

def dump_tlusers(destdir,data):
    with open(destdir + '/user_data.json', 'w') as outfile:
        json.dump(data, outfile)

def add_tlinactive_user(dir_users,tluser):
    tlusers = load_tl_users(dir_users)
    # Track username : Null
    if tluser.username == None:
        tlusers.append({
            "id": tluser.id,
            "first_name": "John",
            "last_name": "DOE",
            "user": "jdoe",
            "phone": "",
            "is_bot": tluser.bot,
            "status": "inactive"
        })
    else:
        tlusers.append({
            "id": tluser.id,
            "first_name": tluser.first_name,
            "last_name": tluser.last_name,
            "user": tluser.username,
            "phone": tluser.phone,
            "is_bot": tluser.bot,
            "status": "inactive"
        })

    dump_tlusers(dir_users,tlusers)

def get_mmuser_from_file(tl_user):
    
    if os.path.isfile(current_list_dir):
        with open(current_list_dir) as tlusers_file:
            tlusers = json.load(tlusers_file)
            for tluser in tlusers:
                if tluser['telegram'] == tl_user:
                    return tluser['mattermost']
    else:
        print(">> Error : Fichier list.json introuvable !")
        exit(0)

def get_tl_username_from_file(dir_users,id):
   
    tlusers = load_tl_users(dir_users)
    for tluser in tlusers:
        if tluser['id'] == id:
            return tluser['user']

def get_tl_id_from_file(dir_users,id):
   
    tlusers = load_tl_users(dir_users)
    for tluser in tlusers:
        if tluser['id'] == id:
            return tluser['id']

def check_match_users(dir_users):

    tlusers = load_tl_users(dir_users)
    mmusers = load_mm_users()
    mmusername_list = []
    tlusername_notfound = []
    tlusername_null =[]

    for mmuser in mmusers:
        mmusername_list.append(mmuser['telegram'])

    for tluser in tlusers:
        if tluser['user'] != None:
            if tluser['user'] not in mmusername_list and tluser['user'] not in tlusername_notfound:
                tlusername_notfound.append(tluser['user'])
        else:
            tlusername_null.append(tluser['first_name'] + "" + tluser['last_name'])
            
    if len(tlusername_null) > 0:
        print(">>>> Error: Les utilisateurs suivants ont des usernames non définis dans Télégram %s" %tlusername_null)
        exit(0)
   
    if len(tlusername_notfound) > 0:
        print(">>>> Error: Les utilisateurs suivants sont introuvables dans le fichier list.json %s" %tlusername_notfound)
        exit(0)


def get_mmteam_id(mmteam_name):
    url =  "%s/v4/teams/name/%s" %(url_server,mmteam_name)
    payload = {}
    headers = {
        'Authorization': 'Bearer %s' %bearer_token,
    }
    resp = requests.request("GET", url, headers=headers, data = payload)
    mmteam = resp.json()
    
    if resp.status_code == 200:
        return mmteam['id']
    else:
        return False
    

def get_mmuser_id(mmusername):
    url = "%s/v4/users/username/%s" %(url_server,mmusername)
    payload = {}
    headers = {
        'Authorization': 'Bearer %s' %bearer_token,
    }
    resp = requests.request("GET", url, headers=headers, data = payload)
    mmuser = resp.json()
    
    if resp.status_code == 200:
        return mmuser['id']
    else:
        return False

def get_mmchannel_id(mmteam_id,mmchannel_name):
    url = "%s/v4/teams/%s/channels/name/%s" %(url_server,mmteam_id,mmchannel_name)
    payload = {}
    headers = {
        'Authorization': 'Bearer %s' %bearer_token,
    }
    resp = requests.request("GET", url, headers=headers, data = payload)
    mmchannel = resp.json()
    
    if resp.status_code == 200:
        return mmchannel['id']
    else:
        return False

def create_mmuser(mmemail,mmusername,mmfirstname,mmlastname):
    url =  "%s/v4/users" %url_server
    payload = {
        'email': '%s' %mmemail,
        'username' : '%s' %mmusername,
        'first_name' : '%s' %mmfirstname,
        'last_name' : '%s' %mmlastname,
        'password' : 'Default@1545',
        'locale' : 'fr'
    }
    payload = json.dumps(payload)
    
    headers = {
        'Authorization': 'Bearer %s' %bearer_token,
        'Content-Type': 'application/json'
    }
    resp = requests.request("POST", url, headers=headers, data = payload)

    if resp.status_code == 400:
        return False
    return True

def create_mmchannel(mmteam_id,mmchannel_name,mmchannel_display_name,mmtype_channel):
    url = "%s/v4/channels" %url_server
    payload = {
        'team_id': '%s' %mmteam_id,
        'name' : '%s' %mmchannel_name,
        'display_name' : '%s' %mmchannel_display_name,
        'type' : '%s' %mmtype_channel
    }
    payload = json.dumps(payload)

    headers = {
        'Authorization': 'Bearer %s' %bearer_token,
        'Content-Type': 'application/json'
    }
    resp = requests.request("POST", url, headers=headers, data = payload)
    mmchannel = resp.json()

    if resp.status_code == 400:
        return False
    return mmchannel['id']

def add_user_to_mmteam(mmteam_id, mmuser_id):
    url = "%s/v4/teams/%s/members" %(url_server,mmteam_id)
    payload = {
        'team_id': '%s' %mmteam_id,
        'user_id' : '%s' %mmuser_id
    }
    payload = json.dumps(payload)

    headers = {
        'Authorization': 'Bearer %s' %bearer_token,
        'Content-Type': 'application/json'
    }
    resp = requests.request("POST", url, headers=headers, data = payload)
    
    if resp.status_code == 400:
        return False
    return True

def add_user_to_mmchannel(mmchannel_id,mmuser_id):
    url = url_server + "/v4/channels/" + mmchannel_id + "/members"
    payload = {
        'user_id': '%s' %mmuser_id
    }
    payload = json.dumps(payload)

    headers = {
        'Authorization': 'Bearer %s' %bearer_token,
        'Content-Type': 'application/json'
    }
    resp = requests.request("POST", url, headers=headers, data = payload)
    if resp.status_code == 400:
        return False
    return True

def tlentity_to_mmchannel(mmteam_id,tlentity_name,args):
    print("------------------------------------------------------------------------------------------------")
    print(">> Creation du Channel tl " + tlentity_name + " dans MM " + args.mmchannel)
    print("------------------------------------------------------------------------------------------------")

    ## Control de l'existance du groupe de destination/ Creer le groupe si inexistant
    mmchannel_id = get_mmchannel_id(mmteam_id,args.mmchannel)
    
    if not mmchannel_id:
        # Creation du canal
        print(">>>> Creation du channel car inexistant ...\n")
        print(tlentity_name.encode('utf-8'))
        result = create_mmchannel(mmteam_id,args.mmchannel,tlentity_name,"P")

        if not result:
            print(">>>> Error: La création automatique du groupe " + args.mmchannel + " à échouée pour une raison inconnue")
            exit(0)
        else:
            mmchannel_id = result
    else:
        print(">>>> Channel Existant ...")

    print(">> Done")
    print("------------------------------------------------------------------------------------------------\n\n")
    return mmchannel_id

def join_mmuser_to_mattermost(mmchannel_id,mmteam_id,mmuser_id,mmuser,status,args):
    # join User to Team or channel
    if(status == "active"):
        print(">>>> - Ajout de l'utilisateur %s à la TEAM : %s" %(mmuser['mattermost'],args.mmteam))
        add_user_to_mmteam(mmteam_id, mmuser_id)

        if args.type == "channel":
            # join User to group
            print(">>>> - Ajout de l'utilisateur %s au channel : %s \n" %(mmuser['mattermost'],args.mmchannel))
            add_user_to_mmchannel(mmchannel_id, mmuser_id)


def tluser_to_mmusers(mmchannel_id,mmteam_id,tlentity_id,args):
    print(">> Migration des Utilisateurs pour importation des données du channel")
    print("------------------------------------------------------------------------------------------------")

    dir_users = media_files + "/" + str(tlentity_id)

    tlusers = load_tl_users(dir_users)
    mmusers = load_mm_users()

    for mmuser in mmusers:
        for tluser in tlusers:
            if mmuser['telegram'] == tluser['user']:

                # Create required users
                print(">>>> Vérification ou création du compte : %s" %mmuser['email'])

                # get userid
                mmuser_id = get_mmuser_id(mmuser['mattermost'])

                if mmuser_id == False:
                    if not args.dry_run:
                        if create_mmuser(mmuser['email'],mmuser['mattermost'],mmuser['firstname'],mmuser['lastname']) == True:
                            mmuser_id = get_mmuser_id(mmuser['mattermost'])
                            # join User to Team or channel
                            join_mmuser_to_mattermost(mmchannel_id,mmteam_id,mmuser_id,mmuser,tluser['status'],args)
                        else:
                            print(">>>> Error: L'Utilisateur %s n'a pas pu être crée dans le système !" %mmuser['mattermost'])
                            exit(0)
                else:
                    if not args.dry_run:
                        # join User to Team or channel
                        join_mmuser_to_mattermost(mmchannel_id,mmteam_id,mmuser_id,mmuser,tluser['status'],args)

    print(">> Done")
    print("------------------------------------------------------------------------------------------------\n\n")

def tl_posts_to_mm_posts(tlentity_id,args):
    srcdir = media_files + "/" + str(tlentity_id)
    # print(">> Migration des conversations et  medias vers le channel/chat Mattermost : " + args.mmchannel)
    print("------------------------------------------------------------------------------------------------\n")
    
    with open(srcdir + '/channel_messages.json') as tlmsg_file:
        tlmsgs = json.load(tlmsg_file)
        listmsgs = tlmsgs 

    mmmsg = 0
    mmtotal_messages = len(tlmsgs)
    mmall_posts = []
    for tlmsg in tlmsgs:
        mmpost = []
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
            if args.type == "channel":
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

            if args.type == "chat":
                from_user = get_mmuser_from_file(args.tlusername)
                to_user = get_mmuser_from_file(args.tlchat)

                mmpost = {
                    "channel_members": [from_user,to_user],
                    "user": get_mmuser_from_file(mmpost_user),
                    "message": tlmsg['message'],
                    "create_at": timestamp_from_date(tlmsg['date']),
                    "replies": replies_msg,
                    "attachments": attached_files_msg
                }
                mmall_posts.append({
                    "type": "direct_post",
                    "direct_post": mmpost
                })
        
        print(">>>> Transfer du message : " + str(mmmsg) + "/" + str(mmtotal_messages))

    return mmall_posts

def import_mmposts(tlentity_id,mmall_posts,args):

    srcdir = media_files + "/" + str(tlentity_id)
    if not args.dry_run:
        ## Generation du fichier d'import!
        with open(srcdir + '/mattermost_data.json', 'w') as filehandle:
            filehandle.writelines('{"type":"version","version":1}\n')
            filehandle.writelines("%s\n" % json.dumps(mmpost) for mmpost in mmall_posts)
        
        print(">> Done")
        print("------------------------------------------------------------------------------------------------\n")
        ## Generation de la commande d'import des données
        run_mmbulk_commands(srcdir)

        print("\n------------------------------------------------------------------------------------------------")
        print(">> Fin de la migration")
        print("------------------------------------------------------------------------------------------------")

    else:
        print("\n------------------------------------------------------------------------------------------------")
        print(">> Fin de la migration")
        print(">> NB : Aucune modification n'a été apporté sur le système")
        print("------------------------------------------------------------------------------------------------")

def get_tlparticipants(client,tlentity,args):

    tlentity_name = utils.get_display_name(tlentity)
    destdir = media_files + "/" + str(tlentity.id)
    
    print("------------------------------------------------------------------------------------------------")
    print(">> Collecte des informations de Chanel/User/Chat : " + tlentity_name)
    print("------------------------------------------------------------------------------------------------\n")

    # Get users Participants
    tlall_participants = client.get_participants(tlentity,limit=int(limit))
    
    if args.type == "chat":
        tlall_participants.append(client.get_me())

    tlall_user_details = []
    print(">> Get All participants: " + str(len(tlall_participants)))

    for tlparticipant in tlall_participants:
        tlall_user_details.append({
            "id": tlparticipant.id,
            "first_name": tlparticipant.first_name,
            "last_name": tlparticipant.last_name,
            "user": tlparticipant.username,
            "phone": tlparticipant.phone,
            "is_bot": tlparticipant.bot,
            "status": "active"
        })

    dump_tlusers(destdir,tlall_user_details)

def get_tl_messages(client,tlentity,args):

    destdir = media_files + "/" + str(tlentity.id)
    if not os.path.isfile(destdir + '/channel_messages.json'):
        tlall_messages = []
        tloffset_id = 0
        tltotal_messages = 0

        print(">> Get All messages\n")
        while True:
            tlhistory = client.get_messages(tlentity,offset_id=tloffset_id,limit=int(limit))
            if not tlhistory:
                break

            for tlmessage in tlhistory:
                if tlmessage.fwd_from is not None:
                    tlfwd = []
                    tlfwd.append({
                        "date": tlmessage.fwd_from.date,
                        "from_id": tlmessage.fwd_from.from_id,
                        "from_name": tlmessage.fwd_from.from_name
                    })
                else:
                    tlfwd = None
                if tlmessage.media is not None:
                    is_media = True
                    mediadir = destdir + "/" + str(tlmessage.id)
                    if not os.path.exists(mediadir):
                        os.makedirs(mediadir)
                    if not args.dry_run:
                        tlmessage.download_media(file=mediadir)
                else:
                    is_media = False
                if tlmessage.action is not None:
                    is_action = True
                else:
                    is_action = False

                # add inactive users
                if get_tl_username_from_file(destdir,tlmessage.from_id) is None:
                    tluser_id  = get_tl_id_from_file(destdir,tlmessage.from_id)
                    if tlmessage.from_id != tluser_id:
                        inactive_tluser = client.get_entity(PeerUser(tlmessage.from_id))
                        add_tlinactive_user(destdir,inactive_tluser)

                # print(client.get_entity(PeerUser(360206578)))
                # exit(0)
                tlall_messages.append({
                    "id": tlmessage.id,
                    "date": tlmessage.date,
                    "message": tlmessage.message,
                    "from_id": tlmessage.from_id,
                    "fwd_from": tlfwd,
                    "reply_to_msg_id": tlmessage.reply_to_msg_id,
                    "media": is_media,
                    "action": is_action
                })

            tloffset_id = tlhistory[len(tlhistory) - 1].id
            tltotal_messages = len(tlall_messages)
            print(">>>> Current Offset ID is:", tloffset_id, "; Total Messages:", tltotal_messages)
            if int(tltotal_count_limit) != 0 and tltotal_messages >= int(tltotal_count_limit):
                break

        with open(destdir + '/channel_messages.json', 'w') as outfile:
            # json.dump(all_messages, outfile, cls=DateTimeEncoder)
            json.dump(tlall_messages, outfile, cls=DateTimeEncoder)

def export_telegram(args):

    client = init_tl_user(args)
    ## check action process
    if args.type == "chat":
        if "https://t.me" not in args.tlchat:
            tluser_input_entity = args.tlchat
        else:
            print(">> Error: Vous tentez de migrer une conversation, Veuillez définir le channel de destination option --tlchat username")
            exit(0)

    if args.type == "channel":
        if "https://t.me" in args.tlchannel:
            tluser_input_entity = args.tlchannel
        else:
            print(">> Error: Vous tentez de migrer un channel, Veuillez définir le channel de destination option --tlchannel https://t.me....")
            exit(0)

    # me = client.get_me()
    tlentity = client.get_entity(tluser_input_entity)

    ## Reinitialisation du repertoire de donnée
    destdir = media_files + "/" + str(tlentity.id)
    init_dir(destdir,args)
    tlentity_name = utils.get_display_name(tlentity)
    # Generation du fichier des participants
    get_tlparticipants(client,tlentity,args)
    # Recuperation de l'emsemble des messages
    get_tl_messages(client,tlentity,args)
    # Controle de l'existance des utilisateurs (recherche des participants inexistants dans le channel)
    check_match_users(destdir)

    print(">> Done")
    print("------------------------------------------------------------------------------------------------\n")
    return {"tlentity_id": tlentity.id,"tlentity_name": tlentity_name}


def import_mattermost(tlentity_info,args):

    tlentity_name = tlentity_info['tlentity_name']
    tlentity_id = tlentity_info['tlentity_id']

    # Check if channel exists
    mmteam_id = get_mmteam_id(args.mmteam)
    if not mmteam_id:
        print(">>>> Error : Team: " + args.mmteam + " Introuvable")
        exit(0)

    if args.type == "channel":

        ## Traitement des channels pour importation
        mmchannel_id = tlentity_to_mmchannel(mmteam_id,tlentity_name,args)
        ## Traitement des utilisateurs pour importation
        tluser_to_mmusers(mmchannel_id,mmteam_id,tlentity_id,args)
        ## Traitement des conversation pour importation
        mmall_posts = tl_posts_to_mm_posts(tlentity_id,args)
        ## Generation du fichier d'import!
        import_mmposts(tlentity_id,mmall_posts,args)

    if args.type == "chat":

        ## Traitement des utilisateurs pour importation
        tluser_to_mmusers("",mmteam_id,tlentity_id,args)
        ## Traitement des conversation pour importation
        mmall_posts = tl_posts_to_mm_posts(tlentity_id,args)
        ## Generation du fichier d'import!
        import_mmposts(tlentity_id,mmall_posts,args)

