import os
from flask import Flask, request
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
app = Flask(__name__)

def call_groq_agent(user_prompt, sys_prompt="Technical utility.", model_name="llama-3.3-70b-versatile"):
    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1,
        max_tokens=150
    )
    return completion.choices[0].message.content

@app.route('/prompt', methods=['POST'])
def handlePrompt():
    data = request.get_json() if request.is_json else request.form
    raw_input = data.get('prompt', '').strip()
    
    if not raw_input.startswith("!"):
        return "[ERROR] Syntax: !web <query> or !sh <task>\n"

    parts = raw_input.split(' ', 1)
    cmd, args = parts[0].lower(), (parts[1] if len(parts) > 1 else "")

    try:
        if cmd == "!web":
            web_sys = (
                "Technical utility. Perform a web search. "
                "Output strictly one plain-text sentence. "
                "No markdown, no asterisks, no bold. Raw text only."
            )
            response = call_groq_agent(args, sys_prompt=web_sys, model_name="groq/compound-mini")
            
        elif cmd == "!sh":
            sh_sys = "Output strictly raw bash code. No markdown, no backticks, no prose."
            response = call_groq_agent(f"Generate bash for: {args}", sys_prompt=sh_sys)
            
        else:
            return f"[ERROR] Unknown module: {cmd}\n"
        
        clean_response = response.replace('\n', ' ').replace('**', '').replace('`', '').strip()
        return clean_response + "\n"
        
    except Exception as e:
        return f"[SYSTEM_FAILURE] {str(e)}\n"

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)