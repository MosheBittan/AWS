import multiprocessing
import time
import psutil
import os
import urllib.request
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# --- Global Storage for Running Processes ---
RUNNING_PROCESSES = []

# --- Helper: Get Public IP ---
def get_public_ip():
    try:
        # We query an external service to find our public IP
        # This works on EC2, home PCs, etc.
        ip = urllib.request.urlopen('https://checkip.amazonaws.com', timeout=3).read().decode('utf-8').strip()
        return ip
    except Exception:
        return "Unknown (Could not fetch IP)"

# --- Backend Logic: Stress Worker ---
def stress_worker(core_id, duration_seconds):
    """
    Runs in a separate process.
    Pins itself to a specific CPU core and performs heavy calculations.
    """
    # מנסים להיצמד לליבה, אבל לא קורסים אם זה נכשל
    try:
        p = psutil.Process(os.getpid())
        p.cpu_affinity([int(core_id)])
    except Exception as e:
        print(f"Warning: Could not pin to core {core_id}, continuing anyway. Error: {e}")
        # מחקנו את ה-return שהיה כאן!

    print(f"--- Starting Stress on Core {core_id} for {duration_seconds} seconds ---")
    
    # Calculate end time (Now + Seconds)
    t_end = time.time() + float(duration_seconds)
    
    # Mathematical load loop
    while time.time() < t_end:
        # פעולה מתמטית פשוטה שמעמיסה על המעבד
        _ = 2134234 * 232134.234234

    print(f"--- Finished Stress on Core {core_id} ---")
    
# --- Web Server Routes ---

