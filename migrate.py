import argparse
from export_telegram import export_telegram
from import_mattermost import import_mattermost


def main():
    #fileDir = os.path.dirname(os.path.realpath('__file__'))

    parser = argparse.ArgumentParser()
    parser.add_argument("--tlusername", type=str)
    parser.add_argument("--tlphone", type=str)
    parser.add_argument("--tlchannel", type=str)
    parser.add_argument("--mmteam", type=str)
    parser.add_argument("--mmchannel", type=str)
    # parser.add_argument("--mmusername", type=str)
    # parser.add_argument("--mmpassword", type=str)
    args = parser.parse_args()

    if not args.tlchannel or not args.tlphone or not args.tlusername or not args.mmteam or not args.mmchannel:
        print("Eg 1 - Migration de Channel :")
        print("shell> python3 migrate.py --tlusername admin_channel_telegram --tlphone phone_number_admin_channel --tlchannel https://t.me/joinchat/EchPiQ1b7_rOL-3KF0aXuQ --mmteam veone --mmchannel channel_mattermost")
        print("---")
        print("Eg 2 - Migration de chat direct :")
        print("shell> python3 migrate.py --tlusername usertelegram --tlphone phone_number_usertelegram --tlchannel username_correspondant --mmteam veone --mmchannel False")
        exit(0)

    import_mattermost(export_telegram(args),args)

if __name__ == "__main__":
    main()
