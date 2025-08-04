import discord
from discord.ext import commands
import logging
import csv
import os
from dotenv import load_dotenv
from datetime import datetime
from PIL import Image
import pytesseract
import pdfplumber
from pdf2image import convert_from_path
import docx
from deep_translator import GoogleTranslator
import ollama
import asyncio


# Optional: Set tesseract path if on Windows
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Load ENV
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Logging
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Bot setup
bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command('help')  # <-- Remove the default help command




# Invite cache
invite_cache = {}

# Resume file tracking (add this 👇)
user_resume_files = {}

# CSV functions
def load_contacts():
    with open("contacts.csv", newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def save_contacts(contacts):
    with open("contacts.csv", "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["name", "email", "type", "status", "last_sent"])
        writer.writeheader()
        writer.writerows(contacts)

def match_contact(name, contacts):
    for contact in contacts:
        if contact['status'].lower() != 'joined' and contact['name'].lower() in name.lower():
            return contact
    return None

# Translate
def translate(text, target_lang='en', source_lang='auto'):
    return GoogleTranslator(source=source_lang, target=target_lang).translate(text)

# Ask LLM
def ask_llm(prompt, image_paths=None):
    try:
        messages = [{"role": "user", "content": prompt}]
        if image_paths:
            messages[0]["images"] = image_paths
        response = ollama.chat(model='llava:7b', messages=messages)
        return response['message']['content'] if 'message' in response else "⚠️ LLM response error."
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Extract text from any file
def extract_text_from_file(file_path):
    ext = os.path.splitext(file_path)[-1].lower()
    try:
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()

        elif ext == '.pdf':
            text = ''
            # Try digital text extraction first
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ''
            # Fallback to OCR if needed
            if not text.strip():
                images = convert_from_path(file_path)
                for img in images:
                    text += pytesseract.image_to_string(img)
            return text

        elif ext == '.docx':
            doc = docx.Document(file_path)
            return '\n'.join(p.text for p in doc.paragraphs)

        elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
            return pytesseract.image_to_string(Image.open(file_path))

        else:
            return "❌ Unsupported file format."

    except Exception as e:
        return f"❌ Error extracting text: {str(e)}"

# Events
@bot.event
async def on_ready():
    print(f"✅ Bot is ready as {bot.user.name}")
    for guild in bot.guilds:
        invites = await guild.invites()
        invite_cache[guild.id] = {invite.code: invite.uses for invite in invites}

@bot.event
async def on_member_join(member):
    print(f"[JOIN] {member.name} has joined.")

    general_channel = discord.utils.get(member.guild.text_channels, name='general')
    college_channel = discord.utils.get(member.guild.text_channels, name='college-community')
    alumni_channel = discord.utils.get(member.guild.text_channels, name='alumni-requests')

    if general_channel:
        await general_channel.send(
            f"🎉 Welcome {member.mention} to **CareerMate Discord of Kongunadu College of Engineering and Technology**!\n\n"
            f"👉 Type `!help` to see all available commands and get started.\n"
    )


    if college_channel:
        await college_channel.send(f"🎉 Welcome {member.mention} to **CareerMate Discord of Kongunadu College of Engineering and Technology**!"
                                   f"👉 Type `!help` to see all available commands and get started.\n")

    # Invite tracking
    guild = member.guild
    try:
        new_invites = await guild.invites()
        old_invites = invite_cache.get(guild.id, {})
        used_invite = None
        for invite in new_invites:
            if invite.code in old_invites and invite.uses > old_invites[invite.code]:
                used_invite = invite
                break
        invite_cache[guild.id] = {invite.code: invite.uses for invite in new_invites}
    except Exception as e:
        print(f"[ERROR] Failed to check invites: {e}")

    # CSV Update and Role Detection
    contacts = load_contacts()
    matched = match_contact(member.name, contacts)
    user_type = None
    if matched:
        matched['status'] = 'joined'
        save_contacts(contacts)
        print(f"✅ CSV updated for {matched['name']}")
        user_type = matched.get('type', '').lower()
    else:
        print(f"ℹ️ No match found for {member.name}")
        return  # Don't proceed if no match found

    # If the user is staff, do nothing further
    if user_type == 'staff':
        print(f"👩‍🏫 {member.name} is staff, skipping career questions.")
        return

    # Proceed only for students or alumni

    if user_type in ['student', 'alumni']:
        await asyncio.sleep(10)
        if not college_channel:
            print("❌ college-community channel not found.")
            return

        try:
            await college_channel.send(
                f"👋 {member.mention}, would you like to apply for an **internship** or a **job**?\nPlease reply with `internship` or `job`."
            )

            def check_type(m):
                return m.author == member and m.channel == college_channel and m.content.lower() in ['internship', 'job']

            try:
                type_msg = await bot.wait_for('message', timeout=60, check=check_type)
                choice = type_msg.content.lower()

                await college_channel.send(
                    f"📄 Great! Please upload your resume as a file (PDF, DOCX, or image), or type your preferred **job role** (e.g., Web Developer, Data Analyst).\nYou have 60 seconds..."
                )

                def resume_or_role_check(m):
                    return m.author == member and m.channel == college_channel

                try:
                    msg = await bot.wait_for('message', timeout=60, check=resume_or_role_check)

                    if msg.attachments:
                        attachment = msg.attachments[0]
                        file_path = f"./temp/{attachment.filename}"
                        os.makedirs("temp", exist_ok=True)
                        await attachment.save(file_path)

                        text = extract_text_from_file(file_path)
                        if not text.strip():
                            await college_channel.send("⚠️ Could not extract text from the resume.")
                            return

                        # Use LLM to extract role
                        prompt = (
                            "From the resume text below, list only the **single most suitable job role** for this user. "
                            "Return just the role name, no extra explanation.\n\n"
                            f"Resume:\n{text[:3000]}"
                        )
                        role_response = ask_llm(prompt)
                        role = role_response.strip().split("\n")[0]

                    else:
                        role = msg.content.strip().title()

                    # Continue with alumni and fallback
                    await college_channel.send(
                        f"🎯 Role selected: **{role}**\n"
                        f"📢 Let me check with alumni for a {choice} in this role..."
                    )

                    if alumni_channel:
                        await alumni_channel.send(
                            f"📢 {member.name} is looking for a **{choice}** opportunity as a **{role}**.\n"
                            f"Please respond here if you can help or refer!"
                        )

                        def alum_check(m):
                            return m.channel == alumni_channel and m.author != bot.user

                        try:
                            response_msg = await bot.wait_for('message', timeout=60, check=alum_check)
                            await college_channel.send(
                                f"📬 {member.mention}, alumni responded:\n> {response_msg.content}"
                            )
                        except asyncio.TimeoutError:
                            # Role-specific job/internship fallback links
                            role_query = role.replace(" ", "+")
                            await college_channel.send(
                                f"🕐 {member.mention}, no alumni has responded yet.\n\n"
                                f"Here are some great resources for finding **{role} {choice}s**:\n\n"
                                f"🔗 [Internshala - {role}](https://internshala.com/internships/{role_query}-internship)\n"
                                f"🔗 [LinkedIn - {role}](https://www.linkedin.com/jobs/search/?keywords={role_query})\n"
                                f"🔗 [Indeed - {role}](https://in.indeed.com/jobs?q={role_query})\n"
                                f"🔗 [LetsIntern - {role}](https://www.letsintern.com/{role_query}-internships)\n\n"
                                f"Good luck! 🚀💼"
                            )

                except asyncio.TimeoutError:
                    await college_channel.send(
                        f"⌛ {member.mention}, no resume or role was received in time. You can try again later!"
                    )

            except asyncio.TimeoutError:
                await college_channel.send(
                    f"⌛ {member.mention}, you didn’t reply. If you’re interested in jobs or internships, just type it anytime!"
                )

        except Exception as e:
            print(f"[ERROR] While processing career questions: {e}")



@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    await bot.process_commands(message)  # To ensure commands still work

    # Only listen in college-community channel
    if message.channel.name == "college-community":
        content = message.content.lower()

        if "apply" in content and ("internship" in content or "job" in content):
            college_channel = message.channel
            member = message.author
            choice = "internship" if "internship" in content else "job"
            alumni_channel = discord.utils.get(message.guild.text_channels, name='alumni-requests')

            await college_channel.send(
                f"👋 {member.mention}, please upload your **resume** (PDF, DOCX, or image), "
                f"**or** type your preferred role (e.g., Web Developer, AI Engineer)."
            )

            def resume_or_role_check(m):
                return m.author == member and m.channel == college_channel

            try:
                msg = await bot.wait_for('message', timeout=60, check=resume_or_role_check)

                if msg.attachments:
                    attachment = msg.attachments[0]
                    file_path = f"./temp/{attachment.filename}"
                    os.makedirs("temp", exist_ok=True)
                    await attachment.save(file_path)

                    text = extract_text_from_file(file_path)
                    if not text.strip():
                        await college_channel.send("⚠️ Could not extract text from the resume.")
                        return

                    # Extract role using LLM
                    prompt = (
                        "From the resume text below, list only the **single most suitable job role** for this user. "
                        "Return just the role name, no extra explanation.\n\n"
                        f"Resume:\n{text[:3000]}"
                    )
                    role_response = ask_llm(prompt)
                    role = role_response.strip().split("\n")[0]

                else:
                    role = msg.content.strip().title()

                # Share with alumni
                await college_channel.send(
                    f"🎯 Role selected: **{role}**\n"
                    f"📢 Let me check with alumni for a {choice} in this role..."
                )

                if alumni_channel:
                    await alumni_channel.send(
                        f"📢 {member.name} is looking for a **{choice}** opportunity as a **{role}**.\n"
                        f"Please respond here if you can help or refer!"
                    )

                    def alum_check(m):
                        return m.channel == alumni_channel and m.author != bot.user

                    try:
                        response_msg = await bot.wait_for('message', timeout=60, check=alum_check)
                        await college_channel.send(
                            f"📬 {member.mention}, alumni **{response_msg.author.name}** replied:\n> {response_msg.content}"
                        )
                    except asyncio.TimeoutError:
                        role_query = role.replace(" ", "+")
                        await college_channel.send(
                            f"🕐 {member.mention}, no alumni has responded yet.\n\n"
                            f"Here are some role-specific **{choice}** opportunities:\n"
                            f"🔗 [Internshala - {role}](https://internshala.com/internships/{role_query}-internship)\n"
                            f"🔗 [LinkedIn - {role}](https://www.linkedin.com/jobs/search/?keywords={role_query})\n"
                            f"🔗 [Indeed - {role}](https://in.indeed.com/jobs?q={role_query})\n"
                            f"🔗 [LetsIntern - {role}](https://www.letsintern.com/{role_query}-internships)\n"
                            f"Good luck! 💼"
                        )

            except asyncio.TimeoutError:
                await college_channel.send("⌛ Time's up! No resume or role received.")



@bot.command()
async def hello(ctx):
    await ctx.send(f"👋 Hello, {ctx.author.mention}! I'm your CareerMate bot.")

@bot.command()
async def hi(ctx):
    await ctx.send(f"👋 Hi, {ctx.author.mention}! I'm your CareerMate bot.")

@bot.command()
async def hii(ctx):
    await ctx.send(f"👋 Hii, {ctx.author.mention}! I'm your CareerMate bot.")

@bot.command()
async def hey(ctx):
    await ctx.send(f"👋 Hello, {ctx.author.mention}! I'm your CareerMate bot.")

@bot.command()
async def invite(ctx):
    await ctx.send("📩 Here’s your invite link: https://discord.gg/fB93Rv2g")

@bot.command()
async def status(ctx):
    contacts = load_contacts()
    total = len(contacts)
    joined = sum(1 for c in contacts if c['status'].lower() == 'joined')
    pending = total - joined
    await ctx.send(f"📊 Status:\n👥 Total: {total}\n✅ Joined: {joined}\n⏳ Pending: {pending}")

@bot.command()
async def help(ctx):
    help_message = (
        f"👋 **Welcome to CareerMate Discord Help Menu**\n\n"
        f"📌 **Available Commands:**\n"
        f"• `!hello` – Greet the bot 👋\n"
        f"• `!hii` – Greet the bot 👋\n"
        f"• `!bot` – Ask any question to bot \n"
        f"• `want to apply for internship/job` – internship/job 👋\n"
        f"• `!resume` – Upload your resume for AI review and suggestions 💼\n"
        f"• `!bot role` – Get a job/internship role recommendation from your resume 🔍\n"
        f"• `!help` – Show this help menu ℹ️\n\n"
    )
    await ctx.send(help_message)



@bot.command(name='bot')
async def bot_command(ctx, *, message: str = ""):
    # General chatbot conversation only
    prompt = translate(message, 'en')
    response = ask_llm(prompt)

    if len(response) <= 2000:
        await ctx.send(f"🧠 CareerMate:\n{response}")
    else:
        with open("response.txt", "w", encoding='utf-8') as f:
            f.write(response)
        await ctx.send("📎 Response too long, see file:", file=discord.File("response.txt"))
        os.remove("response.txt")


import os
import json
import discord
from discord.ext import commands

# Dictionary to store user's uploaded resume paths
user_resume_files = {}

@bot.command()
async def askfile(ctx):
    if not ctx.message.attachments:
        await ctx.send("📎 Please attach a file!")
        return

    attachment = ctx.message.attachments[0]
    file_path = f"./temp/{attachment.filename}"
    os.makedirs("temp", exist_ok=True)
    await attachment.save(file_path)

    if not file_path.lower().endswith(('.pdf', '.docx', '.png', '.jpg', '.jpeg')):
        await ctx.send("⚠️ Only .pdf, .docx, or image files are supported.")
        os.remove(file_path)
        return

    text = extract_text_from_file(file_path)
    if not text.strip():
        await ctx.send("⚠️ Could not extract text from the file.")
        os.remove(file_path)
        return

    prompt = translate(text)
    response = ask_llm(prompt)

    if len(response) <= 2000:
        await ctx.send(f"🧠 CareerMate:\n{response}")
    else:
        with open("file_response.txt", "w", encoding='utf-8') as f:
            f.write(response)
        await ctx.send("📎 Response too long, see file:", file=discord.File("file_response.txt"))
        os.remove("file_response.txt")

    os.remove(file_path)


@bot.command(name="resume-role")
async def resume_role(ctx):
    if ctx.channel.name in ['resume_analyser', 'college-community']:
        await ctx.typing()
        attachment = ctx.message.attachments[0] if ctx.message.attachments else None
        os.makedirs("resumes", exist_ok=True)

        if attachment:
            file_name = f"{ctx.author.id}_{attachment.filename}"
            file_path = os.path.join("resumes", file_name)
            await attachment.save(file_path)

            if not file_path.lower().endswith(('.pdf', '.docx', '.png', '.jpg', '.jpeg')):
                await ctx.send("⚠️ Only .pdf, .docx, or image files are supported.")
                os.remove(file_path)
                return

            user_resume_files[ctx.author.id] = file_path
        elif ctx.author.id in user_resume_files:
            file_path = user_resume_files[ctx.author.id]
        else:
            await ctx.send("📎 Please upload your resume as a file attachment when using `!resume-role`.")
            return

        text = extract_text_from_file(file_path)
        if not text.strip():
            await ctx.send("⚠️ Couldn't extract content from your resume.")
            return

        prompt = (
            "From the resume text below, list 3 to 5 most suitable job roles for this user. "
            "Return the roles as a comma-separated list only, without any explanation.\n\n"
            f"Resume:\n{text[:3000]}"
        )
        try:
            response = ask_llm(prompt)
            roles = [r.strip() for r in response.split(",") if r.strip()]
            if not roles:
                await ctx.send("⚠️ No roles identified from the resume.")
                return

            formatted_roles = "\n".join(f"🔹 {role}" for role in roles)
            await ctx.send(f"🎯 **Top Recommended Roles for You, {ctx.author.mention}:**\n{formatted_roles}")
        except Exception as e:
            await ctx.send(f"⚠️ Error while processing the resume: `{e}`")


@bot.command()
async def resume(ctx):
    if ctx.channel.name in ['resume_analyser', 'college-community']:
        if not ctx.message.attachments:
            await ctx.send("📎 Please attach a resume (.pdf, .docx, or image)!")
            return

        attachment = ctx.message.attachments[0]
        file_path = f"./temp/{attachment.filename}"

        # File extension check
        if not file_path.lower().endswith(('.pdf', '.docx', '.png', '.jpg', '.jpeg')):
            await ctx.send("⚠️ Only .pdf, .docx, or image files are supported.")
            return

        os.makedirs("temp", exist_ok=True)
        await attachment.save(file_path)

        async with ctx.typing():
            text = extract_text_from_file(file_path)
            if not text.strip():
                await ctx.send("⚠️ Could not extract text from the resume.")
                os.remove(file_path)
                return

            prompt = f"""
You are a professional resume reviewer.

Analyze the resume below and provide:

1. Score (0–100) for each section:
   - Objective
   - Experience
   - Projects
   - Skills
   - Education
   - Certifications

2. Overall Score (0–100)

3. Best Recommended Role (1 job title only)

4. Key Strengths (3 bullet points)

5. Key Weaknesses (3 bullet points)

6. Suggestions to improve each section

Resume:
{text[:3000]}
"""

            try:
                result = ask_llm(prompt)

                await ctx.send(f"📄 **Resume Review for `{ctx.author.name}`**\n\n{result}")
                await ctx.message.add_reaction("✅")

            except Exception as e:
                await ctx.send(f"⚠️ Error analyzing resume: {e}")

            finally:
                os.remove(file_path)


# Run the bot
bot.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)
