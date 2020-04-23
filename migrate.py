import argparse
from export_telegram import export_telegram
from import_mattermost import import_mattermost

def main():
    #fileDir = os.path.dirname(os.path.realpath('__file__'))

    parser = argparse.ArgumentParser()
    parser.add_argument("--type", type=str)
    parser.add_argument("--tlusername", type=str)
    parser.add_argument("--tlphone", type=str)
    parser.add_argument("--tlchannel", type=str)
    parser.add_argument("--mmteam", type=str)
    parser.add_argument("--mmchannel", type=str)
    # parser.add_argument("--mmusername", type=str)
    # parser.add_argument("--mmpassword", type=str)
    args = parser.parse_args()

    if args.type not in ["chat","channel"]:
        print(">> Error: Veuillez choisir le type de cannal à migrer (channel|chat)")
        exit(0)
    else:
        if args.type == "chat":
            if not args.tlchat or not args.tlphone or not args.tlusername or not args.mmteam:
                print("les options suivantes sont obligatoires :\n --tlusername\n--tlphone\n--tlchat\n--mmteam")
                print("shell> python3 migrate.py --tlusername usertelegram --tlphone phone_number_usertelegram --tlchat username_correspondant --mmteam veone")
                exit(0)

        if args.type == "channel":
            if not args.tlchannel or not args.tlphone or not args.tlusername or not args.mmteam or not args.mmchannel:
                print("les options suivantes sont obligatoires :\n --tlusername\n--tlphone\n--tlchannel\n--mmteam\n--mmchannel")
                print("eg. shell> python3 migrate.py --tlusername admin_channel_telegram --tlphone phone_number_admin_channel --tlchannel https://t.me/joinchat/EchPiQ1b7_rOL-3KF0aXuQ --mmteam veone --mmchannel channel_mattermost")
                exit(0)
    
    
    import_mattermost(export_telegram(args),args)
if __name__ == "__main__":
    main()
