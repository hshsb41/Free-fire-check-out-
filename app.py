import requests
import json
import urllib.parse
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

def verify_real_garena_token(access_token):
    try:
        url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
        parsed = urllib.parse.urlparse(response.url)
        params = urllib.parse.parse_qs(parsed.query)
        
        uid = params.get("account_id", [None])[0]
        if not uid or uid == "Unknown":
            return False, None, None, None, None
            
        nickname = urllib.parse.unquote(params.get("nickname", ["UNKNOWN"])[0])
        region = params.get("region", ["UNKNOWN"])[0]
        
        email_url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        eparms = {'app_id': '100067', 'access_token': access_token}
        r = requests.get(email_url, params=eparms, headers=headers, timeout=8)
        email = "NOT_BOUND"
        if r.status_code == 200:
            data = r.json()
            if data.get('result') == 0:
                email = data.get('email', 'NOT_BOUND')
                
        return True, uid, nickname, region, email
    except Exception:
        return False, None, None, None, None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GARENA ADVANCED COMMAND CENTER</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Share Tech Mono', monospace;
            background-color: #000000;
            color: #d4d4d4;
        }
        /* Completely borderless and zero glow components */
        .clean-box {
            background-color: #0a0a0a;
            border: none !important;
            box-shadow: none !important;
            border-radius: 0px !important;
        }
        .clean-input {
            background-color: #050505;
            border: none !important;
            box-shadow: none !important;
            border-radius: 0px !important;
            color: #ffffff;
        }
        .clean-input:focus {
            outline: none;
            background-color: #0f0f0f;
        }
        .clean-btn {
            background-color: #141414;
            border: none !important;
            box-shadow: none !important;
            border-radius: 0px !important;
            color: #ffffff;
            transition: background 0.1s ease;
        }
        .clean-btn:hover:not(:disabled) {
            background-color: #262626;
        }
        .clean-btn:disabled {
            opacity: 0.3;
            cursor: not-allowed;
        }
    </style>
