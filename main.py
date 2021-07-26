# coding: utf8

import discord
from discord.ext import commands
import sys
import os
from dotenv import load_dotenv
import shutil
from datetime import datetime

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from psup_dataclasses import *

intents = discord.Intents.all()
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)
console = sys.stdout


def get_session(user_id):
    course_file_name = "datas/"+str(user_id)+"/courses.csv"
    event_file_name = "datas/"+str(user_id)+"/events.csv"
    session = Session(course_file_name, event_file_name)
    session.read()
    return session


def get_plot(user_id, courses):

    plt.close()
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    for course in courses:
        points = []
        for event in course.events:
            if event.kind == "Waiting":
                x = event.date
                y = int(event.place)
                points.append([x, y])
        points.sort(key=lambda x:x[0])
        x = [point[0] for point in points]
        y = [point[1] for point in points]
        ax.plot(x, y, label=course.name)

    # naming the x axis
    plt.xlabel('Date and time')
    # naming the y axis
    plt.ylabel('Place')
    xfmt = mdates.DateFormatter('%d-%m-%y %H:%M')
    ax.xaxis.set_major_formatter(xfmt)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(2))

    y_min, y_max = plt.ylim()
    ax.set_ylim(0, y_max)

    ax.legend()
    # giving a title to my graph
    plt.title("Waiting plot of "+ ", ".join([course.name for course in courses]))
    plt_file_name = "datas/"+str(user_id)+"/plot.png"
    # function to show the plot
    plt.savefig(plt_file_name)

    return plt_file_name


async def get_course(ctx, session, page=0):
    user_id = ctx.author.id
    embed = discord.Embed(title="Chose your course")
    courses_names_list = list(session.courses.keys())
    choice_emojies = {}
    for index in range(min(len(courses_names_list), 10*(page+1))-10*page):
        embed.add_field(name=reactions_order[index], value=courses_names_list[9*page+index], inline=False)
        choice_emojies[reactions_order[index]] = index
    send_embed = await ctx.send(embed=embed)

    for emoji in choice_emojies.keys():
        await send_embed.add_reaction(emoji)
    if page > 0:
        await send_embed.add_reaction(reactions_order["previous"])
        choice_emojies[reactions_order["previous"]] = "previous"
    if page < (len(courses_names_list)-1)//10:
        await send_embed.add_reaction(reactions_order["next"])
        choice_emojies[reactions_order["next"]] = "next"
    await send_embed.add_reaction(reactions_order["close"])
    choice_emojies[reactions_order["close"]] = "close"

    def check(reaction, user):
        return user.id == user_id and reaction.emoji in choice_emojies

    reaction, user = await bot.wait_for('reaction_add', check=check)
    command = choice_emojies[reaction.emoji]

    if type(command) == int:
        return courses_names_list[9*page+command]
    elif command == "next":
        return await get_course(ctx, session, page + 1)
    elif command == "previous":
        return await get_course(ctx, session, page - 1)
    elif command == "close":
        return None
    else:
        raise ValueError('Unknown command after embed course choice')


async def get_date(ctx):
    def check(m):
        return m.author.id == user_id
    user_id = ctx.author.id

    await ctx.channel.send("Send the date. Use the format like this : 27-05-2021")
    date_message = await bot.wait_for('message', check=check)
    str_date = date_message.content
    try:
        day, month, year = map(int,str_date.split("-"))
    except:
        await ctx.channel.send("Wrong date format")
        return await get_date(ctx)

    await ctx.channel.send("Send the hour. Use the format like this : 18:30:00")
    hour_message = await bot.wait_for('message', check=check)
    str_hour = hour_message.content
    try:
        hour, minute, second = map(int,str_hour.split(":"))
    except:
        await ctx.channel.send("Wrong hour format")
        return await get_date(ctx)
    try:
        date = datetime(year, month, day, hour, minute, second)
    except:
        await ctx.channel.send("Wrong datetime format")
        return await get_date(ctx)

    return date


