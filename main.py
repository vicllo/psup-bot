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
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))

    ax.legend()
    # giving a title to my graph
    plt.title("Waiting plot of "+ ", ".join([course.name for course in courses]))
    plt_file_name = "datas/"+str(user_id)+"/plot.png"
    # function to show the plot
    plt.savefig(plt_file_name)

    return plt_file_name


# detecter l'allumage du bot
@bot.event
async def on_ready():
    print("Successfully connected !")
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(".help"))
    serv = bot.get_guild(748924322734932078)
    canal = serv.get_channel(748924322734932082)
    #await canal.send("Salut Martin")


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
async def add_event(ctx, course_name, date, event_type, place=-1):
    """
    Command to add a new event. Enter the course name related to the event, the date (ISO format), the event kind and, if necessary, the place related.
    Possible events : Accepted, UserRefused, SchoolRefused, Waiting, Proposition
    Date format : YYYY-MM-DDTHH:MM:SS
    Ex : .add_event Orsay_MI 2021-06-27T19:30:00 Waiting 285
    """
    # TODO : Split the entries in separate messages
    user_id = ctx.author.id
    user_session = get_session(user_id)
    try:
        course = user_session.courses[course_name]
    except KeyError:
        await ctx.channel.send("Course not found. Please add the course")
        raise KeyError
    try:
        date = datetime.fromisoformat(date)
    except ValueError:
        await ctx.channel.send("Invalid format string. Use the ISO format YYYY-MM-DDTHH:MM:SS")
        raise ValueError
    place = int(place)
    if event_type == "Waiting":
        new_event = WaitingListEvent(date, course, place)
        course.add_event(new_event)
    else:
        new_event = all_event_kinds[event_type](date, course)
        course.add_event(new_event)

    with open("datas/"+str(user_id)+"/events.csv", 'a') as events_file:
        events_file.write(str(new_event)+"\n")
    await ctx.channel.send("Le nouvel évènement a été ajouté avec succès")


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
                await ctx.channel.send(courses[i]+" n'a pas été trouvé")
                courses[i] = None
    plot_file_name = get_plot(user_id, courses)

    await ctx.channel.send(file=discord.File(plot_file_name))
    os.remove(plot_file_name)

load_dotenv()
token = os.getenv('PSUP-BOT-TOKEN')

bot.run(token)

