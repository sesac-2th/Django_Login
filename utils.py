import environ
import os


def getEnvAttr(env_name):
    env = environ.Env(
        # set casting, default value
        DEBUG=(bool, False)
    )

    # Set the project base directory
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Take environment variables from .env file
    environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

    return os.environ.get(env_name)