async def get_type(ctx):
    user_id = ctx.author.id
    embed = discord.Embed(title="Chose your course")
    event_type_list = list(all_event_kinds.keys())
    choice_emojies = {}
    for index in range(len(all_event_kinds)):
        embed.add_field(name=reactions_order[index], value=event_type_list[index], inline=False)
        choice_emojies[reactions_order[index]] = index
    send_embed = await ctx.send(embed=embed)

    for emoji in choice_emojies.keys():
        await send_embed.add_reaction(emoji)

    def check(reaction, user):
        return user.id == user_id and reaction.emoji in choice_emojies

    reaction, user = await bot.wait_for('reaction_add', check=check)
    command = choice_emojies[reaction.emoji]
    return all_event_kinds[event_type_list[command]]


async def get_place(ctx):
    def check(m):
        return m.author.id == user_id

    user_id = ctx.author.id

    await ctx.channel.send("What is your actual rank ?")
    rank_message = await bot.wait_for('message', check=check)
    try:
        rank = int(rank_message.content)
    except:
        await ctx.channel.send("Please send an integer")
        return await get_place(ctx)
    return rank


# detecter l'allumage du bot
@bot.event
async def on_ready():
    print("Successfully connected !")
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(".help"))


#commande test
@bot.command()
async def ping(ctx):
    """
    A small command to see if the bot is alive
    """
    await ctx.send("pong")


@bot.command()
async def register(ctx):
    """
    The command to create your account
    """
    user_id_str = str(ctx.author.id)
    if os.path.exists("datas/"+user_id_str):
        await ctx.channel.send("You are already registered")
    else:

        def check(m):
            return  str(m.author.id) == user_id_str

        await ctx.channel.send("Vos données ne seront pas anonymes. Elles seront conservées jusqu'à votre désinscrption.\n"
                               "Si vous êtes d'accord avec ces conditions, écrivez \"yes\".")
        confirmation = await bot.wait_for('message', check=check)
        if confirmation.content == "yes":
            os.makedirs("datas/"+user_id_str)
            with open("datas/"+user_id_str+"/courses.csv", "x") as courses_file:
                pass
            with open("datas/"+user_id_str+"/events.csv", "x") as events_file:
                pass
            await ctx.channel.send("You successfully registered !")
        else:
            await ctx.channel.send("You refused the register")


@bot.command()
async def delete_account(ctx):
    """
    Command to delete all your personal informations.
    Be sure you saved them. They will be permanently lost.
    """
    # TODO : Add a confirmation message
    user_id_str = str(ctx.author.id)
    if os.path.exists("datas/"+user_id_str):
        shutil.rmtree("datas/"+user_id_str)
        await ctx.channel.send("You successfully deleted your account")
    else:
        await ctx.channel.send("You are not registered yet")


@bot.command()
async def add_course(ctx, course_name, places_available, previous_last_entry):
    """
    Command to add a new course. Enter the course name (no space), the number of places available and the rank of the last entry last year.
    Ex : .add_course Orsay_MI 180 1240
    """
    # TODO : Split the entries in separate messages
    user_id = ctx.author.id
    user_session = get_session(user_id)

    course_selectivity = Selectivity(places_available, previous_last_entry)
    new_course = Course(course_name, course_selectivity)
    return_code = user_session.add_course(new_course)

    if return_code:
        with open("datas/"+str(user_id)+"/courses.csv", 'a') as courses_file:
            courses_file.write(str(new_course)+"\n")
        await ctx.channel.send(course_name+" a été ajouté avec succès")
    else:
        await ctx.channel.send(course_name+" existe déjà")


