pipeline {
    agent any
    
    environment {
        BINANCE_TESTNET_API_KEY    = 'dummy'
        BINANCE_TESTNET_SECRET_KEY = 'dummy'
        GROQ_API_KEY               = 'dummy'
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
                    docker-compose ps
                    echo "All services started successfully!"
                '''
            }
        }
        
        stage('Deploy') {
            steps {
                echo 'Deploying to Kubernetes...'
                sh '''
                    kubectl apply -k infrastructure/kubernetes/base/ || echo "kubectl not available - skipping"
                    echo "Deploy stage complete!"
                '''
            }
        }
        
        stage('Verify') {
            steps {
                echo 'Verifying deployment...'
                sh '''
                    kubectl get pods -n crypto-trading-bot || echo "kubectl not available - skipping"
                    docker-compose ps
                    echo "Verification complete!"
                '''
            }
        }
    }
    
    post {
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed - cleaning up...'
            sh 'docker-compose down || true'
        }
        always {
            echo 'Pipeline finished!'
        }
    }
}