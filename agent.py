# This file is for testing the Google GenAI client and listing available models.
#  It is not part of the main application logic.


from google import genai

client = genai.Client(api_key="ADD_YOUR_Google_Gemini_Key")

models = client.models.list()

for m in models:
    print(m)
