import re
from pytube import Channel

channelURL = "https://www.youtube.com/channel/UC0eNsGYZK87OKoDRcZooqdA"

if re.search("/channel/", channelURL) or re.search("@", channelURL) or re.search("/user/", channelURL) or re.search("/c/", channelURL):
    # This code detects if the given URL is a channel. If the check comes back as True then it grabs the data using pytube.
    c = Channel(channelURL)
    channel_name = c.channel_name
    channel_id = c.channel_id
    channel_id_link = "http://youtube.com/channel/" + channel_id

    print("Channel Name: " + channel_name)
    print("Channel ID: " + channel_id)
    print("Channel Link: " + channel_id_link)

    for url in c.video_urls[:3]:
        print(url)