# Changing EMAIL_INPUT environment variable (using Gmail)
1. Change the value in .env
2. Go to Google Cloud console
3. Create a project, if not yet
4. Go to Enabled APIs and services
5. Enable Gmail API
6. Create new OAuth client
7. Download the JSON file (call it credentials.json)
8. Put credentials.json in the data folder (data folder resides at project root)
9. Run the app once in your local, and sign in the Gmail account to generate token.json (in data folder)
