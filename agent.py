# This file is for testing the Google GenAI client and listing available models.
#  It is not part of the main application logic.


from google import genai

client = genai.Client(api_key="AIzaSyDSI9RO0Dlp5kKKpeURYgU4PjXrhytkmV8")

models = client.models.list()

for m in models:
    print(m)