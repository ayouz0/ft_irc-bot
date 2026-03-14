import os
from flask import Flask, request
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
app = Flask(__name__)

def call_groq_agent(user_prompt, sys_prompt="Technical utility. Raw data only. Max 300 chars. No prose.", lite=True):
    model_name = "llama-3.1-8b-instant" if lite else "llama-3.3-70b-versatile"

    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": sys_prompt},
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
        return "[ERROR] Syntax: !web <query> or !sh <task> or !exec <task>"

    parts = raw_input.split(' ', 1)
    cmd, args = parts[0].lower(), (parts[1] if len(parts) > 1 else "")

    try:
        if cmd == "!web":
            response = call_groq_agent(f"Search and summarize: {args}", lite=False)
        elif cmd == "!sh":
            sh_sys = "Output strictly raw bash code. No markdown formatting, no backticks, no prose."
            response = call_groq_agent(args, sys_prompt=sh_sys, lite=False)
            
        elif cmd == "!exec":
            # generate command using the smaller model for speed
            exec_sys = "Output strictly a single-line raw bash command. No markdown, no prose."
            raw_cmd = call_groq_agent(args, sys_prompt=exec_sys, lite=False).strip()
            
            # evaluate using the larger model
            eval_prompt = f"Analyze this bash command: '{raw_cmd}'. Is it safe to execute on a host macos system? It must not delete files, open reverse shells, or modify system configs. Reply strictly with the word 'SAFE' or 'UNSAFE'. No other text."
            eval_sys = "You are a strict cybersecurity evaluator. Output only SAFE or UNSAFE."
            evaluation = call_groq_agent(eval_prompt, sys_prompt=eval_sys, lite=False).strip().upper()
            
            if evaluation == "SAFE":
                return f"EXEC_PAYLOAD:{raw_cmd}"
            else:
                return f"[SECURITY_BLOCK] Command flagged as unsafe: {raw_cmd}"
        else:
            return f"[ERROR] Unknown module: {cmd}"

        return response.strip()
        
    except Exception as e:
        return f"[SYSTEM_FAILURE] {str(e)}"

if __name__ == '__main__':
    app.run(port=5000)