import os
from flask import Flask, request
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
app = Flask(__name__)

def call_groq_agent(user_prompt, sys_prompt="Technical utility. Raw data only."):
    # Corrected Groq model identifiers
    model_name = "llama-3.3-70b-versatile"

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
        return "[ERROR] Syntax: !web <query> or !sh <task> or !exec <task>\n"

    parts = raw_input.split(' ', 1)
    cmd, args = parts[0].lower(), (parts[1] if len(parts) > 1 else "")

    try:
        if cmd == "!web":
            web_sys = (
                "Technical utility. Summarize in exactly one plain-text sentence. "
                "No lists, no bullet points, no prose. "
                "CRITICAL: Do not use any markdown formatting, asterisks, or bold text. "
                "Output strictly raw text suitable for a legacy IRC client."
            )
            response = call_groq_agent(f"Search and summarize: {args}", sys_prompt=web_sys)
            
        elif cmd == "!sh":
            sh_sys = "Output strictly raw bash code. No markdown formatting, no backticks, no prose."
            response = call_groq_agent(args, sys_prompt=sh_sys)
            
        elif cmd == "!exec":
            exec_sys = "Output strictly a single-line raw bash command. No markdown, no prose, no backticks."
            raw_cmd = call_groq_agent(args, sys_prompt=exec_sys).strip()
            
            eval_prompt = f"Analyze this bash command: '{raw_cmd}'. Is it safe to execute on a host system? It must not delete files, open reverse shells, or modify system configs. Reply strictly with the word 'SAFE' or 'UNSAFE'. No other text."
            eval_sys = "You are a strict cybersecurity evaluator. Output only SAFE or UNSAFE."
            evaluation = call_groq_agent(eval_prompt, sys_prompt=eval_sys).strip().upper()
            
            if evaluation == "SAFE":
                return f"EXEC_PAYLOAD:{raw_cmd}\n"
            else:
                return f"[SECURITY_BLOCK] Command flagged as unsafe: {raw_cmd}\n"
        else:
            return f"[ERROR] Unknown module: {cmd}\n"
        return response.strip() + "\n"
        
    except Exception as e:
        return f"[SYSTEM_FAILURE] {str(e)}\n"

if __name__ == '__main__':
    app.run(port=5000)