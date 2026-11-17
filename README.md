# 🚀 CI/CD Pipeline — Flask To-Do List

Proiect realizat în cadrul cursului **DevOps Online — IT School**.

Pipeline CI/CD complet pentru o aplicație web Python, utilizând Jenkins, Docker, Kubernetes și Prometheus/Grafana.

> **Notă de scop:** aplicația ține taskurile în memorie (demo). Nu e pregătită
> pentru producție; vezi [Roadmap](#roadmap) pentru pașii următori.

---

## 📋 Cuprins

- [Descriere](#descriere)
- [Arhitectură](#arhitectură)
- [Tehnologii folosite](#tehnologii-folosite)
- [Structura proiectului](#structura-proiectului)
- [Instalare și rulare](#instalare-și-rulare)
- [Pipeline CI/CD](#pipeline-cicd)
- [Kubernetes](#kubernetes)
- [Monitoring](#monitoring)
- [Roadmap](#roadmap)

---

## 📖 Descriere

Aplicația este un **To-Do List** dezvoltat în Python cu Flask. Proiectul demonstrează un flux complet DevOps:

1. Dezvoltatorul face commit pe GitHub
2. Jenkins detectează automat commit-ul prin webhook
3. Jenkins rulează testele într-un target Docker dedicat (`--target test`)
4. Jenkins construiește imaginea de runtime și o tag-uiește cu SHA-ul commitului
5. Jenkins publică imaginea în GitHub Container Registry (GHCR)
6. Jenkins deployează cu `helm upgrade --install` în Kubernetes (**1 replică**, demo)
7. Prometheus și Grafana monitorizează aplicația

---

## 🏗️ Arhitectură

```
Developer → GitHub → Webhook → Jenkins
                                   ↓
                       docker build --target test
                                   ↓
                          pytest în container
                                   ↓
                    docker build --target runtime
                                   ↓
                       docker push → GHCR (tag = SHA)
                                   ↓
                    helm upgrade --install (1 replică)
                                   ↓
                       Prometheus + Grafana (monitoring)
```

---

## 🛠️ Tehnologii folosite

| Tehnologie | Versiune | Rol |
|-----------|---------|-----|
| Python | 3.12 | Limbaj de programare |
| Flask | 3.1.3 | Web framework |
| Docker | 29.2.1 | Containerizare (build multi-stage) |
| Jenkins | LTS | CI/CD orchestration |
| Kubernetes | 1.35.1 | Container orchestration |
| Minikube | 1.38.1 | Kubernetes local |
| Helm | 3.21.3 | Package manager K8s |
| Prometheus | latest | Metrics collection |
| Grafana | latest | Metrics visualization |
| pytest | 9.1.1 | Testing |
| GHCR | — | Container registry |
| ngrok | latest | Webhook tunnel |
| Git | 2.43.0 | Version control |

---

## 📁 Structura proiectului

```
proiect-itschool/
├── app.py                      # Aplicația Flask + metrici Prometheus
├── Dockerfile                  # Multi-stage: builder / test / runtime
├── Jenkinsfile                 # Pipeline: test → build & push → Helm deploy
├── deployment.yaml             # Manifest simplu, doar ca referință / backup
├── requirements.txt            # Dependențe de runtime (pin-uite)
├── requirements-dev.txt        # Dependențe doar pentru teste (pytest)
├── test_app.py                 # Teste automate pytest
├── .dockerignore               # ține .git, .venv, .env etc. afară din imagine
├── charts/todo/                # Helm chart (modul recomandat de deploy)
│   ├── Chart.yaml
│   ├── values.yaml             # replicaCount, resurse, probe, PDB, NetworkPolicy
│   └── templates/              # deployment, service, probes, ServiceMonitor,
│                               #   NetworkPolicy, smoke-test etc.
└── README.md                   # Documentație
```

---

## 🚀 Instalare și rulare

### Cerințe

- Docker
- Jenkins (cu plugin-urile Docker, Pipeline și credentialul `ghcr-credentials`)
- Minikube
- kubectl
- Helm
- Python 3.12+

### Rulare locală

```bash
# Clonează repo-ul
git clone https://github.com/stefcosmin09-glitch/proiect-itschool.git
cd proiect-itschool

# Instalează dependențele
pip install -r requirements.txt

# Rulează aplicația (doar pentru dezvoltare locală)
python3 app.py
```

Deschide browserul la `http://localhost:5000`.

### Rulare cu Docker

```bash
# Rulează testele în targetul dedicat (pytest e instalat doar aici)
docker build --target test -t todo-app:test .
docker run --rm todo-app:test

# Construiește imaginea de producție (rulează gunicorn, user non-root)
docker build --target runtime -t todo-app:local .

# Rulează containerul
docker run -d -p 5000:5000 --name todo-app todo-app:local
```

> 💡 **De ce `--target test`?** Imaginea `runtime` nu conține pytest (ca să
> rămână mică și sigură). Comanda veche `docker run --rm myapp pytest` nu mai
> funcționează cu Dockerfile-ul multi-stage — testele au propriul target.

---

## 🔄 Pipeline CI/CD

Pipeline-ul Jenkins are 3 stage-uri, definite în `Jenkinsfile`:

### 1. Test

```groovy
sh 'docker build --target test -t todo-app:test .'
sh 'docker run --rm todo-app:test'
```

### 2. Build & Publish

```groovy
sh "docker build --target runtime -t ${IMAGE}:${IMAGE_TAG} ."
// login GHCR cu credentialul Jenkins `ghcr-credentials`, apoi:
sh "docker push ${IMAGE}:${IMAGE_TAG}"
```

`IMAGE_TAG` este SHA-ul commitului care a declanșat build-ul (7 caractere),
nu `latest`. Așa imaginea deployată e mereu legată de un commit concret.

### 3. Deploy

```groovy
sh "helm upgrade --install todo ./charts/todo --set image.tag=${IMAGE_TAG} --wait"
```

### Configurare Jenkins (o singură dată)

1. **Credential GHCR** — `Manage Jenkins → Credentials → Add Credentials`:
   - ID: `ghcr-credentials`
   - Username: contul tău GitHub
   - Password: Personal Access Token cu scope `write:packages`
2. **Webhook GitHub** — `Settings → Webhooks → Add webhook`:
   - Payload URL: `http://<adresa-jenkins>/github-webhook/` (prin ngrok în demo)
   - Content type: `application/json`
   - Events: `Just the push event`

Tokenul și webhook-ul nu sunt în repo — Jenkins le injectează la build.

---

## ☸️ Kubernetes

Modul recomandat de deploy este **Helm chartul** din `charts/todo/`.

```bash
# Deploy / upgrade
helm upgrade --install todo ./charts/todo \
  --set image.tag=<sha-commit> \
  --namespace default --wait

# Verificare
kubectl get pods
kubectl get svc todo

# Acces aplicație (în Minikube)
minikube service todo --url
```

### De ce 1 replică?

`values.yaml` setează `replicaCount: 1` (și `autoscaling.minReplicas: 1`).
Aplicația ține taskurile într-un dicționar în memoria procesului — cu 2+
replici, un task adăugat pe o replică nu apare pe cealaltă și se pierde la
restart. De aceea **PDB-ul e dezactivat** cât timp există o singură replică
(un `minAvailable: 1` ar bloca complet drain-ul nodului).

Când trecem la Postgres + migrări, `replicaCount` și PDB-ul pot fi ridicate.
Chartul conține deja probe (`/healthz`, `/readyz`), resurse, `securityContext`,
`NetworkPolicy` și `ServiceMonitor` pregătite pentru acel pas.

> `deployment.yaml` rămâne în repo doar ca exemplu minimal de referință;
> pentru deploy real folosește chartul Helm.

### Test smoke în cluster

```bash
helm test todo
```

Rulesază jobul din `charts/todo/templates/tests/smoke-test.yaml`.

---

## 📊 Monitoring

Prometheus și Grafana instalate cu Helm în namespace-ul `monitoring`.

```bash
# Instalare
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace

# Acces Grafana
kubectl --namespace monitoring port-forward service/monitoring-grafana 3000:80
```

Deschide Grafana la `http://localhost:3000`:
- Username: `admin`
- Dashboard: `Kubernetes / Compute Resources / Cluster`

Aplicația expune metrici la `/metrics` (`todo_http_requests_total`,
`todo_http_request_duration_seconds`, `todo_tasks_in_memory`), iar chartul
activează un `ServiceMonitor` care le descoperă automat.

---

## 🗺️ Roadmap

Lucrurile pe care vreau să le fac în continuare, în ordinea priorității:

1. **Persistență reală** — Postgres + Alembic în loc de dict în memorie;
   apoi `replicaCount` poate crește la 2 și PDB-ul se reactivează.
2. **Securitate web** — `/delete` pe `POST` cu token CSRF (în prezent e `GET`)
   și autentificare minimă pentru `/add`.
3. **Teste extinse** — concurență între workeri, comportament multiproc pentru
   `/metrics`, și `helm lint` / `kubectl` smoke în CI.
4. **Pinning complet** — hash-uri în `requirements*.txt` (`pip-compile
   --generate-hashes`) și versiune Python fixă în Dockerfile.
5. **Git history** — squash-uiască commit-urile vechi de test webhook.

---

## 👤 Autor

**Gheorghe Ștefăniță Cosmin**
Junior DevOps Engineer
[GitHub](https://github.com/stefcosmin09-glitch)
