import os
from time import sleep

def spinner():
    print("Checking if Telethon is installed...")
    for _ in range(3):
        for frame in r"-\|/-\|/":
            print("\b", frame, sep="", end="", flush=True)
            sleep(0.1)

def clear_screen():
    if os.name == "posix":
        os.system("clear")
    else:
        os.system("cls")

def get_api_id_and_hash():
    print(
        "Get your API ID and API HASH from https://my.telegram.org/apps to proceed.\n\n",
    )
    try:
        API_ID = int(input("Please enter your API ID: "))
    except ValueError:
        print("APP ID must be an integer.\nQuitting...")
        exit(0)
    API_HASH = input("Please enter your API HASH: ")
    return API_ID, API_HASH


def telethon_session():
    try:
        spinner()
        import telethon

        x = "\bFound an existing installation of Telethon...\nSuccessfully Imported.\n\n"
    except ImportError:
        print("Installing Telethon...")
        os.system("pip uninstall telethon -y && pip install -U telethon")

        x = "\bDone. Installed and imported Telethon."
    clear_screen()
    print(x)

    from telethon.errors.rpcerrorlist import (
        ApiIdInvalidError,
        PhoneNumberInvalidError,
        UserIsBotError,
    )

    from telethon.sync import TelegramClient

    session_name = os.getenv("TG_SESSION", 'cafe')
    API_ID = os.getenv("TG_API_ID", '')
    API_HASH = os.getenv("TG_API_HASH", '')

    if API_ID == "" or API_HASH == "":
        API_ID, API_HASH = get_api_id_and_hash()

    client = TelegramClient(
        session_name,
        API_ID,
        API_HASH,
        system_version="5.15.10-vxCUSTOM",
    )

    # logging in
    try:
        with client as client:
            print("Generating default session")
            try:
                client.send_message(
                    "me",
                    f"**YOUR SESSION** has been generated and saved in `./tg_session/{session_name}.session`\n\n**Do not share this file anywhere!**",
                )
                return
            except UserIsBotError:
                print("Are you trying to Generate Session for your Bot's Account?")
                print(f"Here is That!\n`./tg_session/{session_name}.session`\n\n")
                print("NOTE: You can't use that as User Session..")
    except ApiIdInvalidError:
        print("Your API ID/API HASH combination is invalid. Kindly recheck.\nQuitting...")
        exit(0)
    except ValueError:
        print("API HASH must not be empty!\nQuitting...")
        exit(0)
    except PhoneNumberInvalidError:
        print("The phone number is invalid!\nQuitting...")
        exit(0)
    except Exception as er:
        print("Unexpected Error Occurred while Creating Session")
        print(er)


def main():
    clear_screen()
    telethon_session()

    x = input("Run again? (Y/n)")
    if x.lower() in ["y", "yes"]:
        main()
    else:
        exit(0)


main()
