#!/usr/bin/python3

import discord
import sqlite3
import re
import asyncio
import random
from sqlite3 import Error

TOKEN = ''
client = discord.Client()
database = "./points.db"
miniac_server_id = 0
miniac_general_channel_id = 0
miniac_welcome_channel_id = 0

def get_sorted_leaderboard(conn):
    """
    Returns the top 20 users on the discord server ordered by points.
    :param: conn: connection to the database
    :return: list
    """
    # We're querying for 20 people instead of 10 because sometimes the top 10 will include people who
    # are no longer in the server. This way, we can sort the "None" types out and get a real top 10.
    get_sorted_leaderboard_query = "Select id, sum(points) AS pointCount FROM UserData GROUP BY id ORDER BY pointCount DESC LIMIT 20"
    if conn is not None:
        try:
            cur = conn.cursor()
            cur.execute(get_sorted_leaderboard_query)
            return cur.fetchall()
        except Error as e:
            print('Failed to retrieve the leaderboard. Error is below.')
            print(e)
    else:
        print("Error! Database connection was not established when querying the order of the leaderboard.")

def get_user_points(user,conn):
    get_points_query = "SELECT sum(points) FROM UserData WHERE id='{}'".format(user)
    if conn is not None:
        try:
            cur = conn.cursor()
            cur.execute(get_points_query)
            return cur.fetchone()[0]
        except Error as e:
            print('Failed to retrieve {}\'s points. Error is below.'.format(user))
            print(e)
    else:
        print("Error! Database connection was not established when querying a user's points.")

def get_user_gallery(user, conn):
    """
    This returns the content of a user's gallery table.
    :param user: the ID of a discord user
    :param conn: connection to the database
    :return: returns a list of tuples
    """
    get_gallery_query = "SELECT link FROM UserData WHERE id='{}' AND link IS NOT NULL".format(user)
    if conn is not None:
        try:
            cur = conn.cursor()
            cur.execute(get_gallery_query)
            return cur.fetchall()
        except Error as e:
            print('Failed to retrieve {}\'s gallery. Error is below.'.format(user))
            print(e)
    else:
        print("Error! Database connection was not established when querying a user's gallery.")

def get_member(member_id):
    return client.get_guild(miniac_server_id).get_member(member_id)

def add_user_submission(user,link,points,conn):
    add_submission_query = "INSERT INTO UserData (id,link,points,date) VALUES ({},{},{},{})".format(user,link,points,sqlite3.Date('now'))
    if conn is not None:
        try:
            cur = conn.cursor()
            cur.execute(add_submission_query)
            return cur.fetchall()
        except Error as e:
            print('Failed to add a submission for user {}. Error is below.'.format(user))
            print(e)
    else:
        print("Error! Database connection was not established when adding a submission for user.")

async def set_name(user_points, member, discord_user_id):
    #If possible, use the members nick name on the server before their account name
    user_name = ''
    try:
        user_name = member.nick
    except AttributeError:
        print('This member has no nickname, will proceed using their user account name')
    if not user_name:
        user_name = member.name

    # Everytime we award points, the emojis we award are removed, the person's bracket is
    # recalculated, and they are given the correct emoji so everything stays straight.
    if '\N{money bag}' in user_name:
        user_name = user_name.replace('\N{money bag}', '').strip()
        await member.edit(nick=user_name)

    if '\N{crossed swords}' in user_name:
        user_name = user_name.replace('\N{crossed swords}', '').strip()
        await member.edit(nick=user_name)

    if '\N{crown}' in user_name:
        user_name = user_name.replace('\N{crown}', '').strip()
        await member.edit(nick=user_name)

    if '\N{banana}' in user_name:
        user_name = user_name.replace('\N{banana}', '').strip()
        await member.edit(nick=user_name)

    if user_points >= 50 and user_points < 120:
        new_nick = "{0} {1}".format(user_name, '\N{money bag}')
        await member.edit(nick=new_nick)

    elif user_points >= 120 and user_points < 400:
        new_nick = "{0} {1}".format(user_name, '\N{crossed swords}')
        await member.edit(nick=new_nick)

    elif user_points >= 400 and user_points < 1000:
        new_nick = "{0} {1}".format(user_name, '\N{crown}')
        await member.edit(nick=new_nick)

    elif user_points >= 1000:
        new_nick = "{0} {1}".format(user_name, '\N{banana}')
        await member.edit(nick=new_nick)

