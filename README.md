# Razer HQ Gantry Bot
This project is a Telegram bot that automates the Razer HQ gantry visitor registration process. It consists of **two components**:
1. **Telegram Bot** - handles user interaction
2. **Daily Job/Scheduler** - runs automated daily batch job

You can run the bot locally on **Windows** or **via Docker**.

Feel free to try out the [@razer_hq_gantry_bot](https://web.telegram.org/k/#@razer_hq_gantry_bot) deployed on Telegram.

<br>

## Prerequisites
Before you start, make sure you have the following installed:
- Python 3.10+
- Git
- Docker & Docker Compose (only required for Docker setup)
- A Telegram account
- A Gmail account (for automated email processing)

<br>

## Running the Bot Locally (Windows)
1. Clone/Download the [repository](https://github.com/yongjianwen/razer-hq-gantry-bot)
2. Create a virtual environment in the project root:
```
python -m venv .venv
```
3. Activate the virtual environment:
```
.venv\Scripts\activate.bat
```
4. Install dependencies:
```
pip install -r requirements.txt
```
5. Install Playwright:
```
playwright install
```
6. Create an empty `/data` folder in root folder:
```
mkdir data
```
7. Enter Telegram bot token into the `.env` file (create your Telegram bot with Telegram's BotFather):
```
TELEGRAM_BOT_TOKEN=<YOUR_BOT_TOKEN>
```
8. Update the email address in the .env file (refer to this [section](#changing-email_input-environment-variable-gmail) for full instructions):
```
EMAIL_INPUT=<YOUR_EMAIL_ADDRESS>
```
9. Run the command to start the bot in your local:
```
python -m bot.bot
```
10. Run the command to start the daily job/scheduler in your local:
```
python -m bot.daily_job
```

<br>

### Changing EMAIL_INPUT environment variable (Gmail)
1. Change the value in `.env`
2. Go to Google Cloud console
3. Create a project (if not yet created)
4. Go to Enabled APIs and services
5. Enable Gmail API
6. Create new OAuth client
7. Download the JSON file (rename it `credentials.json`)
8. Put `credentials.json` in the `/data` folder
9. Run the app locally, and sign in the Gmail account to generate `token.json` (automatically generated in `/data` folder)

<br>

## Running with Docker
1. Build the docker images:
```
docker compose build --no-cache
```
2. Save/Extract the docker image to anywhere on your local machine:
```
docker save -o razer-bot.tar razer-hq-auto-registration-telegram-bot
```

## Deploying Container on Synology
1. Upload the extracted docker image to anywhere on Synology, e.g. `/volume1/docker/razer-bot/docker-image/`
2. Go to Container Manager > Image
3. Click on Action > Import > Add From File > From this DSM
4. Select the docker image uploaded
5. After adding the image, click on Run, then select the inputs as follows:
<p align="start"><img width="500" alt="image" src="https://github.com/user-attachments/assets/1c511428-78d3-46ab-a72b-19f2bcb2187b" /></p>

6. Mount the volumes (create the path and upload the file, if not yet done):
<p align="start"><img width="500" alt="image" src="https://github.com/user-attachments/assets/f3bbdd29-2dbd-4784-94a9-cb86f2629b13" /></p>

7. Enter the command:
<p align="start"><img width="500" alt="image" src="https://github.com/user-attachments/assets/5e0540a8-8508-47ef-b319-43e712553ee0" /></p>

8. Finish the creation process for the **Telegram Bot** component
9. Repeat the same steps for the **Daily Job/Scheduler** component, by replacing the command with `python -m bot.daily_job`