@bot.command()
async def add_event(ctx, course_name=None, date=None, event_kind=None, place=None):
    """
    Command to add a new event.
    Enter the course name, the date (ISO format), the event kind and if necessary, the place related.
    Possible events : Accepted, UserRefused, SchoolRefused, Waiting, Proposition
    Date format : YYYY-MM-DDTHH:MM:SS
    Ex : .add_event Orsay_MI 2021-06-27T19:30:00 Waiting 285
    Ex : .add_event
    """
    user_id = ctx.author.id
    user_session = get_session(user_id)

    # GET THE COURSE NAME
    if course_name in user_session.courses:
        course = user_session.courses[course_name]
    else:
        course_name = await get_course(ctx, user_session)
        if not course_name:
            await ctx.channel.send("Command canceled")
            return -1
        course = user_session.courses[course_name]

    # GET THE DATE
    if date:
        try:
            date = datetime.fromisoformat(date)
        except ValueError:
            await ctx.channel.send("Invalid format string. Next time use the ISO format YYYY-MM-DDTHH:MM:SS. "
                                   "Now let's enter the date manually")
            date = await get_date(ctx)

    else:
        date = await get_date(ctx)

    # GET THE EVENT TYPE
    if event_kind:
        event_type = all_event_kinds[event_kind]
    else:
        event_type = await get_type(ctx)

    # CREATE THE EVENT
    if event_type == WaitingListEvent:
        if place:
            try:
                place = int(place)
            except:
                await ctx.channel.send("Please send an integer")
                place = await get_place(ctx)
        else:
            place = await get_place(ctx)

        new_event = WaitingListEvent(date, course, place)
        course.add_event(new_event)
    else:
        new_event = event_type(date, course)
        course.add_event(new_event)

    with open("datas/"+str(user_id)+"/events.csv", 'a') as events_file:
        events_file.write(str(new_event)+"\n")
    await ctx.channel.send("The new event was successfully added")


@bot.command()
async def my_files(ctx):
    """
    Sends your information files. You can then download them.
    """
    user_id = ctx.author.id
    courses_file = "datas/"+str(user_id)+"/courses.csv"
    events_file ="datas/"+str(user_id)+"/events.csv"
    await ctx.channel.send("The courses file :", file=discord.File(courses_file, filename=ctx.author.name+"courses.csv"))
    await ctx.channel.send("The events file :", file=discord.File(events_file, filename=ctx.author.name+"events.csv"))


@bot.command()
async def plot(ctx, *courses):
    """
    Plots your waiting lists informations. Send the name of the courses you want to see on the graph, or leave blank to see them all
    Ex : .plot
    Ex : .plot Orsay_MI
    """
    user_id = ctx.author.id
    user_session =get_session(user_id)
    courses = list(courses)
    if not courses:
        courses = list(user_session.courses.values())
    else:
        for i in range(len(courses)):
            if courses[i] in user_session.courses:
                courses[i] = user_session.courses[courses[i]]
            else:
                await ctx.channel.send(courses[i]+" has not been found")
                courses[i] = None
    plot_file_name = get_plot(user_id, courses)

    await ctx.channel.send(file=discord.File(plot_file_name))
    os.remove(plot_file_name)


@bot.command()
async def upload(ctx):
    def check(m):
        return m.author.id == user_id
    user_id = ctx.author.id
    await ctx.channel.send("You are about to upload your own files.\n "
                           "Please consider checking them so that they have no errors.\n"
                           "This command will result on the suppresion of your old files. "
                           "If you want to downloaw them, please type .myfiles\n"
                           "If you agree with this, type \"yes\"")

    confirmation = await bot.wait_for('message', check=check)
    if confirmation.content == "yes":
        await ctx.channel.send("Send the courses file")

        confirmation = await bot.wait_for('message', check=check)
        if len(confirmation.attachments) == 1:
            await confirmation.attachments[0].save("datas/"+str(user_id)+"/courses.csv")

        await ctx.channel.send("Send the events file")

        confirmation = await bot.wait_for('message', check=check)
        if len(confirmation.attachments) == 1:
            await confirmation.attachments[0].save("datas/" + str(user_id) + "/events.csv")
    else:
        await ctx.channel.send("Command canceled")


load_dotenv()
token = os.getenv('PSUP-BOT-TOKEN')

bot.run(token)