# coding: utf8

import discord
from discord.ext import commands
import sys
import os
from dotenv import load_dotenv
import shutil

from dataclasses import *

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


load_dotenv()
token = os.getenv('PSUP-BOT-TOKEN')

bot.run(token)