@app.route('/')
def index():
    cpu_count = psutil.cpu_count(logical=True)
    public_ip = get_public_ip()
    
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CPU Stress Controller</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; padding: 20px; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
            h1 { text-align: center; color: #333; margin-bottom: 10px; }
            .ip-display { text-align: center; color: #666; font-size: 14px; margin-bottom: 30px; background: #eee; display: inline-block; padding: 5px 15px; border-radius: 15px; position: relative; left: 50%; transform: translateX(-50%); }
            
            /* Grid for Core Selection */
            .cores-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 10px; margin-bottom: 20px; }
            .core-item { background: #e9ecef; padding: 10px; text-align: center; border-radius: 8px; user-select: none; }
            .core-item input { margin-right: 5px; }
            
            /* Controls Section */
            .controls { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border: 1px solid #dee2e6; }
            input[type="number"] { padding: 8px; font-size: 16px; width: 80px; text-align: center; border: 1px solid #ced4da; border-radius: 4px; }
            
            /* Buttons */
            .btn { color: white; border: none; padding: 12px 24px; font-size: 16px; border-radius: 6px; cursor: pointer; transition: 0.2s; margin: 5px; }
            .btn-start { background-color: #dc3545; }
            .btn-start:hover { background-color: #c82333; }
            .btn-stop { background-color: #333; }
            .btn-stop:hover { background-color: #000; }
            
            /* Monitor Section */
            .monitor-section { margin-top: 40px; }
            .monitor-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 15px; }
            .monitor-card { background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
            .core-label { font-weight: bold; font-size: 14px; margin-bottom: 5px; display: flex; justify-content: space-between; }
            .progress-bg { background-color: #e9ecef; height: 10px; border-radius: 5px; overflow: hidden; }
            .progress-fill { height: 100%; background-color: #28a745; width: 0%; transition: width 0.5s ease-in-out, background-color 0.5s; }
            
            #status-msg { margin-top: 15px; font-weight: bold; color: #0056b3; min-height: 24px;}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>CPU Stress Controller</h1>
            <div class="ip-display">Machine Public IP: <strong>{{ public_ip }}</strong></div>

            <form id="stressForm">
                <div class="cores-grid">
                    {% for i in range(cpu_count) %}
                    <div class="core-item">
                        <label>
                            <input type="checkbox" name="cores" value="{{i}}"> Core {{i}}
                        </label>
                    </div>
                    {% endfor %}
                </div>

                <div class="controls">
                    <label>Duration:</label>
                    <input type="number" id="seconds" value="30" min="1" max="3600"> Seconds
                    <br><br>
                    <button type="submit" class="btn btn-start">🔥 Start Stress</button>
                    <button type="button" id="stopBtn" class="btn btn-stop">🛑 Stop All</button>
                    <div id="status-msg"></div>
                </div>
            </form>

            <div class="monitor-section">
                <h2 style="border-bottom: 2px solid #eee; padding-bottom: 10px;">Real-Time Monitor</h2>
                <div class="monitor-grid" id="monitorGrid">
                    {% for i in range(cpu_count) %}
                    <div class="monitor-card">
                        <div class="core-label">
                            <span>Core {{i}}</span>
                            <span id="text-core-{{i}}">0%</span>
                        </div>
                        <div class="progress-bg">
                            <div class="progress-fill" id="bar-core-{{i}}"></div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <script>
            const statusDiv = document.getElementById('status-msg');

            // --- Handle START Submission ---
            document.getElementById('stressForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const cores = [];
                document.querySelectorAll('input[name="cores"]:checked').forEach(cb => cores.push(cb.value));
                const seconds = document.getElementById('seconds').value;

                if (cores.length === 0) {
                    alert("Select at least one core!");
                    return;
                }

                statusDiv.innerText = "Launching stress processes...";
                statusDiv.style.color = "blue";
                
                try {
                    const response = await fetch('/start_stress', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ cores: cores, seconds: seconds })
                    });
                    const res = await response.json();
                    statusDiv.innerText = res.message;
                } catch (err) {
                    statusDiv.innerText = "Error: " + err;
                }
            });

            // --- Handle STOP Button ---
            document.getElementById('stopBtn').addEventListener('click', async function() {
                statusDiv.innerText = "Stopping all processes...";
                statusDiv.style.color = "red";
                try {
                    const response = await fetch('/stop_stress', { method: 'POST' });
                    const res = await response.json();
                    statusDiv.innerText = res.message;
                } catch (err) {
                    statusDiv.innerText = "Error stopping: " + err;
                }
            });

            // --- Real-Time Monitoring Loop ---
            async function updateMonitor() {
                try {
                    const response = await fetch('/cpu_status');
                    const data = await response.json();
                    
                    data.usage.forEach((usage, index) => {
                        const bar = document.getElementById(`bar-core-${index}`);
                        const text = document.getElementById(`text-core-${index}`);
                        if (bar && text) {
                            bar.style.width = usage + '%';
                            text.innerText = usage.toFixed(1) + '%';
                            
                            if (usage > 80) bar.style.backgroundColor = '#dc3545';
                            else if (usage > 50) bar.style.backgroundColor = '#ffc107';
                            else bar.style.backgroundColor = '#28a745';
                        }
                    });
                } catch (e) { console.log("Monitor error:", e); }
            }

            setInterval(updateMonitor, 1000);
            updateMonitor();
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template, cpu_count=cpu_count, public_ip=public_ip)

@app.route('/start_stress', methods=['POST'])
def start_stress():
    global RUNNING_PROCESSES
    
    data = request.json
    cores = data.get('cores', [])
    # Get 'seconds' from the request, default to 30 if missing
    seconds = float(data.get('seconds', 30))

    if not cores:
        return jsonify({"status": "error", "message": "No cores selected"}), 400

    count_started = 0
    for core_id in cores:
        p = multiprocessing.Process(target=stress_worker, args=(core_id, seconds))
        p.start()
        RUNNING_PROCESSES.append(p)
        count_started += 1

    return jsonify({"status": "success", "message": f"Started stress on {count_started} cores for {seconds}s."})

@app.route('/stop_stress', methods=['POST'])
def stop_stress():
    global RUNNING_PROCESSES
    count = 0
    for p in RUNNING_PROCESSES:
        if p.is_alive():
            p.terminate()
            count += 1
    RUNNING_PROCESSES = []
    return jsonify({"status": "success", "message": f"Stopped {count} active stress processes."})

@app.route('/cpu_status')
def cpu_status():
    usage = psutil.cpu_percent(percpu=True, interval=None)
    return jsonify({"usage": usage})

if __name__ == '__main__':
    psutil.cpu_percent(percpu=True, interval=None)
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
