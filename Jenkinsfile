pipeline {
    agent any
    
    environment {
        DOCKER_COMPOSE_FILE = 'docker-compose.yml'
    }
    
    stages {
        
        stage('Checkout') {
            steps {
                echo 'Checking out code from GitHub...'
                checkout scm
            }
        }
        
        stage('Build') {
            steps {
                echo 'Building Docker images...'
                sh 'docker-compose build'
            }
        }
        
        stage('Test') {
            steps {
                echo 'Running service health checks...'
                sh '''
                    docker-compose up -d
                    sleep 30
                    curl -f http://localhost:8001/health || exit 1
                    curl -f http://localhost:8002/health || exit 1
                    curl -f http://localhost:8003/health || exit 1
                    curl -f http://localhost:8004/health || exit 1
                    curl -f http://localhost:8005/health || exit 1
                    echo "All services healthy!"
                '''
            }
        }
        
        stage('Deploy') {
            steps {
                echo 'Deploying to Kubernetes...'
                sh '''
                    kubectl apply -k infrastructure/kubernetes/base/
                    kubectl rollout status deployment -n crypto-trading-bot --timeout=120s
                '''
            }
        }
        
        stage('Verify') {
            steps {
                echo 'Verifying deployment...'
                sh '''
                    kubectl get pods -n crypto-trading-bot
                    echo "Deployment successful!"
                '''
            }
        }
    }
    
    post {
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
            sh 'docker-compose down'
        }
    }
}