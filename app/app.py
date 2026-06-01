import time
import sys
from flask import Flask, jsonify, request, render_template_string
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

REQUEST_COUNT = Counter(
    "fps_tracker_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

ACTIVE_SESSIONS = Gauge(
    "fps_tracker_active_sessions",
    "Number of active sessions"
)

REQUEST_DURATION = Histogram(
    "fps_tracker_request_duration_seconds",
    "HTTP request duration in seconds",
    ["endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

PLAYER_KD = Gauge(
    "fps_tracker_player_kd_ratio",
    "Player K/D ratio",
    ["player", "game"]
)

PLAYER_WINS = Gauge(
    "fps_tracker_player_wins_total",
    "Player total wins",
    ["player", "game"]
)

PLAYER_HOURS = Gauge(
    "fps_tracker_player_hours_played",
    "Player hours played",
    ["player", "game"]
)

STAT_UPDATES = Counter(
    "fps_tracker_stat_updates_total",
    "Total stat updates per player",
    ["player"]
)

PLAYERS = {
    "ShadowFPS": {
        "game": "CS2",
        "kills": 4820,
        "deaths": 2100,
        "wins": 312,
        "losses": 188,
        "hours_played": 1240.5,
        "headshot_pct": 48.3,
        "rank": "Global Elite"
    },
    "ValoAce": {
        "game": "Valorant",
        "kills": 6340,
        "deaths": 3980,
        "wins": 428,
        "losses": 302,
        "hours_played": 890.0,
        "headshot_pct": 31.7,
        "rank": "Radiant"
    },
    "WarzonePro": {
        "game": "Call of Duty",
        "kills": 9120,
        "deaths": 5640,
        "wins": 187,
        "losses": 413,
        "hours_played": 2100.0,
        "headshot_pct": 22.4,
        "rank": "Top 250"
    }
}


def _init_metrics():
    for name, data in PLAYERS.items():
        kd = data["kills"] / data["deaths"] if data["deaths"] > 0 else 0
        PLAYER_KD.labels(player=name, game=data["game"]).set(kd)
        PLAYER_WINS.labels(player=name, game=data["game"]).set(data["wins"])
        PLAYER_HOURS.labels(player=name, game=data["game"]).set(data["hours_played"])


_init_metrics()

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FPS Tracker — Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #0c0c0e;
    --surface: #141418;
    --border: #1e1e26;
    --cs2: #e8ff57;
    --cod: #57d4ff;
    --valo: #ff5757;
    --text: #e8e8f0;
    --muted: #6b6b80;
    --green: #4ade80;
    --orange: #fb923c;
  }
  body { background: var(--bg); color: var(--text); font-family: 'DM Mono', monospace; min-height: 100vh; }
  header { display: flex; align-items: center; justify-content: space-between; padding: 24px 40px; border-bottom: 1px solid var(--border); }
  header h1 { font-family: 'Syne', sans-serif; font-size: 1.6rem; font-weight: 800; letter-spacing: -0.02em; }
  header h1 span { color: var(--cs2); }
  .pill { display: flex; align-items: center; gap: 8px; background: #1a2a1a; border: 1px solid #2a4a2a; border-radius: 999px; padding: 6px 14px; font-size: 0.72rem; color: #6fff6f; }
  .dot { width: 7px; height: 7px; border-radius: 50%; background: #4ade80; animation: pulse 1.5s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
  main { max-width: 1100px; margin: 0 auto; padding: 40px 20px; }
  .section-title { font-family: 'Syne', sans-serif; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.15em; text-transform: uppercase; color: var(--muted); margin-bottom: 20px; }
  .cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; margin-bottom: 48px; }
  .card { background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 28px; animation: fadeUp 0.4s ease both; }
  .card:nth-child(1) { animation-delay: 0.05s; }
  .card:nth-child(2) { animation-delay: 0.12s; }
  .card:nth-child(3) { animation-delay: 0.19s; }
  @keyframes fadeUp { from{opacity:0;transform:translateY(18px)} to{opacity:1;transform:translateY(0)} }
  .card-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px; }
  .player-name { font-family: 'Syne', sans-serif; font-size: 1.15rem; font-weight: 700; }
  .game-badge { font-size: 0.7rem; padding: 4px 10px; border-radius: 6px; font-weight: 500; margin-top: 4px; display: inline-block; }
  .cs2 { color: var(--cs2); border: 1px solid var(--cs2)22; background: var(--cs2)11; }
  .valorant { color: var(--valo); border: 1px solid var(--valo)22; background: var(--valo)11; }
  .cod { color: var(--cod); border: 1px solid var(--cod)22; background: var(--cod)11; }
  .kd-big { font-family: 'Syne', sans-serif; font-size: 2.4rem; font-weight: 800; line-height: 1; }
  .kd-label { font-size: 0.65rem; color: var(--muted); margin-top: 2px; }
  .kd-green { color: var(--green); }
  .kd-orange { color: var(--orange); }
  .kd-red { color: var(--valo); }
  .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 20px; }
  .stat { background: var(--bg); border-radius: 10px; padding: 12px; }
  .stat-val { font-size: 1.05rem; font-weight: 500; }
  .stat-key { font-size: 0.62rem; color: var(--muted); margin-top: 2px; }
  .rank-row { margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
  .rank-val { font-size: 0.85rem; }
  .rank-key { font-size: 0.62rem; color: var(--muted); }
  .form-section { background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 32px; margin-bottom: 40px; }
  .form-section h2 { font-family: 'Syne', sans-serif; font-size: 1rem; font-weight: 700; margin-bottom: 20px; }
  .form-row { display: flex; gap: 12px; flex-wrap: wrap; }
  .form-group { display: flex; flex-direction: column; gap: 6px; min-width: 120px; }
  label { font-size: 0.65rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.1em; }
  select, input[type=number] { background: var(--bg); border: 1px solid var(--border); border-radius: 8px; color: var(--text); padding: 10px 12px; font-family: 'DM Mono', monospace; font-size: 0.85rem; outline: none; }
  select:focus, input[type=number]:focus { border-color: var(--cs2); }
  .submit-btn { align-self: flex-end; background: var(--cs2); color: #0c0c0e; border: none; border-radius: 8px; padding: 10px 24px; font-family: 'Syne', sans-serif; font-weight: 700; font-size: 0.85rem; cursor: pointer; margin-top: 20px; }
  .submit-btn:hover { opacity: 0.85; }
  #session-msg { margin-top: 12px; font-size: 0.8rem; color: var(--green); min-height: 1.2em; }
  .links { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 8px; }
  .links a { color: var(--cs2); font-size: 0.8rem; text-decoration: none; border: 1px solid var(--cs2)33; padding: 6px 14px; border-radius: 8px; }
  .links a:hover { background: var(--cs2)11; }
  .links .valo-link { color: var(--valo); border-color: var(--valo)33; }
  .links .valo-link:hover { background: var(--valo)11; }
  .links .cod-link { color: var(--cod); border-color: var(--cod)33; }
  .links .cod-link:hover { background: var(--cod)11; }
</style>
</head>
<body>
<header>
  <h1>FPS<span>Tracker</span></h1>
  <div class="pill"><span class="dot"></span>LIVE &middot; Prometheus actif</div>
</header>
<main>
  <p class="section-title">Joueurs suivis</p>
  <div class="cards">
    {% for name, p in players.items() %}
    {% set kd = (p.kills / p.deaths) if p.deaths > 0 else 0 %}
    {% set wr = (p.wins / (p.wins + p.losses) * 100) if (p.wins + p.losses) > 0 else 0 %}
    <div class="card">
      <div class="card-header">
        <div>
          <div class="player-name">{{ name }}</div>
          <span class="game-badge {% if p.game == 'CS2' %}cs2{% elif p.game == 'Valorant' %}valorant{% else %}cod{% endif %}">{{ p.game }}</span>
        </div>
        <div style="text-align:right">
          <div class="kd-big {% if kd >= 2 %}kd-green{% elif kd >= 1 %}kd-orange{% else %}kd-red{% endif %}">{{ "%.2f"|format(kd) }}</div>
          <div class="kd-label">K/D RATIO</div>
        </div>
      </div>
      <div class="stats-grid">
        <div class="stat"><div class="stat-val">{{ p.kills }}</div><div class="stat-key">Kills</div></div>
        <div class="stat"><div class="stat-val">{{ p.deaths }}</div><div class="stat-key">Deaths</div></div>
        <div class="stat"><div class="stat-val">{{ "%.1f"|format(wr) }}%</div><div class="stat-key">Win Rate</div></div>
        <div class="stat"><div class="stat-val">{{ "%.1f"|format(p.headshot_pct) }}%</div><div class="stat-key">Headshot %</div></div>
      </div>
      <div class="rank-row">
        <div><div class="rank-val">{{ p.rank }}</div><div class="rank-key">RANG</div></div>
        <div style="text-align:right"><div class="rank-val">{{ "%.0f"|format(p.hours_played) }}h</div><div class="rank-key">TEMPS DE JEU</div></div>
      </div>
    </div>
    {% endfor %}
  </div>

  <div class="form-section">
    <h2>Enregistrer une session</h2>
    <div class="form-row">
      <div class="form-group">
        <label>Joueur</label>
        <select id="sess-player">
          {% for name in players.keys() %}
          <option value="{{ name }}">{{ name }}</option>
          {% endfor %}
        </select>
      </div>
      <div class="form-group">
        <label>Kills</label>
        <input type="number" id="sess-kills" value="20" min="0">
      </div>
      <div class="form-group">
        <label>Deaths</label>
        <input type="number" id="sess-deaths" value="10" min="0">
      </div>
      <div class="form-group">
        <label>Victoire</label>
        <select id="sess-win">
          <option value="true">Oui</option>
          <option value="false">Non</option>
        </select>
      </div>
      <div class="form-group">
        <label>Heures</label>
        <input type="number" id="sess-hours" value="1.5" min="0" step="0.5">
      </div>
    </div>
    <button class="submit-btn" onclick="submitSession()">Enregistrer</button>
    <div id="session-msg"></div>
  </div>

  <p class="section-title">Endpoints API</p>
  <div class="links">
    <a href="/api/players">GET /api/players</a>
    <a href="/api/leaderboard">GET /api/leaderboard</a>
    <a href="/health">GET /health</a>
    <a href="/metrics" class="cod-link">GET /metrics</a>
  </div>
</main>
<script>
async function submitSession() {
  const player = document.getElementById('sess-player').value;
  const body = {
    kills: parseInt(document.getElementById('sess-kills').value) || 0,
    deaths: parseInt(document.getElementById('sess-deaths').value) || 0,
    win: document.getElementById('sess-win').value === 'true',
    hours: parseFloat(document.getElementById('sess-hours').value) || 0
  };
  const msg = document.getElementById('session-msg');
  try {
    const res = await fetch('/api/players/' + player + '/session', {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)
    });
    const data = await res.json();
    if (res.ok) {
      msg.style.color = '#4ade80';
      msg.textContent = 'Session enregistrée — nouveau K/D : ' + data.new_kd.toFixed(2) + ' | Victoires : ' + data.new_wins;
      setTimeout(() => location.reload(), 1200);
    } else {
      msg.style.color = '#ff5757';
      msg.textContent = data.error || 'Erreur';
    }
  } catch(e) {
    msg.style.color = '#ff5757';
    msg.textContent = 'Erreur réseau';
  }
}
</script>
</body>
</html>"""


@app.before_request
def before_request():
    request.start_time = time.time()
    ACTIVE_SESSIONS.inc()


@app.after_request
def after_request(response):
    duration = time.time() - request.start_time
    endpoint = request.path
    REQUEST_DURATION.labels(endpoint=endpoint).observe(duration)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=endpoint,
        status=str(response.status_code)
    ).inc()
    ACTIVE_SESSIONS.dec()
    return response


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, players=PLAYERS)


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "fps-tracker",
        "version": "1.0.0",
        "players_tracked": len(PLAYERS)
    })


@app.route("/api/players")
def get_players():
    result = {}
    for name, data in PLAYERS.items():
        p = dict(data)
        p["kd_ratio"] = round(p["kills"] / p["deaths"], 3) if p["deaths"] > 0 else 0
        total = p["wins"] + p["losses"]
        p["win_rate"] = round(p["wins"] / total * 100, 1) if total > 0 else 0
        result[name] = p
    return jsonify(result)


@app.route("/api/players/<name>")
def get_player(name):
    if name not in PLAYERS:
        return jsonify({"error": f"Player '{name}' not found"}), 404
    p = dict(PLAYERS[name])
    p["kd_ratio"] = round(p["kills"] / p["deaths"], 3) if p["deaths"] > 0 else 0
    total = p["wins"] + p["losses"]
    p["win_rate"] = round(p["wins"] / total * 100, 1) if total > 0 else 0
    return jsonify(p)


@app.route("/api/players/<name>/session", methods=["POST"])
def add_session(name):
    if name not in PLAYERS:
        return jsonify({"error": f"Player '{name}' not found"}), 404
    body = request.get_json(force=True) or {}
    kills = int(body.get("kills", 0))
    deaths = int(body.get("deaths", 0))
    win = bool(body.get("win", False))
    hours = float(body.get("hours", 0))

    p = PLAYERS[name]
    p["kills"] += kills
    p["deaths"] += deaths
    p["hours_played"] += hours
    if win:
        p["wins"] += 1
    else:
        p["losses"] += 1

    kd = round(p["kills"] / p["deaths"], 3) if p["deaths"] > 0 else 0
    PLAYER_KD.labels(player=name, game=p["game"]).set(kd)
    PLAYER_WINS.labels(player=name, game=p["game"]).set(p["wins"])
    PLAYER_HOURS.labels(player=name, game=p["game"]).set(p["hours_played"])
    STAT_UPDATES.labels(player=name).inc()

    return jsonify({
        "player": name,
        "new_kd": kd,
        "new_wins": p["wins"],
        "message": "Session recorded"
    })


@app.route("/api/leaderboard")
def leaderboard():
    board = []
    for name, data in PLAYERS.items():
        p = dict(data)
        p["name"] = name
        p["kd_ratio"] = round(p["kills"] / p["deaths"], 3) if p["deaths"] > 0 else 0
        board.append(p)
    board.sort(key=lambda x: x["kd_ratio"], reverse=True)
    return jsonify(board)


@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


if __name__ == "__main__":
    port = 5000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    app.run(host="0.0.0.0", port=port, debug=False)
