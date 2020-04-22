import configparser
import json
import os
import shutil

from datetime import date, datetime
from telethon import TelegramClient , events, sync
from telethon.errors import SessionPasswordNeededError
from telethon import utils

# some functions to parse json date
class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):   # pylint: disable=E0202
        if isinstance(o, datetime):
            return o.isoformat()

        if isinstance(o, bytes):
            return list(o)

        return json.JSONEncoder.default(self, o)


def export_telegram(args):

    # Reading Configs
    config = configparser.ConfigParser()
    config.read("config.ini")

    # Setting configuration values
    api_id = config['Telegram']['api_id']
    api_hash = config['Telegram']['api_hash']
    api_hash = str(api_hash)

    phone = args.tlphone
    username = args.tlusername
    user_input_channel = args.tlchannel

    media_files = config['Telegram']['media_files']
    # bot_token = config['Telegram']['bot_token']
    limit = config['Telegram']['limit']
    total_count_limit = config['Telegram']['total_count_limit']

       
    # Create the client and connect
    client = TelegramClient(username, api_id, api_hash)
    if client.start(phone=phone):
        print("Client Created")

    # Ensure you're authorized
    if not client.is_user_authorized():
        client.send_code_request(phone)
        try:
            client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            client.sign_in(password=input('Password: '))

    # me = client.get_me()
    channel = client.get_entity(user_input_channel)
    channel_name = utils.get_display_name(channel)

    ## Reinitialisation du repertoire de donnée
    destdir = media_files + "/" + channel_name
    
    for root, dirs, files in os.walk(destdir):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))

    if not os.path.exists(destdir):
        os.makedirs(destdir)


    print("------------------------------------------------------------------------------------------------")
    print(">> Collecte des informations de Chanel/User/Chat : " + utils.get_display_name(channel))
    print("------------------------------------------------------------------------------------------------\n")

    # Get users Participants
    all_participants = client.get_participants(channel,limit=int(limit))
    all_user_details = []
    print(">> Get All participants: " + str(len(all_participants)))

    for participant in all_participants:
        all_user_details.append({
            "id": participant.id,
            "first_name": participant.first_name,
            "last_name": participant.last_name,
            "user": participant.username,
            "phone": participant.phone,
            "is_bot": participant.bot
        })

    with open(destdir + '/user_data.json', 'w') as outfile:
        json.dump(all_user_details, outfile)

  
        
    all_messages = []
    offset_id = 0
    total_messages = 0
    print(">> Get All messages")

    while True:
        history = client.get_messages(channel,offset_id=offset_id,limit=int(limit))
        if not history:
            break

        for message in history:
            
            if message.fwd_from is not None:
                fwd = []
                fwd.append({
                    "date": message.fwd_from.date,
                    "from_id": message.fwd_from.from_id,
                    "from_name": message.fwd_from.from_name
                })
            else:
                fwd = None

            if message.media is not None:
                is_media=True
                mediadir = destdir + "/" + str(message.id)
                if not os.path.exists(mediadir):
                    os.makedirs(mediadir)
                message.download_media(file=mediadir)
            else:
                is_media = False

            if message.action is not None:
                is_action = True
            else:
                is_action = False


            all_messages.append({
                "id": message.id,
                "date": message.date,
                "message": message.message,
                "from_id": message.from_id,
                "fwd_from": fwd,
                "reply_to_msg_id": message.reply_to_msg_id,
                "media": is_media,
                "action": is_action
            })

        offset_id = history[len(history) - 1].id
        total_messages = len(all_messages)
        print(">>>> Current Offset ID is:", offset_id, "; Total Messages:", total_messages)
        
        if int(total_count_limit) != 0 and total_messages >= int(total_count_limit):
            break

    with open(destdir + '/channel_messages.json', 'w') as outfile:
        # json.dump(all_messages, outfile, cls=DateTimeEncoder)
        json.dump(all_messages, outfile, cls=DateTimeEncoder)

    print(">> Done")
    print("------------------------------------------------------------------------------------------------\n")
    return channel_name
