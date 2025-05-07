from datetime import datetime, timezone

from shared.models.models import Instagram_Account, Source, Tg_Channel


class SourceService:
    async def add_inst_account(self, user_name: str, user_id) -> Instagram_Account:
        async with Instagram_Account.ormar_config.database.transaction():
            account, created = await Instagram_Account.objects.get_or_create(
                inst_username=user_name, inst_user_id=user_id
            )
            if created:
                new_src = await Source.objects.create(source_type="instagram")
                account.source = new_src
                await account.update()
        return account

    async def get_active_inst_accounts(self) -> list[Instagram_Account]:
        accounts = await Instagram_Account.objects.filter(
            source__is_active=True, source__is_deleted=False
        ).all()
        return accounts

    async def get_active_tg_channels(self) -> list[Tg_Channel]:
        accounts = await Tg_Channel.objects.filter(
            source__is_active=True, source__is_deleted=False
        ).all()
        return accounts

    async def tg_channel_update(self, channel: Tg_Channel, last_message_id: int):
        channel.last_message_id = last_message_id
        channel.source.processed_at = datetime.now(timezone.utc)
        await channel.update()
        await channel.source.update()

    async def instagram_account_update(self, account: Instagram_Account, last_message_time: int):
        account.last_message_time = last_message_time
        account.source.processed_at = datetime.now(timezone.utc)
        await account.update()
        await account.source.update()
