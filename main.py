import discord
from discord.ext import commands
import random
import asyncio
import aiofiles
import json
from cryptography.fernet import Fernet, InvalidToken
import os

intents = discord.Intents.all()

bot = commands.Bot(command_prefix='!', intents=intents)

cases = {
    'cs:go weapon case': [
        ('AUG | Wings', 'Blue', 350),
        ('MP7 | Skulls', 'Blue', 350),
        ('SG 553 | Ultraviolet', 'Blue', 350),
        ('USP-S | Dark Water', 'Purple', 150),
        ('M4A1-S | Dark Water', 'Purple', 150),
        ('Glock-18 | Dragon Tattoo', 'Purple', 100),
        ('Desert Eagle | Hypnotic', 'Pink', 100),
        ('AK-47 | Case Hardened', 'Pink', 50),
        ('AWP | Lightning Strike', 'Red', 50),
        ('Bayonet | Fade', 'Gold', 10)
    ],
}

def setup():
    if not os.path.exists("encryption_key.txt"):
        with open("encryption_key.txt", "wb") as key_file:
            key = Fernet.generate_key()
            key_file.write(key)
            print("Encryption key file created.")

    if not os.path.exists("simpleDB.json"):
        with open("simpleDB.json", "w") as db_file:
            db_file.write("{}")
            print("simpleDB.json created.")

    if not os.path.exists("registered_users.json"):
        with open("registered_users.json", "w") as users_file:
            users_file.write("[]")
            print("registered_users.json created.")

setup()

with open("encryption_key.txt", "rb") as key_file:
    key = key_file.read()

cipher_suite = Fernet(key)

def load_user_skins():
    try:
        with open("simpleDB.json", "rb") as file:
            encrypted_data = file.read()
            decrypted_data = cipher_suite.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
    except (FileNotFoundError, json.JSONDecodeError, InvalidToken) as e:
        print(f"Error loading user skins: {e}")
        return {}

async def save_user_skins(user_skins):
    async with aiofiles.open("simpleDB.json", "wb") as file:
        encrypted_data = cipher_suite.encrypt(json.dumps(user_skins).encode())
        await file.write(encrypted_data)

async def register_user(user_id):
    registered_users = await load_registered_users()  # Await the coroutine
    registered_users.add(user_id)
    await save_registered_users(registered_users)

async def load_registered_users():
    try:
        async with aiofiles.open("registered_users.json", "r") as file:
            return set(json.loads(await file.read()))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading registered users: {e}")
        return set()


async def save_registered_users(registered_users):
    try:
        async with aiofiles.open("registered_users.json", "w") as file:
            await file.write(json.dumps(list(registered_users)))
    except FileNotFoundError as e:
        print(f"Error saving registered users: {e}")


@bot.event
async def on_message(message):
    if not message.author.bot and message.content.startswith('!'):
        if message.content.startswith('!register'):
            await register_user(message.author.id)
            await message.channel.send(f"You have been successfully registered with ID: {message.author.id}")
        elif message.author.id not in await load_registered_users():
            await message.channel.send("You need to register before using the bot. Use the command !register.")
        else:
            await bot.process_commands(message)

user_skins = load_user_skins()

@bot.event
async def on_message(message):
    if not message.author.bot and message.content.startswith('!'):
        if message.content.startswith('!register'):
            await register_user(message.author.id)
            reg_message = await message.channel.send(f"You have been successfully registered with ID: {message.author.id}")
            await asyncio.sleep(5)  # Wait for 5 seconds
            await reg_message.delete()  # Delete the registration message after 5 seconds
        elif message.author.id not in await load_registered_users():
            await message.channel.send("You need to register before using the bot. Use the command !register.")
        else:
            await bot.process_commands(message)


@bot.command()
async def open(ctx, *, case_name: str):
    case_name = case_name.lower()
    if case_name in cases:
        await ctx.send(f'You opened a {case_name.title()}.')

        skins = cases[case_name]

        random.shuffle(skins)

        selected_skin = None
        total_odds = sum(odds for _, _, odds in skins)
        rand = random.randint(1, total_odds)
        for skin, rarity, odds in skins:
            rand -= odds
            if rand <= 0:
                selected_skin = skin
                rarity_emoji = rarity
                break

        user_id = str(ctx.author.id)
        if user_id not in user_skins:
            user_skins[user_id] = []
        user_skins[user_id].append(selected_skin)
        await save_user_skins(user_skins)

        await ctx.send(f'You got: {selected_skin} Rarity = {rarity_emoji}')
    else:
        await ctx.send('Invalid case name')

@bot.command()
async def skins(ctx):
    user_id = str(ctx.author.id)
    if user_id in user_skins:
        skins_list = '\n'.join(user_skins[user_id])
        await ctx.send(f'Your skins:\n{skins_list}')
    else:
        await ctx.send('You have not opened any skins yet.')

@bot.command()
async def showskins(ctx, *, case_name: str):
    case_name = case_name.lower()
    if case_name in cases:
        skins = cases[case_name]

        sorted_skins = sorted(skins, key=lambda x: ('Blue', 'Purple', 'Pink', 'Red', 'Gold').index(x[1]))

        skins_list = '\n'.join([f'{skin} Rarity = {rarity}' for skin, rarity, _ in sorted_skins])

        await ctx.send(f'Skins in {case_name.title()} (ordered by rarity):\n{skins_list}')
    else:
        await ctx.send('Invalid case name')

bot.run('')
