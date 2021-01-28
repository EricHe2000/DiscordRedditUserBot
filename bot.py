import discord
from discord.ext import commands, tasks
from itertools import cycle
import requests
import requests.auth
import json
import random

const config = require('./config.json')

count = 0

token = config.token

client = commands.Bot(command_prefix=config.prefix)

client_auth = requests.auth.HTTPBasicAuth(
    config.clientID, config.clientSecret)
post_data = {"grant_type": "password", "username": config.redditUsername,
             "password": config.redditPassword}
headers = {"User-Agent": config.redditBotName}
response = requests.post("https://www.reddit.com/api/v1/access_token?duration=permanent",
                         auth=client_auth, data=post_data, headers=headers)
data = response.json()
access_token = 'bearer ' + data['access_token']


@client.event
async def on_ready():
    check_update.start()
    check_error.start()
    print("Bot is ready")


@client.command()
async def content(ctx):
    await ctx.send('https://www.reddit.com/user/' + config.username)


@client.command()
async def status(ctx):
    response = requests.get("https://www.reddit.com/r/" + config.username + "/about.json",
                            headers={'User-agent': config.redditBotName})
    data = response.json()
    await ctx.send(data["data"]["public_description"])


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Invalid command used. Use -help to see list of commands.")


@client.command()
async def randomPost(ctx):
    try:
        headers = {"Authorization": access_token,
                   "User-Agent": config.redditBotName}
        url = 'https://oauth.reddit.com/user/'+config.username'/submitted?limit=100'
        response = requests.get(url, headers=headers)
        data = response.json()
        x = random.randint(0, count-1)

        await ctx.send(data["data"]["children"][x]["data"]["title"])
        selftext = data["data"]["children"][x]["data"]["selftext"]
        if len(selftext) > 2000:
            chunks = [selftext[i:i+2000]
                      for i in range(0, len(selftext), 2000)]
            for i in chunks:
                await ctx.send(i)
        else:
            await ctx.send(selftext)
    except Exception as e:
        print(e)


def getCount():
    count1 = 0
    after = ''
    begin = False
    while after or not begin:
        headers = {"Authorization": access_token,
                   "User-Agent": config.redditBotName}
        url = 'https://oauth.reddit.com/user/' +
        config.username + '/submitted?after=' + after
        response = requests.get(url, headers=headers)
        data = response.json()
        count1 += data["data"]["dist"]
        after = data["data"]["after"]
        begin = True
    return count1


count = getCount()


@tasks.loop(seconds=60)
async def check_error():
    try:
        getCount()
    except:
        global client_auth, post_data, headers, access_token
        responseT = requests.post("https://www.reddit.com/api/v1/access_token",
                                  auth=client_auth, data=post_data, headers=headers)
        data = responseT.json()
        access_token = 'bearer ' + data['access_token']


def getNewest():  # returns newest URL string
    headers = {"Authorization": access_token,
               "User-Agent": config.redditBotName}
    url = 'https://oauth.reddit.com/user/' +
    config.username+'/submitted?sort=top&t=hour'
    response = requests.get(url, headers=headers)
    data = response.json()
    dataF = data["data"]["children"][0]["data"]
    return dataF["url"]


@tasks.loop(seconds=500)
async def check_update():
    try:
        global count
        if getCount() > count:
            await client.get_channel(config.discordChannelID).send("New Post")
            url = getNewest()
            await client.get_channel(config.discordChannelID).send(url)
            count = getCount()
        if getCount() < count:
            await client.get_channel(config.discordChannelID).send("Post was deleted.")
            count = getCount()
    except ValueError:
        print("value Error:")
    except Exception as e:
        print("Please restart the bot.")
client.run(token)
