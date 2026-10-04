"""Transcript -> Instagram carousel multi-agent pipeline."""
from dotenv import find_dotenv, load_dotenv

# Load a .env file from the folder you run the command in (real env vars take priority).
# Must happen before the other modules read settings such as CAROUSEL_MODEL.
load_dotenv(find_dotenv(usecwd=True))
