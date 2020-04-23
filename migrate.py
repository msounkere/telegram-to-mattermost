import configparser
import argparse
import os
from export_telegram import export_telegram
from import_mattermost import import_mattermost
# Reading Configs
config = configparser.ConfigParser()
config.read("config.ini")

# Setting configuration values
mattermost_cli = config['Mattermost']['mattermost_cli']

def get_mmbulk_commands():
    currentdir = os.getcwd() + "/" + "media"
    mmchannel_dirs = os.listdir(currentdir)
    
    ## Get mmchannel list json file
    mmlist_command_actions = []
    for mmchannel_dir in mmchannel_dirs:
        current_channel_dir = currentdir + "/" + mmchannel_dir
        if os.path.isdir(current_channel_dir):
            current_channel_jsonfile = current_channel_dir + "/mattermost_data.json"
            if os.path.isfile(current_channel_jsonfile):
                mmlist_command_actions.append(current_channel_jsonfile)

    print(mmlist_command_actions)
    
    # /mattermost/bin/mattermost import bulk /opt/telegram-to-mattermost/media/1192446106/mattermost_data.json --apply

    ## Generate cmd
    cmd = "%s import bulk " % mattermost_cli 
    with open('bulk_import.py', 'w') as filehandle:
        filehandle.writelines('import os\n')
        filehandle.writelines("os.system(\"" + cmd + mm_command_action + " --apply\")\n"  for mm_command_action in mmlist_command_actions)
    


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
    get_mmbulk_commands()

if __name__ == "__main__":
    main()
