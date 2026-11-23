
import os
import time
import threading
from collections import deque
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

VERSION = os.getenv("APP_VERSION", "v1")
RELEASE_MESSAGE = os.getenv(
    "RELEASE_MESSAGE",
    f"Release Pipeline {VERSION}"
)

# Per-process request counter: rolling five-minute window
request_history = deque()
request_lock = threading.Lock()


def record_request():
    now = time.time()
    cutoff = now - 300

    with request_lock:
        request_history.append(now)

        while request_history and request_history[0] < cutoff:
            request_history.popleft()


def get_request_count():
    cutoff = time.time() - 300

    with request_lock:
        while request_history and request_history[0] < cutoff:
            request_history.popleft()

        return len(request_history)


@app.before_request
def count_requests():
    record_request()


HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#0b1020">
<title>Release Pipeline | Deployment Dashboard</title>

<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    min-height: 100vh;
    font-family: Inter, Arial, sans-serif;
    color: #eef2ff;
    background: radial-gradient(circle at top right, #243b70, #10172a 45%, #090d18);
}

.container { max-width: 1050px; margin: auto; padding: 35px 22px; }

header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 15px;
}

.brand { font-size: 21px; font-weight: 800; letter-spacing: .3px; }
.brand span { color: #7c9cff; }

.live {
    color: #8cf0bb;
    border: 1px solid #28684e;
    background: #123529;
    padding: 9px 14px;
    border-radius: 30px;
    font-size: 12px;
    font-weight: 700;
}

.hero { margin: 65px 0 35px; text-align: center; }
.eyebrow { color: #91a9ff; text-transform: uppercase; letter-spacing: 3px; font-size: 12px; }
h1 { font-size: clamp(34px, 7vw, 58px); margin: 15px 0; }
.subtitle { color: #aab5ce; line-height: 1.7; }

.grid {
    display: grid;
    grid-template-columns: 1.2fr .8fr;
    gap: 20px;
}

.card {
    background: rgba(24, 34, 59, .86);
    border: 1px solid #344363;
    border-radius: 20px;
    padding: 28px;
    box-shadow: 0 18px 50px #0003;
}

.card h2 { margin-top: 0; font-size: 15px; color: #aab8d8; }

.version { font-size: 54px; font-weight: 850; margin: 20px 0 8px; }
.version.v1 { color: #65dfa4; }
.version.v2 { color: #82a6ff; }

.message { color: #aab5ce; }
.status { display: inline-flex; align-items: center; gap: 8px; color: #8cf0bb; font-size: 13px; }
.dot { width: 9px; height: 9px; border-radius: 50%; background: #42d392; box-shadow: 0 0 12px #42d392; }

.metric { font-size: 29px; font-weight: 800; margin: 18px 0 5px; }
.muted { color: #95a3bf; font-size: 13px; }

.info {
    margin-top: 20px;
    display: flex;
    justify-content: space-between;
    gap: 12px;
    border-top: 1px solid #344363;
    padding-top: 17px;
    font-size: 13px;
}

.traffic-card {
    margin-top: 20px;
}

.traffic-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 22px 0 9px;
    font-size: 14px;
}

.traffic-value { font-size: 24px; font-weight: 800; }

.bar {
    width: 100%;
    height: 15px;
    background: #303c55;
    border-radius: 20px;
    overflow: hidden;
    display: flex;
}

.bar-v1 { background: #3b82f6; width: 90%; }
.bar-v2 { background: #16a34a; width: 10%; }

.actual-bar-v1 { background: #3b82f6; width: 0%; }
.actual-bar-v2 { background: #16a34a; width: 0%; }

.legend {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
    margin-top: 14px;
    font-size: 12px;
    color: #aab5ce;
}

.legend span { display: flex; align-items: center; gap: 7px; }

.legend i {
    display: inline-block;
    width: 9px;
    height: 9px;
    border-radius: 50%;
}

footer {
    text-align: center;
    color: #8492ad;
    font-size: 12px;
    margin-top: 35px;
}

@media(max-width:650px) {
    .grid { grid-template-columns: 1fr; }
    .hero { margin-top: 45px; }
    header { align-items: flex-start; }
}
</style>
</head>

<body>
<div class="container">

<header>
    <div class="brand">🚀 RELEASE<span>PIPELINE</span></div>
    <div class="live">● LIVE MONITORING</div>
</header>

<section class="hero">
    <div class="eyebrow">Continuous Integration & Deployment</div>
    <h1>Release Dashboard</h1>
    <p class="subtitle">
        Monitor application deployments, release versions and application health in real time.
    </p>
</section>

<section class="grid">

    <div class="card">
        <h2>ACTIVE APPLICATION RELEASE</h2>

        <div id="version" class="version">Checking...</div>

        <p id="message" class="message">
            Fetching deployment information...
        </p>

        <div class="status">
            <span class="dot"></span>
            <span id="health">Checking application health</span>
        </div>

        <div class="info">
            <span>Application</span>
            <strong id="application">Release Pipeline</strong>
        </div>

        <div class="info">
            <span>Last updated</span>
            <strong id="updated">--</strong>
        </div>
    </div>

    <div class="card">
        <h2>DEPLOYMENT MONITOR</h2>

        <div class="metric">LIVE</div>
        <div class="muted">Application endpoint responding</div>

        <div class="info">
            <span>Deployment strategy</span>
            <strong>Canary Release</strong>
        </div>

        <div class="info">
            <span>Stable version</span>
            <strong>v1</strong>
        </div>

        <div class="info">
            <span>Canary version</span>
            <strong>v2</strong>
        </div>

        <div class="info">
            <span>Configured traffic</span>
            <strong>90% / 10%</strong>
        </div>
    </div>

</section>

<section class="card traffic-card">
    <h2>CANARY TRAFFIC DISTRIBUTION</h2>

    <div class="muted">Configured Ingress traffic weight</div>

    <div class="traffic-row">
        <strong>v1 — Stable</strong>
        <span class="traffic-value" style="color:#60a5fa">90%</span>
    </div>

    <div class="bar">
        <div class="bar-v1"></div>
        <div class="bar-v2"></div>
    </div>

    <div class="traffic-row">
        <strong>v2 — Canary</strong>
        <span class="traffic-value" style="color:#4ade80">10%</span>
    </div>

    <div class="info">
        <span>Traffic routing</span>
        <strong>NGINX Ingress</strong>
    </div>

    <div class="info">
        <span>Canary status</span>
        <strong id="canary-status">Configured at 10%</strong>
    </div>

    <p class="muted" style="margin-top:18px">
        Traffic weight is configured at the Ingress level.
        Actual distribution is probabilistic and should be verified
        using a sufficiently large request sample.
    </p>
</section>

<footer>
    Release Pipeline Project · Docker · Kubernetes · Jenkins · Minikube
    <br><br>Dashboard refreshes automatically every 5 seconds.
</footer>

</div>

<script>
async function refreshDashboard() {
    try {
        const response = await fetch('/api/info', { cache: 'no-store' });

        if (!response.ok) throw new Error('Application unavailable');

        const data = await response.json();

        const version = document.getElementById('version');

        version.textContent = data.version.toUpperCase();
        version.className = 'version ' + (data.version === 'v2' ? 'v2' : 'v1');

        document.getElementById('message').textContent = data.message;
        document.getElementById('health').textContent = 'Application healthy';
        document.getElementById('application').textContent = data.application;
        document.getElementById('updated').textContent = new Date().toLocaleTimeString();

    } catch (error) {
        document.getElementById('version').textContent = 'Unavailable';
        document.getElementById('health').textContent = 'Health check failed';
    }
}

refreshDashboard();
setInterval(refreshDashboard, 5000);
</script>

</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/api/info")
def info():
    return jsonify({
        "application": "Release Pipeline",
        "version": VERSION,
        "message": RELEASE_MESSAGE,
        "status": "healthy"
    })


@app.route("/api/traffic")
def traffic():
    return jsonify({
        "version": VERSION,
        "requests": get_request_count(),
        "window_seconds": 300
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "version": VERSION
    })
