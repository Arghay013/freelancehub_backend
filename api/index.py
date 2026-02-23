import os
from config.wsgi import application

# Vercel looks for `app` or `application`
app = application
