import configparser
import json
import os
import shutil

from datetime import date, datetime
from telethon import TelegramClient , events, sync
from telethon.errors import SessionPasswordNeededError
from telethon import utils

# Reading Configs
tlconfig = configparser.ConfigParser()
tlconfig.read("config.ini")

# Setting configuration values
tlapi_id = tlconfig['Telegram']['api_id']
tlapi_hash = tlconfig['Telegram']['api_hash']
tlapi_hash = str(tlapi_hash)

currentdir = os.getcwd()
media_files = currentdir + "/" + tlconfig['Telegram']['media_files']
# bot_token = tlconfig['Telegram']['bot_token']
limit = tlconfig['Telegram']['limit']
tltotal_count_limit = tlconfig['Telegram']['total_count_limit']

# some functions to parse json date
class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):   # pylint: disable=E0202
        if isinstance(o, datetime):
            return o.isoformat()

        if isinstance(o, bytes):
            return list(o)

        return json.JSONEncoder.default(self, o)

def callback(current, total):
    print('>>>>>>>> Downloaded', current, 'out of', total,
          'bytes: {:.2%}'.format(current / total))

def export_telegram(args):

    tlphone = args.tlphone
    tlusername = args.tlusername
    tluser_input_channel = args.tlchannel
    
    # Create the client and connect
    client = TelegramClient(tlusername, tlapi_id, tlapi_hash)
    if client.start(phone=tlphone):
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

    client.takeout()
    # me = client.get_me()
    if "https://t.me" in tluser_input_channel and args.mmchannel == "False":
        print("Error: Vous tentez de migrer un channel, Veuillez définir le channel de destination option --mmchannel")
        exit(0)

    if "https://t.me" not in tluser_input_channel and args.mmchannel != "False":
        print("Error: Vous tentez de migrer une conversation, veuillez définir le channel de destination option --mmchannel à <<False>>")
        exit(0)

    tlchannel = client.get_entity(tluser_input_channel)
    tlchannel_name = utils.get_display_name(tlchannel)

    ## Reinitialisation du repertoire de donnée
    destdir = media_files + "/" + str(tlchannel.id)
    
    for root, dirs, files in os.walk(destdir):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))

    if not os.path.exists(destdir):
        os.makedirs(destdir)


    print("------------------------------------------------------------------------------------------------")
    print(">> Collecte des informations de Chanel/User/Chat : " + utils.get_display_name(tlchannel))
    print("------------------------------------------------------------------------------------------------\n")

    # Get users Participants
    tlall_participants = client.get_participants(tlchannel,limit=int(limit))
    tlall_user_details = []
    print(">> Get All participants: " + str(len(tlall_participants)))

    for tlparticipant in tlall_participants:
        tlall_user_details.append({
            "id": tlparticipant.id,
            "first_name": tlparticipant.first_name,
            "last_name": tlparticipant.last_name,
            "user": tlparticipant.username,
            "phone": tlparticipant.phone,
            "is_bot": tlparticipant.bot
        })

    with open(destdir + '/user_data.json', 'w') as outfile:
        json.dump(tlall_user_details, outfile)

  
        
    tlall_messages = []
    tloffset_id = 0
    tltotal_messages = 0
    print(">> Get All messages")

    while True:
        tlhistory = client.get_messages(tlchannel,offset_id=tloffset_id,limit=int(limit))
        if not tlhistory:
            break

        for tlmessage in tlhistory:

            # print(tlmessage)

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
                tlmessage.download_media(file=mediadir,progress_callback=callback)
            else:
                is_media = False

            if tlmessage.action is not None:
                is_action = True
            else:
                is_action = False


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
        print("\n>>>> Current Offset ID is:", tloffset_id, "; Total Messages:", tltotal_messages)
        print("-------------------------------------------------------")
        if int(tltotal_count_limit) != 0 and tltotal_messages >= int(tltotal_count_limit):
            break

    with open(destdir + '/channel_messages.json', 'w') as outfile:
        # json.dump(all_messages, outfile, cls=DateTimeEncoder)
        json.dump(tlall_messages, outfile, cls=DateTimeEncoder)

    print(">> Done")
    print("------------------------------------------------------------------------------------------------\n")
    return {"tlchannel_id": tlchannel.id,"tlchannel_name": tlchannel_name}