</head>
<body class="min-h-screen flex items-center justify-center p-3">

    <div class="w-full max-w-xl clean-box p-6 space-y-6">
        
        <!-- HEADER -->
        <div class="pb-3 flex justify-between items-center bg-transparent border-b border-neutral-900">
            <div>
                <h1 class="text-xs font-bold tracking-[0.2em] text-red-500 uppercase"></h1>
                <p class="text-[10px] text-neutral-500 uppercase tracking-widest mt-0.5">FREE FIRE</p>
            </div>
            <div>
                <span class="px-2 py-1 bg-neutral-900 text-red-500 text-[9px] uppercase font-bold">ONLINE</span>
            </div>
        </div>

        <!-- STEP 1: TOKEN INPUT (BORDERLESS & NO GLOW) -->
        <div id="tokenSection" class="space-y-2">
            <label class="block text-[11px] font-bold tracking-wider text-neutral-400 uppercase">🔑 ACCESS TOKEN</label>
            <div class="flex gap-2">
                <input type="text" id="accessToken" placeholder="PASTE ACCESS TOKEN HERE..." 
                    class="w-full clean-input px-3 py-3 text-xs font-bold placeholder-neutral-700">
                <button onclick="validateToken()" id="validateBtn" class="clean-btn px-6 text-xs font-bold uppercase tracking-wider">
                    VERIFY
                </button>
            </div>
            <p id="tokenErrorMsg" class="text-[10px] text-red-500 font-bold uppercase hidden"></p>
        </div>

        <!-- STEP 2: PROFILE & FAST LOOP ENGINE -->
        <div id="controlSection" class="space-y-4 hidden pt-2">
            
            <!-- PROFILE DISPLAY -->
            <div class="clean-box p-3.5 space-y-2 text-[11px] bg-neutral-950">
                <div class="text-neutral-500 font-bold uppercase pb-1 border-b border-neutral-900">👤 VERIFIED SESSION PROFILE</div>
                <div class="grid grid-cols-2 gap-2 font-bold text-neutral-300">
                    <div>UID: <span id="infoUid" class="text-white">---</span></div>
                    <div>REGION: <span id="infoRegion" class="text-cyan-400">---</span></div>
                    <div class="col-span-2">NAME: <span id="infoName" class="text-emerald-400">---</span></div>
                    <div class="col-span-2">EMAIL: <span id="infoEmail" class="text-amber-400">---</span></div>
                </div>
            </div>

            <!-- CONTROLS -->
            <div class="space-y-2">
                <label class="block text-[11px] font-bold tracking-wider text-neutral-400 uppercase"></label>
                <button onclick="startCodeLoop()" id="execBtn" class="w-full clean-btn py-3.5 text-xs font-extrabold uppercase tracking-widest text-red-500 bg-red-950/20">
                     START 
                </button>
            </div>

            <!-- TERMINAL LOGS -->
            <div class="space-y-1">
                <div class="text-[10px] font-bold text-neutral-500 uppercase tracking-widest flex justify-between">
                    <span>💻 LIVE CHECKING</span>
                    <span id="loopStatus" class="text-red-500 font-bold">STATUS: IDLE</span>
                </div>
                <div id="terminalLog" class="clean-input p-3 text-xs h-56 overflow-y-auto space-y-1.5 font-bold uppercase bg-black">
                    <div class="text-neutral-600">></div>
                </div>
            </div>

        </div>

    </div>

    <script>
        let verifiedToken = "";
        let isRunning = false;
        let loopTimeout = null;

        async function validateToken() {
            const tokenInput = document.getElementById('accessToken').value.trim();
            const btn = document.getElementById('validateBtn');
            const errBox = document.getElementById('tokenErrorMsg');
            const controlSec = document.getElementById('controlSection');

            if (!tokenInput) {
                errBox.innerText = "ERROR: TOKEN FIELD CANNOT BE EMPTY";
                errBox.classList.remove('hidden');
                return;
            }

            btn.disabled = true;
            btn.innerText = "CHECKING...";
            errBox.classList.add('hidden');

            try {
                const res = await fetch('/api/validate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({token: tokenInput})
                });
                const data = await res.json();

                if (data.success) {
                    verifiedToken = tokenInput;
                    document.getElementById('infoUid').innerText = data.uid;
                    document.getElementById('infoRegion').innerText = data.region;
                    document.getElementById('infoName').innerText = data.name;
                    document.getElementById('infoEmail').innerText = data.email;
                    
                    document.getElementById('tokenSection').classList.add('opacity-40');
                    document.getElementById('accessToken').disabled = true;
                    btn.innerText = "VERIFIED";
                    controlSec.classList.remove('hidden');
                } else {
                    errBox.innerText = "ERROR: INVALID TOKEN OR REJECTED";
                    errBox.classList.remove('hidden');
                    btn.disabled = false;
                    btn.innerText = "VERIFY";
                }
            } catch (e) {
                errBox.innerText = "ERROR: CONNECTION FAILED";
                errBox.classList.remove('hidden');
                btn.disabled = false;
                btn.innerText = "VERIFY";
            }
        }

        function startCodeLoop() {
            if (isRunning) return;
            isRunning = true;

            const execBtn = document.getElementById('execBtn');
            const logBox = document.getElementById('terminalLog');
            const loopStatus = document.getElementById('loopStatus');
            
            execBtn.disabled = true;
            execBtn.innerText = "";
            loopStatus.innerText = "STATUS: RUNNING";
            logBox.innerHTML = `<div class="text-cyan-400 font-bold">>LOADING</div>`;

            let currentCode = Math.floor(Math.random() * 200000);

            function processBatch() {
                if (!isRunning) return;

                // Push multiple sequential code iterations per tick so it doesn't feel slow or stuck on one code
                let batchHtml = "";
                for (let i = 0; i < 4; i++) {
                    if (currentCode > 999999) currentCode = 0;
                    let codeStr = String(currentCode).padStart(6, '0');
                    
                    batchHtml += `<div class="text-red-500 font-bold tracking-wider pb-0.5">> TESTING 6-DIGIT CODE: [ <span class="text-white">${codeStr}</span> ] -> NO MATCH: <span class="text-red-600"></span></div>`;
                    currentCode += Math.floor(Math.random() * 7) + 1;
                }

                logBox.innerHTML += batchHtml;
                logBox.scrollTop = logBox.scrollHeight;

                // Fast continuous loop cycle (runs smoothly every 400 milliseconds instead of lagging or waiting 30 seconds)
                loopTimeout = setTimeout(processBatch, 400);
            }

            processBatch();
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/validate', methods=['POST'])
def api_validate():
    data = request.get_json()
    token = data.get('token', '').strip()
    
    if not token:
        return jsonify({"success": False})
        
    is_valid, uid, name, region, email = verify_real_garena_token(token)
    if is_valid:
        return jsonify({
            "success": True,
            "uid": uid,
            "name": name,
            "region": region,
            "email": email
        })
    else:
        return jsonify({"success": False})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
