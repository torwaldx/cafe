import os
from telethon.errors.rpcerrorlist import (
    ApiIdInvalidError,
    PhoneNumberInvalidError,
)
from telethon.sync import TelegramClient

def clear_screen():
    if os.name == "posix":
        os.system("clear")
    else:
        os.system("cls")

def telethon_session():

    SESSION = './tg_sessions/' + os.getenv("TG_SESSION", 'cafe')
    API_ID = os.getenv("TG_API_ID")
    API_HASH = os.getenv("TG_API_HASH")

    print(SESSION, API_ID, API_HASH)

    client = TelegramClient(
        SESSION,
        API_ID,
        API_HASH,
        system_version="5.15.10-vxCUSTOM",
    )

    # logging in
    try:
        with client as client:
            print("Generating default session")
            client.send_message(
                "me",
                f"**YOUR SESSION** has been generated and saved in `{SESSION}.session`\n\n**Do not share this file anywhere!**",
            )
            return
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
    _ = input("press any key to exit..")
    exit(0)


main()
