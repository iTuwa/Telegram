import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError


def fmt(v):
    return v if v is not None else "<none>"


async def main():
    load_dotenv()
    api_id = os.getenv("TG_API_ID")
    api_hash = os.getenv("TG_API_HASH")
    phone = os.getenv("TG_PHONE")

    if not api_id or not api_hash:
        print("Missing TG_API_ID or TG_API_HASH in environment/.env")
        return

    client = TelegramClient("forwarder", int(api_id), api_hash)
    print("Starting Telegram client (may prompt for login code)...")
    await client.connect()

    if not await client.is_user_authorized():
        if not phone:
            print("No TG_PHONE provided. Can't sign in interactively.")
            await client.disconnect()
            return
        # Send code and prompt user to enter it (non-blocking environments may still accept input)
        await client.send_code_request(phone)
        code = input("Enter the login code you received: ")
        try:
            await client.sign_in(phone=phone, code=code)
        except SessionPasswordNeededError:
            # Two-step verification enabled; try TG_PASSWORD from env or prompt
            pwd = os.getenv("TG_PASSWORD")
            if not pwd:
                pwd = input("Two-step password required. Enter your password: ")
            await client.sign_in(password=pwd)

    print("Connected. Listing dialogs (id, api-chat-id, username, title, type):")
    async for dialog in client.iter_dialogs():
        ent = dialog.entity
        entity_id = getattr(ent, 'id', None)
        # For channels, a common API chat id form is -100{entity_id}
        api_chat_id = f"-100{entity_id}" if dialog.is_channel else str(entity_id)
        username = getattr(ent, 'username', None)
        title = getattr(dialog, 'title', None) or getattr(ent, 'first_name', None) or getattr(ent, 'last_name', None) or ""
        kind = 'channel' if dialog.is_channel else ('user' if dialog.is_user else 'chat')
        print(f"{dialog.id}\t{api_chat_id}\t{fmt(username)}\t{fmt(title)}\t{kind}")

    await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