async def increment_points_wrapper(message):
    """
    This is a wrapper for the function to add points to a discord user.
    :param message: this is a discord message containing all the params to run this function
    :return: a message to print out in discord
    """

    # The message to print out in discord
    return_message = ''
    roles = []
    for role in message.author.roles:
        roles.append(role.name)

    if 'Wight King' not in roles and 'Thrall' not in roles:
        # ah ah ah!
        return 'http://gph.is/15wY87J'

    # split out the various params
    command_params = message.content.split()

    if len(command_params) < 3:
        return "You are missing some parameters. Please see !brian for help on how to use this command."

    if len(command_params) == 3:
        if "-" not in command_params[2]:
            return "You can only use this format of the command to remove points."
    try:
        int(command_params[2])
    except ValueError:
        return 'You need to use an integer when giving a user points.'

    if '@' not in command_params[1] or re.search('[a-zA-Z]', command_params[1]):
        return 'You need to tag a user with this command. Their name should appear blue in discord.'

    if len(command_params) == 3:
        if "-" not in command_params[2]:
            return_message = "You can only use this format of the command to remove points."
            return return_message

        # using the !add command to remove points
        # command = command_params[0]
        # remove non digit characters like !, @, <, or >
        discord_user_id = int(re.sub("\D", "", command_params[1]))
        points = command_params[2]

        conn = sqlite3.connect(database)
        # When we decrement we add a submission with an empty link this entry will be ignored when the person's gallery is grabbed
        add_user_submission(discord_user_id,(None,), points, conn)
        user_points = get_user_points(discord_user_id,conn)
        conn.close
        await set_name(user_points, get_member(discord_user_id), discord_user_id)
        return_message = ":sob: Woops, {}. You now have {} points :sob:".format(get_member(discord_user_id).display_name, user_points)
        return return_message

    elif len(command_params) == 4:
        # using the !add command to actually add points
        # command = command_params[0]
        image_link = command_params[3]
        # remove non digit characters like !, @, <, or >
        discord_user_id = int(re.sub("\D", "", command_params[1]))
        points = command_params[2]
        image_link = command_params[3]

        conn = sqlite3.connect(database)
        before_points = get_user_points(discord_user_id,conn)
        add_user_submission(discord_user_id,image_link, points, conn)
        user_points = before_points + points
        conn.close

        await set_name(user_points, get_member(discord_user_id), discord_user_id)
        if user_points >= 50 and before_points < 50:
            return_message = ":moneybag: HOOTY HOO! You've earned your first emoji. FLEX ON THE HATERS WHO DON'T PAINT! :moneybag:"

        elif user_points >= 120 and before_points < 120:
            return_message = ":crossed_swords: KACAW! You've earned your second emoji. HAIL AND KILL! :crossed_swords:"

        elif user_points >= 400 and before_points < 400:
            return_message = ":crown: SKKKRT! You've earned your third emoji. YOU DA KING :crown:"

        elif user_points >= 1000 and before_points < 1000:
            return_message = ":banana: LORD ALMIGHTY! You've earned your fourth and final emoji. You've ascended to minipainting godhood :banana:"

        else:
            return_message = ":metal:Congratulations, {}. You now have {} points:metal:".format(client.get_guild(miniac_server_id).get_member(discord_user_id).display_name,user_points)

        return return_message

    else:
        return_message = 'You\'re missing a parameter. Please see the !brian documentation'
        return return_message

def get_leaderboard(message):
    discord_message = ''
    conn = sqlite3.connect(database)
    leaderboard = get_sorted_leaderboard(conn)
    conn.close()
    discord_message = '' 
    if not len(leaderboard):
        return '```leaderboard is empty.```'
    else:
        x = 0
        y = 0
        while(x < 10 and y < 20):
            member = client.get_guild(miniac_server_id).get_member(int(leaderboard[y][0]))
            if member:
                x +=1
                discord_message += '{}: {}\n'.format(member.display_name, leaderboard[y][1])
            y +=1
        return '```{}```'.format(discord_message)

def get_points(message):
    conn = sqlite3.connect(database)
    command_params = message.content.split()
    insults = [
            "Looks like you have no points. Time to PAINT MORE MINIS!",
            "0/10 did not enjoy how pretentious you come off when talking about having literally zero points. Nothing you painted has received points since 10 years ago... you know back when you were born.",
            "Those unprimed and unpainted minis won't paint themselves! You have 0 points.",
            "Sucks to suck! You have zero points!",
            "Bro, do you even paint? You have zero points.",
            "Sometimes I think I'm unproductive, and then I remember you exist. You have zero points!",
            "You're beautiful even if you have zero points. I still love you.",
            "I believe in you. In a week you'll be on the board. For now you have zero points, though."
            ]
    if len(command_params) == 1:
        points = get_user_points(conn, message.author.id)
        if int(points):
            return_message = "```{}: {}```".format(message.author.display_name, points)
        else:
            return_message = insults[random.randint(0,7)]

        conn.close()
        return return_message
    elif len(command_params) == 2:
        if '@' not in command_params[1] or re.search('[a-zA-Z]', command_params[1]):
            return_message = 'You need to tag a user with this command. Their name should appear blue in discord.'
            return return_message

        discord_user_id = int(re.sub("\D", "", command_params[1]))
        points = get_user_points(conn, discord_user_id)
        return_message = "```{}: {}```".format(client.get_guild(miniac_server_id).get_member(discord_user_id).display_name, points)
        conn.close()
        return return_message
    else:
        return_message = 'You have one too many parameters. Check !brian for help on how this command works.'
        conn.close()
        return return_message

