pipeline {
    agent any

    environment {
        // Registry-ul si numele imaginii. GHCR = GitHub Container Registry.
        REGISTRY  = 'ghcr.io'
        IMAGE     = 'ghcr.io/stefcosmin09-glitch/todo-app'

        // GIT_COMMIT e pus la dispozitie de Jenkins (SHA-ul care a declansat
        // build-ul). Tag-uim imaginea cu el, nu cu 'latest', ca fiecare deploy
        // sa fie tracetabil pana la un commit exact. Fallback pentru build manual.
        IMAGE_TAG = "${env.GIT_COMMIT ? env.GIT_COMMIT.take(7) : 'manual'}"

        // ID-ul credentialului Jenkins (username + token) pentru GHCR.
        // Il creezi in Jenkins -> Manage Jenkins -> Credentials -> Add:
        //   ID:       ghcr-credentials
        //   Username: contul tau GitHub
        //   Password: Personal Access Token cu scope-ul `write:packages`
        // Tokenul NU sta in repo; Jenkins il injecteaza doar in timpul build-ului.
        GHCR_CRED = 'ghcr-credentials'
    }

    stages {
        stage('Test') {
            steps {
                // Dockerfile-ul are un target `test` dedicat: instaleaza
                // requirements-dev.txt (pytest inclus) si ruleaza suita ca CMD.
                // Astfel tool-urile de test nu ajung niciodata in imaginea finala.
                sh 'docker build --target test -t todo-app:test .'
                sh 'docker run --rm todo-app:test'
            }
        }

        stage('Build & Publish') {
            steps {
                // Builduim doar targetul `runtime` si il tag-uim cu SHA-ul
                // commitului. Ordinea conteaza: testele trebuie sa treaca
                // inainte ca o imagine sa fie publicata.
                sh "docker build --target runtime -t ${IMAGE}:${IMAGE_TAG} ."

                withCredentials([usernamePassword(
                    credentialsId: env.GHCR_CRED,
                    usernameVariable: 'GHCR_USER',
                    passwordVariable: 'GHCR_TOKEN'
                )]) {
                    // --password-stdin evita tokenul in istoricul comenzilor
                    // si in log-urile Jenkins.
                    sh 'echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USER" --password-stdin'
                    sh "docker push ${IMAGE}:${IMAGE_TAG}"
                }
            }
        }

        stage('Deploy') {
            steps {
                // Helm randarez chartul din charts/todo si injecteaza tag-ul
                // construit mai sus. --wait face stage-ul sa esueze daca podurile
                // nu devin Ready, deci un deploy stricat e vizibil imediat.
                sh "helm upgrade --install todo ./charts/todo --set image.tag=${IMAGE_TAG} --wait"
            }
        }
    }

    post {
        always {
            // Nu lasam tokenul de registry in docker config-ul de pe agent.
            sh 'docker logout ghcr.io || true'
        }
    }
}
