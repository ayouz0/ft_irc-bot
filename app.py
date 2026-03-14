import os
from flask import Flask, request
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
app = Flask(__name__)

def call_groq_agent(user_prompt, lite = True):
    model_name =  "llama-3.3-70b-versatile" if lite == False else "llama-3-8b"

    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "Technical utility. Raw data only. Max 300 chars. No prose."},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1
    )
    return completion.choices[0].message.content

@app.route('/prompt', methods=['POST'])
def handlePrompt():
    data = request.get_json() if request.is_json else request.form
    raw_input = data.get('prompt', '').strip()
    
    if not raw_input.startswith("!"):
        return "[ERROR] Syntax: !web <query> or !sh <task>"

    parts = raw_input.split(' ', 1)
    cmd, args = parts[0].lower(), (parts[1] if len(parts) > 1 else "")

    try:
        if cmd == "!web":
            response = call_groq_agent(f"Search and summarize: {args}", lite=True)
        elif cmd == "!sh":
            response = call_groq_agent(f"provide BASH ONLY for this user query: {args}")
        elif cmd == "!exec":
            # generate the command
            generate_prompt = f"Output strictly the raw bash command for: {args}. No markdown, no prose, no backticks."
            raw_cmd = call_groq_agent(generate_prompt)
            clean_cmd = raw_cmd.replace('`', '').replace('\n', ' && ').strip()
            
            # evaluate the generated command
            eval_prompt = f"Analyze this bash command: '{clean_cmd}'. Is it safe to execute on a host macos system? It must not delete files, open reverse shells, or modify system configs. Reply strictly with the word 'SAFE' or 'UNSAFE'. No other text."
            evaluation = call_groq_agent(eval_prompt).strip().upper()
            if evaluation == "SAFE":
                return f"EXEC_PAYLOAD:{clean_cmd}"
            else:
                return f"[SECURITY_BLOCK] Command flagged as unsafe. {clean_cmd}"
        else:
            return f"[ERROR] Unknown module: {cmd}"

        return response.replace('**', '').strip()[:400]
    except Exception as e:
        return f"[SYSTEM_FAILURE] {str(e)}"

if __name__ == '__main__':
    app.run(port=5000)