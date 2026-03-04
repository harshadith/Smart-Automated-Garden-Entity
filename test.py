from google import genai

# No arguments needed; it checks GOOGLE_API_KEY or GEMINI_API_KEY automatically
client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.0-flash-lite", 
    contents="Tell me a joke about cats."
)

print(response.text)