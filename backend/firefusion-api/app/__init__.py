# Load .env into os.environ at the moment the `app` package is imported,
# *before* any submodule reads `os.environ[...]`. This makes local
# `fastapi dev` runs match the docker-compose environment without anyone
# having to remember to `export` env vars by hand.
#
# In Docker, .env doesn't exist and docker-compose has already populated
# os.environ — load_dotenv() is a no-op there.
from dotenv import load_dotenv

load_dotenv()
