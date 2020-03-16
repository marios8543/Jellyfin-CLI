from jellyfin_cli.jellyfin_client.JellyfinClient import HttpClient, InvalidCredentialsError, ServerContext, HttpError
from aiohttp import ClientSession
from json import load, dump
from getpass import getpass

async def login():
    try:
        return await load_creds()
    except Exception as e:
        print(str(e))
        pass
    while True:
        server = input("Enter the server URL: ")
        if server.endswith("/"):
            server = server[:-1]
        username = input("Enter the username: ")
        password = getpass("Enter the password: ")
        client = HttpClient(server)
        try:
            await client.login(username, password)
            print("Logged in...")
            return client
        except InvalidCredentialsError as e:
            print(str(e))
            continue

def store_creds(context):
    with open("creds.json", "w") as f:
        dump({
            "url": context.url,
            "auth_header": context.client._default_headers["x-emby-authorization"],
            "user_id": context.user_id,
            "server_id": context.server_id,
            "username": context.username
        },f)

async def load_creds():
    with open("creds.json", "r") as f:
        dc = load(f)
        client = HttpClient(dc["url"], ServerContext(cfg=dc))
        await client.get_views()
        return client