def get_gallery(message):
    # split out the various params
    command_params = message.content.split()
    if len(command_params) != 2:
        return_message = 'You\'re missing a parameter. Please see the !brian documentation'
        return return_message

    if '@' not in command_params[1]:
        return_message = 'You need to tag a user with this command. Their name should appear blue in discord.'
        return return_message

    # command = command_params[0]
    # remove non digit characters like !, @, <, or >
    discord_user_id = int(re.sub("\D", "", command_params[1]))
    conn = sqlite3.connect(database)
    gallery = get_user_gallery(discord_user_id, conn)
    conn.close()
    discord_private_message = ''
    discord_private_message_list = []
    index = 1
    try:
        for link in gallery:
            if((len(discord_private_message) + len(link[0])) > 2000):
                discord_private_message_list.append(discord_private_message)
                discord_private_message = ""

            discord_private_message += '{}. {}\n'.format(index, link[0])
            index += 1

        # Append the final message that didn't make it to 2k characters
        discord_private_message_list.append(discord_private_message)
    except TypeError:
        discord_private_message_list[0] = "User has no gallery. Harass them to paint some minis!"

    return discord_private_message_list

def brian():
    return_message = """
    Hi, I'm Brian. You can call me Bryguy. I'm your friendly bot companion. Here are the commands you can do: \n
    `!leaderboard`\n
    This returns the current point totals for the top 10 painters on the discord server.\n
    `!gallery [discord_user]`\n
    This private messages you a discord user's personal gallery. These are all the pictures they've gotten points for. Make sure to actually tag the user, their name should appear blue.\n
    `!points [discord_user]`\n
    This command can be run with a parameter or without a parameter. If you want to find someone's point total, run "!points @[name-of-person]". If you want to know your own points, run "!points"\n
    `!7years` \n
    Never do this.\n
    `!add [discord_user] [points] [link]`\n
    Only Wight Kings and Thralls can run this command. This increments your point total by [points], and adds a new image to your gallery.\n
    `!brian`
    This prints this message!
    """
    return return_message

# Custom welcome message
@client.event
async def on_member_join(member):
    print("Recognized that " + member.name + " joined")
    await client.get_channel(miniac_general_channel_id).send('Welcome to the Miniac Discord, {} Make sure to check out the <#537337389400719360> channel for all the information and rules!'.format(member.name))
    print("Sent message about " + member.name + " to #general")

async def boot_non_roles():
        await client.wait_until_ready()
        miniac_server = ''
        keeper_roles = {'Wight King','Patreon','Rythm','Executioner','Zombie','Moose Fanclub','Dark Wizard','Acolyte','Zombie','Sepulchral Guard'}
        for server in client.guilds:
            if server.name == 'Miniac':
                miniac_server = server

        boot = list()
        for member in miniac_server.members:
            roles = set()
            for miniac_role in member.roles:
                roles.add(miniac_role.name)
            if not (keeper_roles & roles):
                boot.append(member)

        while not client.is_closed:
            for person in boot:
                await person.kick()
            await asyncio.sleep(2592000) # task runs once a month

@client.event
async def on_message(message):
    # Find string versions of the name and add them to a list

    if message.content.startswith('!add'):
        discord_message = await increment_points_wrapper(message)
        await message.channel.send( discord_message)
    if message.content == "!submit":
        await message.channel.send( 'Submit your models for points with this form: https://forms.gle/FkvMWfyCVgAZvGLd6')

    if message.content == '!leaderboard':
        discord_message = get_leaderboard(message)
        await message.channel.send(discord_message)

    if message.content.startswith('!gallery'):
        discord_private_message_list = get_gallery(message)
        await message.author.send("{}'s Gallery".format(message.content.split()[1]))
        for discord_message in discord_private_message_list:
            await message.author.send("{}".format(discord_message))

    if message.content == "!7years":
        await message.channel.send( 'https://i.imgur.com/9NYdTDj.gifv')

    if message.content.startswith('!points'):
        await message.channel.send( get_points(message))

    if message.content == "!brian":
        await message.channel.send('{}'.format(brian()))

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
#client.loop.create_task(boot_non_roles())
client.run(TOKEN)
