pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                sh 'docker build -t myapp .'
            }
        }
        stage('Test') {
            steps {
                sh 'docker run --rm myapp pytest'
            }
        }
        stage('Deploy') {
            steps {
                sh 'docker stop myapp || true'
                sh 'docker rm myapp || true'
                sh 'docker run -d -p 5000:5000 --name myapp myapp'
            }
        }
    }
}