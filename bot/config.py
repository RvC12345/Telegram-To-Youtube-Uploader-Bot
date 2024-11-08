import os

class Config:

    BOT_TOKEN = os.environ.get('tk')

    SESSION_NAME = "ytuper"

    API_ID = os.environ.get('apiid')

    API_HASH = os.environ.get('apihash')

    CLIENT_ID = os.environ.get('client_id')

    CLIENT_SECRET = os.environ.get('client_secret')

    AUTH_USERS = [1387186514]

    VIDEO_DESCRIPTION = ""

    VIDEO_CATEGORY = ""

    VIDEO_TITLE_PREFIX = ""

    VIDEO_TITLE_SUFFIX = ""
    
    DEBUG = bool()

    UPLOAD_MODE = "unlisted"
    
    CRED_FILE = "auth_token.txt"
