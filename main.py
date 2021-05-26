# coding: utf8

import discord
from discord.ext import commands
import sys
import os
from dotenv import load_dotenv
import shutil
from datetime import datetime
import matplotlib.pyplot as plt

from psup_dataclasses import *

intents = discord.Intents.all()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
console = sys.stdout


def get_session(user_id):
    course_file_name = "datas/"+str(user_id)+"/courses.csv"
    event_file_name = "datas/"+str(user_id)+"/events.csv"
    session = Session(course_file_name, event_file_name)
    session.read()
    return session


def get_plot(user_id, courses):
    # x axis values
    x = [1, 2, 3]
    # corresponding y axis values
    y = [2, 4, 1]

    # plotting the points
    plt.plot(x, y)

    # naming the x axis
    plt.xlabel('x - axis')
    # naming the y axis
    plt.ylabel('y - axis')

    # giving a title to my graph
    plt.title('My first graph!')
    plt_file_name = "datas/"+str(user_id)+"/plot.png"
    # function to show the plot
    plt.savefig(plt_file_name)

    return plt_file_name

# detecter l'allumage du bot
@bot.event
async def on_ready():
    # TODO : Bot status
    print("Ready !")


#commande test
@bot.command()
async def ping(ctx):
    """
    A small command to see if the bot is alive
    """
    await ctx.send("pong")


@bot.command()
async def register(ctx):
    user_id_str = str(ctx.author.id)
    if os.path.exists("datas/"+user_id_str):
        await ctx.channel.send("You are already registered")
    else:
        os.makedirs("datas/"+user_id_str)
        with open("datas/"+user_id_str+"/courses.csv", "x") as courses_file:
            pass
        with open("datas/"+user_id_str+"/events.csv", "x") as events_file:
            pass
        await ctx.channel.send("You successfully registered !")


@bot.command()
async def delete_account(ctx):
    # TODO : Add a confirmation message
    user_id_str = str(ctx.author.id)
    if os.path.exists("datas/"+user_id_str):
        shutil.rmtree("datas/"+user_id_str)
        await ctx.channel.send("You successfully deleted your account")
    else:
        await ctx.channel.send("You are not registered yet")


@bot.command()
async def add_course(ctx, course_name, places_available, previous_last_entry):
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
    # TODO : Split the entries in separate messages
    user_id = ctx.author.id
    user_session = get_session(user_id)
    course = user_session.courses[course_name]
    date = datetime.fromisoformat(date)
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
    user_id = ctx.author.id
    courses_file = "datas/"+str(user_id)+"/courses.csv"
    events_file ="datas/"+str(user_id)+"/events.csv"
    await ctx.channel.send("The courses file :", file=discord.File(courses_file, filename=ctx.author.name+"courses.csv"))
    await ctx.channel.send("The events file :", file=discord.File(events_file, filename=ctx.author.name+"events.csv"))


@bot.command()
async def plot(ctx, *courses):
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

load_dotenv()
token = os.getenv('PSUP-BOT-TOKEN')

bot.run(token)

