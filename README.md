[![CodeFactor](https://www.codefactor.io/repository/github/jonwiseman/lfj/badge)](https://www.codefactor.io/repository/github/jonwiseman/lfj)[![buddy pipeline](https://app.buddy.works/bowlian/lfj/pipelines/pipeline/251746/badge.svg?token=ab2372452e6e3f91c0b0f43ce4d2b5f58e6e232abaaf685199102b62422cc5d7 "buddy pipeline")](https://app.buddy.works/bowlian/lfj/pipelines/pipeline/251746)

This repository contains files related to the final project for CS341: Software Engineering.

## Goal
This project aims to create a Discord bot for Elizabethtown College's E-Sports team to accomplish five goals:
1. Handling event signup
2. Balancing scrimmage teams
3. Posting reminders for registered events
4. Allowing users to self-assign to groups
5. Relevant statistics collection and querying

## Requirements
In order to use the LFJ bot, you will need four things:

1. An installation of Python 3.7 (for installing prerequesites and running the main bot file)  
2. An installation of MySQL (for building and utilizing the database backend)  
3. A Discord account
4. The LFJ bot token (for signing the bot in to Discord)

## Start Guide

**Cloning the Repository**

Run the following command:

`git clone https://github.com/jonwiseman/LFJ FOLDER`

FOLDER: name of folder to clone repository into

**Creating a Virtual Environment**  
It's good practice to create a virtual environment for each one of your projects.  You can think of it like a separate Python installation for a project.  Creating a new virtual environment is simple: navigate to LFJ's root directory and run the following command:

`python -m venv env`

This will create a new virtual environment in the root directory called env (you can name it whatever you want: just substitute a file name for env).  To activate your new virtual environment on Windows, run the following command:

`.\env\Scripts\activate`

On Linux, run:

`source env/bin/activate`

You should now see a little (env) before your command line, indicating that you are running in a virtual environment.

**Installing Python Requirements**  
With your virtual environment running, navigate to the LFJ/Docs folder.  To install all of the Python requirements needed to run LFJ, execute the following command:

`pip install -r Docs/requirements.txt`

This will read all of the requirements and install them via pip.

**Constructing the configuration.conf File**  
To maintain data security (such as database usernames and passwords, and the bot's unique Discord token), you must maintain a configuration file that is parsed by many of LFJ's scripts.  The format is as follows:

[Discord]  
token =   
event_channel_id =   
prefix =

[Database]  
username =   
password =   
host =   
database =   

Creating a configuration file is simple: create a simple text file, copy and paste the above text, fill in the required information (don't worry about putting quotations around Strings or anything like that), and save the file as configuration.conf.  Keep the configuration file in the project's root directory (i.e. not inside any folder; keep it next to the .gitignore file and the README).  To make sure that the token and database information is kept private, make sure that configuration.conf is listed in the .gitignore (this keeps it from being pushed to Github).  Don't worry about the Discord section yet: we'll cover it below in the "Setting up Discord and Creating a Bot" subsection.

**Building the Database**    
The next step is to initialize the backend database.  Open MySQL (either through the workbench - my preferred option - or through its command line) and run the lfj.sql script (located under LFJ/Database).  This script creates the database and initializes the user table with a single entry: jon_wiseman#8494 with admin status.  Don't worry, you can add yourself to the database later via the LFJ bot in Discord or run init_db.py and add yourself in manually.  The backend scripts are run such that only an admin can add, delete, or update users; additionally, an admin cannot delete another admin user (so be careful adding in new users via LFJ: if you add an admin, you'll have to manually remove him via MySQL queries or using the init_db.py script).  Admin status is either 0 (NOT an admin) or 1 (IS an admin).

**Setting up Discord and Creating a Bot**  
In order to use LFJ, you'll need a Discord account, a registered bot, and that bot's token.  Creating a Discord account is easy: just head on over to [Discord](https://discordapp.com/login) and register your account.  Now that you've got a Discord account, you'll need to create a bot account that can run LFJ's scripts.  The steps are fairly straightforward:

1. Head to the application developer [portal](https://discordapp.com/developers/applications/)  
2. Create a new application by selecting the button at the top right  
3. Give your new application a name  
4. Navigate to the bot settings using the right-hand list  
5. Add a new bot by selecting the button on the right side of the screen  
6. Give your new bot a name  

Now that you've got a bot, you can enter the bot's token to your configuration file!  You can copy it from the bot's overview on the application page.  Please note that if you post your secret token online, Discord will automatically generate a new token for security.  With the bot created, we can organize our server appropriately.  To create a new server, follow these steps:  

1. Open Discord  
2. On the left-hand side of the screen, select the green plus icon to create a new server  
3. Confirm that you want to create a server and give it a name  

LFJ requires that your server has a channel named events so that it can notify users about upcoming events and allow them to register for them.  On the left-hand side of the screen under the "Text Channels" dropdown, click the plus to create a new text channel.  Name it "events" so that the bot can find it on startup; no caps, no punctuation, all lowercase.  Next, we'll need to get this channel's unique ID to supply to our configuration file.  To do this, you'll need to enable Developer Mode:  

1. Open Discord  
2. Navigate to User Settings (located next to your display name at the bottom left)  
3. Click on Appearance on the left-hand side  
4. Scroll down to Advanced  
5. Enable Developer Mode  

Now go back to your server, right click on the events channel, and select Copy ID.  Paste this numeric ID into the configuration file under event_channel_id.  Finally, you'll need to invite your bot to the server.  Navigate back to the Developer Portal and select the application again.  Under OAuth2, select bot under Scopes.  Give your bot the permissions it requires, and then copy the URL from the Scopes section.  Follow that URL and add your bot to the server you created before.

If these directions are confusing, [here's](https://discordpy.readthedocs.io/en/latest/discord.html) a helpful link that might explain it better.  You can also navigate to the Wiki where there's a more detailed guide with photos.

**Starting the Bot**  
The bot's functionality is divided into modules: each script in the LFJ/Scripts folder controls one of the bot's functions (such as querying the user table or adding events).  To run the bot, you need only run bot_controller.py.  After the bot is running, you should see his status turn to green in Discord.  Do not interact with the bot via the command line; after the bot is started, only send it commands via Discord.  A list of commands you can use to interact with the bot are available in the [Available Commands](https://github.com/jonwiseman/LFJ#available-commands) section.

## Available Commands  
There are nineteen commands available in LFJ right now, organized into 6 categories:

**User Queries**  
These are queries that allow interaction with the user table:

1. add_user
2. delete_user
3. query_user
4. set_admin_status

**Game Queries**  
These are queries that allow interaction with the game table:

5. add_game
6. delete_game
7. query_game
8. edit_id
9. edit_name
10. list_games

**Event Queries**  
These are queries that allow interaction with the event and registration tables:

11. create_event
12. delete_event
13. get_events
14. query_event
15. sort_teams

**Membership Queries**  
These are queries that allow interaction with the membership table:

16. create_membership
17. delete_membership
18. set_skill

**Performance Queries**  
These are commands that allow the input of game statistics.

19. perf_template  
20. perf_update

**Miscellaneous Commands**  

21. help
22. exit

You can specify which prefix is used to address the bot by changing the configuration file.

---

**Adding a new user**
The add_user command can be used to add a new user to LFJ's database.  This is the first step necessary for a user to be able to register in game groups and for events.  Please note that the adding user MUST be an admin.  The syntax for this command is as follows:

`$add_user USER_ID ADMIN`

USER_ID: the user's Discord id (mine is 480122056114044939)
ADMIN: the user's admin status [TRUE|FALSE].  Please note that a user with admin status TRUE cannot be deleted via LFJ later

**Deleting a User**
The delete_user command can be used to delete a user from LFJ's database.  Please note that the user doing the deleting MUST be an admin, and that an admin cannot be deleted from the database.  The syntax for this command is as follows:

`$delete_user USER_ID`

USER_ID: the user's Discord id

**Querying for a User**
The query_user command requires one of two additional arguments: either ALL or a USER_ID.  If ALL is entered, then the bot will return a list of all users in the database; if a USER_ID is entered, then only that user's information will be returned.  The syntax for this command is as follows:

`$query_user [ALL|USER_ID]`

**Setting a User's Admin Status**
This command can be used to update a user's admin status. Please not that only an admin can update another user's admin status. The syntax for this command is as follows:

`$set_admin_status USER_ID [TRUE|FALSE]`

**Adding a new Game**
The add_game command can be used to add a new game to the bot's backend.  Please note that the requesting user must be an administrator to successfully add a new game.  The syntax for this command is as follows:

`$add_game ID NAME`

ID: numeric ID for game
NAME: string name of game

**Deleting a Game**
The delete_game command can be used to delete a game from the bot's backend.  Please note that the requesting user must be an administrator to successfully delete a game.  The syntax for this command is as follows:

`$delete_game NAME`

NAME: string name of game to be deleted

**Querying for a Game**
The query_game command can be used to get information about one specific game or all games in the bot's database.  The syntax for this command is as follows:

`$query_game [ALL|NAME]`

ALL: to query all games in the database
NAME: name of specific game to query

**Editing a Game's ID**
The edit_id command can be used to edit a game's numeric ID.  Please note that the requesting user must be an admin in order to successfully edit a game's information.  The syntax for this command is as follows:

`$edit_id NAME NEW_ID`

NAME: game's string name for identification
NEW_ID: new numeric ID of game

**Editing a Game's Name**
The edit_name command can be used to edit a game's name.  Please note that the requesting user must be an admin in order to successfully edit a game's information.  The syntax for this command is as follows:

`$edit_name OLD_NAME NEW_NAME`

OLD_NAME: old string name of game
NEW_NAME: new string name of game

**Editing a Game's ID**
The list_games command is an alias to query_game ALL

`$list_games`

**Creating a New Event**
The create_event command can be used to create a new event, and requires three positional arguments: an event title (must be one token), an event date (formatted as MM/DD/YYYY), and a game title.  Right now, any user can create an event.  The syntax for this command is as follows:

`$create_event EVENT_NAME DATE GAME`

EVENT_NAME: event's title
DATE: event's date (formatted MM/DD/YYYY)
GAME: game's title (must match what is in the database)

**Deleting an Event**
The delete_event command delete's an event from the LFJ database; it requires one positional argument: event title (must be one token).  Only an admin user can delete an event.  The syntax for this command is as follows:

`$delete_event EVENT_NAME`

EVENT_NAME: event's title

**See all Events**
The get_events command returns all events in the LFJ database; it does not require any positional arguments.  The syntax for this command is as follows:

`$get_events`

**Getting Information about an Event**
The query_event command returns information about a specific event.  The syntax for this command is as follows:

`$query_event ALL|TITLE`

ALL: to query all events in the database
TITLE: event's title

**Sorting Event Teams**
The sort_teams command sorts the teams of a given event.  The syntax for this command is as follows:

`$sort_teams EVENT_NAME SORT_TYPE`

EVENT_NAME: event's title
SORT_TYPE: type to sort event teams by (RANDOM) (FULL)

**Adding a game to your user profile**
The create_membership command registers a user as a player of a game.  The syntax for this command is as follows:

`$create_membership GAME SKILL`

GAME: game's title (must match what is in the database)
SKILL: user's initial ranking for game

**Removing a game from your user profile**
The delete_membership command removes as a player for a game.  The syntax for this command is as follows:

`$delete_membership USER GAME`

USER: name of the user to remove
GAME: game's title (must match what is in the database)

**Setting a User's Game Skill**
This command can be used to update a user's skill level for a given game. The syntax for this command is as follows:

`$set_skill GAME SKILL_LEVEL`

GAME: game name for updating skill level (CSGO, LOL, RL)
SKILL_LEVEL: skill ranking for game being updated (NUMERIC)

**Getting a Template to Enter Event Statistics**  
This command can be used to retrieve a template to upload stats based on the registered players. The syntax for this command is as follows:

`$perf_template EVENT_NAME`

EVENT_NAME: title of the event to request registered players template for

**Updating Performance Information**
This command can be used to update statistics based on a csv template file. To use this command upload a modified csv template file and use the comment:

`$perf_update`

This will Update/Insert performance data based off of the provided CSV file

**Getting Help**
The help command can be used to get help from the bot regarding available commands and specific command syntax.  Running the command without supplying an additional argument will return a list of all available commands. The syntax for this command is as follows:

`$help [COMMAND]`

COMMAND: (optional) specific command to get help for

**Querying for a Specific Event**
The query_event command can be used to get information about a specific event.  The syntax for this command is as follows:

`$query_event NAME`

NAME: string name of the event about which to get information
