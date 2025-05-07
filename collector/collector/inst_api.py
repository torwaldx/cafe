from hikerapi import Client

from shared.models.models import Instagram_Account
from shared.logging_config import setup_logger
from time import sleep

logger = setup_logger()

class InstAPI:
    def __init__(self, ACCESS_KEY):
        self.ACCESS_KEY = ACCESS_KEY
        self.client = Client(ACCESS_KEY)

    def get_inst_user_id(self, username: str) -> str:
        clean_username = username.lstrip("@")
        user = self.client.user_by_username_v2(username=clean_username)
        return user["user"]["id"]

    def extract_posts(
        self, ig_posts: list[dict], last_message_time: int
    ) -> tuple[list[dict[str, str]], bool]:
        extracted = []
        FINAL = True

        for item in ig_posts:
            id = item.get("id")
            text = item.get("caption", {}).get("text")
            timestamp = item.get("taken_at_ts", item.get("taken_at"))

            if timestamp < last_message_time:
                return extracted, FINAL

            if text and timestamp:
                extracted.append({"external_id": id, "text": text, "timestamp": timestamp})

        return extracted, not FINAL

    def get_new_posts(self, account: Instagram_Account, limit: int = 10) -> list[dict]:
        posts = []
        page_id = None

        while len(posts) < limit:
            try:
                resp = self.client.user_medias_v2(user_id=account.inst_user_id, page_id=page_id)
                chunk = resp["response"]["items"]
                extracted, final = self.extract_posts(chunk, account.last_message_time)
                posts.extend(extracted)

                if final:
                    break

                page_id = resp["next_page_id"]
                if not page_id:
                    break
            except Exception as e:
                logger.error(f"❌ Ошибка при получении постов для {account.inst_username}")
                logger.error(self.ACCESS_KEY)
                logger.error(str(e), exc_info=True)
                logger.error(str(resp))
                break

        return posts
    
    def format_info(self, user: dict) -> str:
        keys = ["full_name", "page_name", "biography"]
        values = []
        for key in keys:
            val =  user.get(key, False)
            if val:
                values.append(val)
        if values:
            result = ' | '.join(values).replace('\n', ' - ')
            return f" ({result})"
        return ''
    

    def get_bio(self, username: str) -> str:
        clean_username = username.lstrip("@")
        sleep(1)
        try:
            user_dict = self.client.user_by_username_v2(username=clean_username)
            return username + self.format_info(user_dict["user"])
        except Exception as e:
            logger.error(f"Ошибка при получении информации о пользователе {username}")
            logger.error(str(e), exc_info=True)
            
            return username
        
