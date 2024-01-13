import json
import asyncio
import re
import time
import config
import urllib.request
import urllib.parse
from alive_progress import alive_bar
import yadisk
import shortuuid


path = config.ya_path
load_amount = config.load_amount


def get_response(group, count, offset):
    url = (
        "https://api.vk.com/method/wall.get?domain="
        + group
        + "&count="
        + str(count)
        + "&offset="
        + str(offset)
        + "&access_token="
        + config.vk_token
        + "&v=5.199"
    )
    content = urllib.request.urlopen(url).read()
    return json.loads(content)["response"]


def get_count(group):
    return get_response(group, 1, 1)["count"]


def get_items(group, count, offset):
    return get_response(group, count, offset)["items"]


def get_photos_links_by_item(item):
    attachments = item["attachments"]
    photos = []
    for attachment in attachments:
        if (attachment["type"] == "photo"):
            sizes = sorted(attachment["photo"]["sizes"], key=lambda size: size["width"], reverse=True)
            link = re.sub(
                "&([a-zA-Z]+(_[a-zA-Z]+)+)=([a-zA-Z0-9-_]+)",
                "",
                sizes[0]["url"])
            photos.append(link)
    return photos


async def send_to_ya(photos_links):
    client = yadisk.AsyncClient(token=config.ya_token)
    with alive_bar(len(photos_links)) as bar:
        async with client:
            for task in asyncio.as_completed([client.upload_url(photo, path + str(shortuuid.uuid()) + ".jpg") for photo in photos_links]):
                await task
                bar()


def collect_links(group, offset):
    items = get_items(group, load_amount, offset)
    photos_links = []
    for item in items:
        photos_links.extend(get_photos_links_by_item(item))
    return photos_links


def main():
    print('stating program...')
    with open('groups.json', 'r') as file:
        groups = json.load(file)
    for group in groups:
        items_count = get_count(group)
        offset = 1
        stage = 1
        print("load group: " + group)
        while offset < items_count:
            photos_links = collect_links(group, offset)
            print("stage " + str(stage))
            asyncio.run(send_to_ya(photos_links))
            offset += load_amount
            stage += 1
            time.sleep(5) # anti-spam system

if __name__ == "__main__":
    main()
