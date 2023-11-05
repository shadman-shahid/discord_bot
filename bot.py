import dotenv
import os
from urllib.parse import urlparse, parse_qs
import re

import discord
from discord.interactions import Interaction
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

"""Google drive authorization"""
## Uses authentication settings in 'settings.yaml'.
gauth = GoogleAuth()

## Authenticate via web browser
# gauth.LocalWebserverAuth()  # Uses client_secrets.json file. 

## Authenticate a service account
gauth.ServiceAuth()

drive = GoogleDrive(gauth)


"""Discord bot authorization"""
dotenv.load_dotenv()
token = str(os.getenv("TOKEN"))

"""Discord bot client"""
bot = discord.Bot()


@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")


async def get_assignment(user, assignment_no, drive_link, ctx=None, interaction=None):
    async def send_message(*args, **kwargs):
        if ctx:
            await ctx.followup.send(*args, **kwargs)
        else:
            await interaction.response.send_message(*args, **kwargs)

    """Extract the file names and google drive links of individual files in the drive folder URL."""

    parsed_url = urlparse(drive_link)
    if parsed_url.query:
        try:
            folder_id = parse_qs(parsed_url.query).get('id')[0]
        except (TypeError):
            path_segments = parsed_url.path.split('/')
            folder_id = path_segments[-1] if len(path_segments) > 1 else None

    file_list = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()

    # List of tuples of (file_id, file_name) type
    file_id_names = [(file['id'], file['title']) for file in file_list]
    file_links = [file.metadata.get('alternateLink') for file in file_list]

    """Implement the logic here. I'm not sure, how student members are verified, in any case, that code will go here. 
    For now, I am just using a randon student ID. """


    # student_id = '22301728'
    student_id = re.search(r"[0-9]{8}", user.display_name).group(0)
    file_id = 0
    for (file_link, (i, filename)) in zip(file_links, file_id_names):
        if student_id in filename:
            file_id = i
            desired_link = file_link
            break
    if file_id:
        # Send the assignment file
        await send_message(f"{user.mention}'s Assignment No. {assignment_no} is available at: {desired_link}", ephemeral=True)
    else:
        await send_message(
            "Assignment not found! Perhaps you did not submit the assignment. Otherwise, contact faculty.", ephemeral=True)


class GetAssignmentButton(discord.ui.Button):
    def __init__(self, assignment_no, drive_link, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.assignment_no = assignment_no
        self.drive_link = drive_link
        self.label = f"Get Assignment {assignment_no}"
        self.style = discord.ButtonStyle.red

    async def callback(self, interaction: Interaction):
        user = interaction.user
        await get_assignment(user, self.assignment_no, self.drive_link, interaction=interaction)


class GetAssignmentButtonView(discord.ui.View):
    def __init__(self, assignment_no, drive_link, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timeout = None
        self.add_item(item=GetAssignmentButton(assignment_no, drive_link))


@bot.slash_command(name="return-assignments", description="Publish checked assignments with google drive link")
async def return_assignments(ctx, assignment_no, drive_link):

    """One may authorize access to users google drive here: However, I think, doing it globally once would be a
    better option. """

    button_view = GetAssignmentButtonView(assignment_no, drive_link)
    await ctx.respond(
        f" Press the button below to get your checked copy of assignment {assignment_no}.",
        view=button_view
    )






bot.run(token)
