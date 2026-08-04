# 🚀 CI/CD Pipeline — Flask To-Do List

Proiect realizat în cadrul cursului **DevOps Online — IT School**.

Pipeline CI/CD complet pentru o aplicație web Python, utilizând Jenkins, Docker, Kubernetes și Prometheus/Grafana.

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

---

## 📖 Descriere

Aplicația este un **To-Do List** dezvoltat în Python cu Flask. Proiectul demonstrează un flux complet DevOps:

1. Dezvoltatorul face commit pe GitHub
2. Jenkins detectează automat commit-ul prin webhook
3. Jenkins face build la imaginea Docker
4. Jenkins rulează testele automate cu pytest
5. Jenkins deployează aplicația în container Docker
6. Aplicația rulează în Kubernetes cu 2 replici
7. Prometheus și Grafana monitorizează infrastructura

---

## 🏗️ Arhitectură

```
Developer → GitHub → Webhook → Jenkins
                                  ↓
                            docker build
                                  ↓
                            pytest tests
                                  ↓
                            docker deploy
                                  ↓
                          Kubernetes (2 replici)
                                  ↓
                      Prometheus + Grafana (monitoring)
```

---

## 🛠️ Tehnologii folosite

| Tehnologie | Versiune | Rol |
|-----------|---------|-----|
| Python | 3.12.3 | Limbaj de programare |
| Flask | 3.1.3 | Web framework |
| Docker | 29.2.1 | Containerizare |
| Jenkins | LTS | CI/CD orchestration |
| Kubernetes | 1.35.1 | Container orchestration |
| Minikube | 1.38.1 | Kubernetes local |
| Helm | 3.21.3 | Package manager K8s |
| Prometheus | latest | Metrics collection |
| Grafana | latest | Metrics visualization |
| pytest | 9.1.1 | Testing |
| ngrok | latest | Webhook tunnel |
| Git | 2.43.0 | Version control |

---

## 📁 Structura proiectului

```
proiect-itschool/
├── app.py              # Aplicația Flask
├── Dockerfile          # Configurare container Docker
├── Jenkinsfile         # Pipeline CI/CD
├── deployment.yaml     # Kubernetes deployment + service
├── requirements.txt    # Dependențe Python
├── test_app.py         # Teste automate pytest
└── README.md           # Documentație
```

---

## 🚀 Instalare și rulare

### Cerințe
- Docker
- Jenkins
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

# Rulează aplicația
python3 app.py
```

Deschide browserul la `http://localhost:5000`

### Rulare cu Docker

```bash
# Build imagine
docker build -t myapp .

# Rulează containerul
docker run -d -p 5000:5000 --name myapp myapp
```

---

## 🔄 Pipeline CI/CD

Pipeline-ul Jenkins are 3 stage-uri:

### 1. Build
```groovy
stage('Build') {
    steps {
        sh 'docker build -t myapp .'
    }
}
```

### 2. Test
```groovy
stage('Test') {
    steps {
        sh 'docker run --rm myapp pytest'
    }
}
```

### 3. Deploy
```groovy
stage('Deploy') {
    steps {
        sh 'docker stop myapp || true'
        sh 'docker rm myapp || true'
        sh 'docker run -d -p 5000:5000 --name myapp myapp'
    }
}
```

### Webhook GitHub
Pipeline-ul se declanșează automat la fiecare `git push` prin webhook GitHub → ngrok → Jenkins.

---

## ☸️ Kubernetes

Aplicația rulează în Kubernetes cu **2 replici** pentru high availability.

```bash
# Deploy în Kubernetes
kubectl apply -f deployment.yaml

# Verificare pod-uri
kubectl get pods

# Acces aplicație
minikube service myapp-service --url
```

### deployment.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myapp:latest
        imagePullPolicy: Never
        ports:
        - containerPort: 5000
---
apiVersion: v1
kind: Service
metadata:
  name: myapp-service
spec:
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 5000
  type: NodePort
```

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

Deschide Grafana la `http://localhost:3000`
- Username: `admin`
- Dashboard: `Kubernetes / Compute Resources / Cluster`

---

## 👤 Autor

**Gheorghe Ștefăniță Cosmin**
Junior DevOps Engineer
[GitHub](https://github.com/stefcosmin09-glitch)
