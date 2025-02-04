import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or  "59c22d42144f43cdd5afde98af1d63306181dc83dc5b26ea4fc03243eff2671b"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///" + os.path.join(basedir,"userdb.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
