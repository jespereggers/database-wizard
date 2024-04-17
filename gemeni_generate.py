import google.generativeai as genai

# Configure the GEMINI LLM
genai.configure(api_key='AIzaSyCAQUi69WK1fEN-bh4uAJ6miMW-1OCJ-VY')
model = genai.GenerativeModel('gemini-pro')

#basic generation
def generate_text(prompt):
    response = model.generate_content(prompt)
    return response.text

print(generate_text("Wieviele Mitarbeiter hat a+d estrichbau gmbh?"))