from os import environ
from dotenv import load_dotenv

load_dotenv(dotenv_path=r'src\.env')

SECRET_KEY = environ.get('SECRET_KEY')
SQLALCHEMY_DATABASE_URI = environ.get('SQLALCHEMY_DATABASE_URI')
SQLALCHEMY_TRACK_MODIFICATIONS = environ.get('SQLALCHEMY_TRACK_MODIFICATIONS')
if __name__ == "__main__":
     print(SECRET_KEY)
     print(SQLALCHEMY_DATABASE_URI)
     print(SQLALCHEMY_TRACK_MODIFICATIONS)