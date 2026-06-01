# FPS Tracker

[![CI/CD](https://github.com/ton-username/fps-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/ton-username/fps-tracker/actions/workflows/ci.yml)

Application de tracking de statistiques FPS (CS2, Valorant, Call of Duty) avec monitoring Prometheus/Grafana et pipeline CI/CD GitHub Actions.

---

## Stack technique

| Composant | Technologie |
|---|---|
| Backend | Flask 3.0 (Python 3.12) |
| Métriques | Prometheus Client 0.20 |
| Monitoring | Prometheus v2.51 |
| Dashboards | Grafana 10.4 |
| Conteneurisation | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| Registry | Docker Hub |

---

## Lancement rapide

```bash
git clone https://github.com/ton-username/fps-tracker.git
cd fps-tracker
docker compose up --build -d
```

---

## URLs

| Service | URL | Auth |
|---|---|---|
| Application | http://localhost:5000 | — |
| Prometheus | http://localhost:9090 | — |
| Grafana | http://localhost:3000 | admin / devops2024 |

---

## Endpoints API

| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/` | Dashboard HTML |
| GET | `/health` | Health check JSON |
| GET | `/api/players` | Tous les joueurs avec K/D et win rate |
| GET | `/api/players/<name>` | Stats d'un joueur |
| POST | `/api/players/<name>/session` | Enregistrer une session |
| GET | `/api/leaderboard` | Classement par K/D décroissant |
| GET | `/metrics` | Métriques Prometheus |

---

## Métriques Prometheus

| Métrique | Type | Description |
|---|---|---|
| `fps_tracker_requests_total` | Counter | Requêtes HTTP totales (method, endpoint, status) |
| `fps_tracker_active_sessions` | Gauge | Sessions actives simultanées |
| `fps_tracker_request_duration_seconds` | Histogram | Durée des requêtes par endpoint |
| `fps_tracker_player_kd_ratio` | Gauge | Ratio K/D par joueur et jeu |
| `fps_tracker_player_wins_total` | Gauge | Victoires totales par joueur |
| `fps_tracker_player_hours_played` | Gauge | Heures jouées par joueur |
| `fps_tracker_stat_updates_total` | Counter | Mises à jour de stats par joueur |

---

## Exemples PromQL

```promql
# Taux de requêtes par seconde
rate(fps_tracker_requests_total[1m])

# K/D ratio de tous les joueurs
fps_tracker_player_kd_ratio

# Durée médiane des requêtes (p50)
histogram_quantile(0.50, rate(fps_tracker_request_duration_seconds_bucket[5m]))

# Durée p95 des requêtes
histogram_quantile(0.95, rate(fps_tracker_request_duration_seconds_bucket[5m]))
```

---

## Pipeline CI/CD

```
push / PR
    │
    ▼
┌─────────┐
│  lint   │  flake8 — erreurs critiques + style
└────┬────┘
     │
     ▼
┌─────────┐
│  test   │  pytest — 9 tests unitaires
└────┬────┘
     │
     ▼
┌─────────┐
│  build  │  docker build + smoke test /health & /leaderboard
└────┬────┘
     │ (main branch only)
     ▼
┌─────────┐
│  push   │  docker push → Docker Hub (sha- + latest)
└─────────┘
```

---

## Secrets GitHub à configurer

| Secret | Description |
|---|---|
| `DOCKERHUB_USERNAME` | Votre nom d'utilisateur Docker Hub |
| `DOCKERHUB_TOKEN` | Token d'accès Docker Hub |

> Settings → Secrets and variables → Actions → New repository secret

---

## Commandes utiles

```bash
# Voir les logs de l'application
docker compose logs -f fps-tracker

# Lancer les tests
pip install -r app/requirements.txt
pytest app/tests/ -v

# Simuler du trafic en boucle
for i in $(seq 1 20); do
  curl -s http://localhost:5000/api/leaderboard > /dev/null
  curl -s http://localhost:5000/health > /dev/null
done

# Arrêter et supprimer les volumes
docker compose down -v
```

---

## Exemple curl — enregistrer une session

```bash
curl -X POST http://localhost:5000/api/players/ShadowFPS/session \
  -H "Content-Type: application/json" \
  -d '{"kills": 25, "deaths": 8, "win": true, "hours": 2.0}'
```

Réponse :

```json
{
  "player": "ShadowFPS",
  "new_kd": 2.31,
  "new_wins": 313,
  "message": "Session recorded"
}
```
