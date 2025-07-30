from google.cloud import firestore
import os
from dotenv import load_dotenv

load_dotenv()

db = firestore.Client()
