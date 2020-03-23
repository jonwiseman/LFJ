This repository contains files related to the final project for CS341: Software Engineering.

## Goal  
This project aims to create a Discord bot for Elizabethtown College's E-Sports team to accomplish five goals:  
1. Handling event signup  
2. Balancing scrimmage teams  
3. Posting reminders for registered events  
4. Allowing users to self-assign to groups  
5. Relevant statistics collection and querying  

## Requirements
In order to use the LFJ bot, you will need two things:  

1. An installation of MySQL (for building and utilizing the database backend)  
2. The LFJ bot token (for signing the bot in to Discord)

## Start Guide

**Creating a Virtual Environment**  
It's good practice to create a virtual environment for each one of your projects.  You can think of it like a separate Python installation for a project.  Creating a new virtual environment is simple: navigate to LFJ's root directory and run the following command:

`python venv env`

This will create a new virtual environment in the root directory called env (you can name it whatever you want: just substitute a file name for env).  To activate your new virtual environment, run the following command:

`.\env\Scripts\activate`

You should now see a little (env) before your command line, indicating that you are running in a virtual environment.

**Installing Python Requirements**  
With your virtual environment running, navigate to the LFJ/Docs folder.  To install all of the Python requirements needed to run LFJ, execute the following command:  

`pip install -r requirements.txt`

This will read all of the requirements and install them via pip.

**Constructing the configuration.conf File**  
To maintain data security (such as database usernames and passwords, and the bot's unique Discord token), you must maintain a configuration file that is parsed by many of LFJ's scripts.  The format is as follows:  

[Discord]  
token =   

[Database]  
username =   
password =   
host =   
database =   

Creating a configuration file is simple: create a simple text file, copy and paste the above text, fill in the required information (don't worry about putting quotations around Strings or anything like that), and save the file as configuration.conf.  Keep the configuration file in the project's root directory (i.e. not inside any folder; keep it next to the .gitignore file and the README).  To make sure that the token and database information is kept private, make sure that configuration.conf is listed in the .gitignore (this keeps it from being pushed to Github).

**Building the Database**    
The next step is to initialize the backend database.  Open MySQL (either through the workbench - my preferred option - or through its command line) and run the lfj.sql script (located under LFJ/Database).  This script creates the database and initializes the user table with a single entry: jon_wiseman#8494 with admin status.  Don't worry, you can add yourself to the database later via the LFJ bot in Discord.  The backend scripts are run such that only an admin can add, delete, or update users; additionally, an admin cannot delete another admin user (so be careful adding in new users via LFJ: if you add an admin, you'll have to manually remove him via MySQL queries).  Admin status is either 0 (NOT an admin) or 1 (IS an admin).

**Starting the Bot**  
The bot's functionality is divided into modules: each script in the LFJ/Scripts folder controls one of the bot's functions (such as querying the user table or adding events).  To run the bot, you need only run bot_controller.py.  After the bot is running, you should see his status turn to green in Discord.  Do not interact with the bot via the command line; after the bot is started, only send it commands via Discord.  A list of commands you can use to interact with the bot are available in the [Available Commands](https://github.com/jonwiseman/LFJ/wiki/2.-Available-Commands) section.

## Available Commands  
There are four commands available in LFJ right now:

1. add_user
2. delete_user
3. query_user
4. set_email
5. set_admin
6. set_skill

**Adding a new user**     
The add_user command can be used to add a new user to LFJ's database.  This is the first step necessary for a user to be able to register in game groups and for events.  Please note that the adding user MUST be an admin.  The syntax for this command is as follows:  

`@LFJ add_user DISPLAY_NAME EMAIL ADMIN`

DISPLAY_NAME: the user's Discord display name (mine is jon_wiseman#8494)  
EMAIL: the user's email  
ADMIN: the user's admin status (0 or 1).  Please note that a user with admin status 1 cannot be deleted via LFJ later

**Deleting a User**    
The delete_user command can be used to delete a user from LFJ's database.  Please note that the user doing the deleting MUST be an admin, and that an admin cannot be deleted from the database.  The syntax for this command is as follows:  

`@LFJ delete_user DISPLAY_NAME`

DISPLAY_NAME: the user's Discord display name  

**Querying for a User**    
The query_user command requires one of two additional arguments: either ALL or a DISPLAY_NAME.  If ALL is entered, then the bot will return a list of all users in the database; if a DISPLAY_NAME is entered, then only that user's information will be returned.  The syntax for this command is as follows:  

`@LFJ query_user [ALL|DISPLAY_NAME]`

**Setting a User's Email**    
This command can be used to update a user's email.  Please note that only an admin can update a user's information.  The syntax for this command is as follows:  

`@LFJ set_email DISPLAY_NAME EMAIL`  

DISPLAY_NAME: Discord display name of the user whose email will be updated  
EMAIL: new email for the user

**Setting a User's Admin Status**
This command can be used to update a user's admin status. Please not that only an admin can update another user's admin status. The syntax for this command is as follows:

`@LFJ set_admin DISPLAY_NAME [TRUE|FALSE]`

**Setting a User's Game Skill**
This command can be used to update a user's skill level for a given game. The syntax for this command is as follows:

`@LFJ set_skill GAME SKILL_LEVEL

GAME: game name for updating skill level (CSGO, LOL, RL)
SKILL_LEVEL: skill ranking for game being updated (NUMERIC)