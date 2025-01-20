# The app for monitoring telegram channels

`telegram_analyst2.py` - main app module
* `/plugins/handlers.py` - handlers for our telegram user-bot
* `app_status.py` - working with the application status
* `app_types.py` - a module of some types and structures of the application
* `database.py` - resetting database tables
* `normalizer.py` - Telegram antiflood class 'Normalizer' 
* `logger.py` - logger module
* `pgdb.py` - Postgres-connector class 'Database'
* `pgdb_example.py` - examples of using of 'Database'-class
* `chunk.py` - splitting streaming data into chunks
* `channel.py` - channel processing module
* `post.py` - post processing module
* `task.py` - task processing module
* `reaction.py` - counting reactions to a post
* `scheduler.py` - a class for working with a schedule
* `processing.py` - a module for creating all schedules
* `config_py.py` - configuration infrastructure
* `config_example.json` - example of configuration file (config.json)
* `requirements.txt` - requirements

_Note: This project uses `.venv`_

## How it works (in Russian):
[How it works (in Russian)](docs/How_it_works.md)

[How it works (in Russian) Google doc](https://docs.google.com/document/d/1oyME8felY9CLCRHY1TccnelgImf6SMs4yv9Oh2cx9vc/edit?usp=sharing)