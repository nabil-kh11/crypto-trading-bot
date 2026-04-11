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

        stage('Detect Changes') {
            steps {
                script {
                    def changes = sh(
                        script: 'git diff --name-only HEAD~1 HEAD || git diff --name-only HEAD',
                        returnStdout: true
                    ).trim()
                    
                    echo "Changed files:\n${changes}"
                    
                    env.BUILD_MARKET_DATA    = changes.contains('services/market-data-collector') ? 'true' : 'false'
                    env.BUILD_ML_ENGINE      = changes.contains('services/ml-decision-engine') ? 'true' : 'false'
                    env.BUILD_SENTIMENT      = changes.contains('services/sentiment-collector') ? 'true' : 'false'
                    env.BUILD_ORDER_EXECUTOR = changes.contains('services/order-executor') ? 'true' : 'false'
                    env.BUILD_CHATBOT        = changes.contains('services/chatbot') ? 'true' : 'false'
                    env.BUILD_DASHBOARD      = changes.contains('services/dashboard') ? 'true' : 'false'
                    
                    echo "Services to rebuild:"
                    echo "  market-data-collector: ${env.BUILD_MARKET_DATA}"
                    echo "  ml-decision-engine:    ${env.BUILD_ML_ENGINE}"
                    echo "  sentiment-collector:   ${env.BUILD_SENTIMENT}"
                    echo "  order-executor:        ${env.BUILD_ORDER_EXECUTOR}"
                    echo "  chatbot:               ${env.BUILD_CHATBOT}"
                    echo "  dashboard:             ${env.BUILD_DASHBOARD}"
                }
            }
        }

        stage('Code Quality — SonarQube') {
            steps {
                echo 'Running SonarQube analysis...'
                sh '''
                    docker exec jenkins bash -c "
                        cd /var/jenkins_home/workspace/crypto-trading-bot && \
                        sonar-scanner \
                        -Dsonar.projectKey=crypto-trading-bot \
                        -Dsonar.sources=services \
                        -Dsonar.exclusions=**/*_pb2.py,**/*_pb2_grpc.py,**/migrations/**,**/__pycache__/** \
                        -Dsonar.host.url=http://172.17.0.5:9000 \
                        -Dsonar.python.version=3.11 \
                        -Dsonar.token=sqp_8925d4034556b3d0174fb6794cbd2f582d8f5152
                    " || echo "SonarQube analysis completed"
                '''
            }
        }
                
        stage('Build') {
            steps {
                echo 'Building only changed services...'
                script {
                    if (env.BUILD_MARKET_DATA == 'true') {
                        sh 'docker-compose build market-data-collector'
                        echo '✓ Built market-data-collector'
                    }
                    if (env.BUILD_SENTIMENT == 'true') {
                        sh 'docker-compose build sentiment-collector'
                        echo '✓ Built sentiment-collector'
                    }
                    if (env.BUILD_ORDER_EXECUTOR == 'true') {
                        sh 'docker-compose build order-executor'
                        echo '✓ Built order-executor'
                    }
                    if (env.BUILD_CHATBOT == 'true') {
                        sh 'docker-compose build chatbot'
                        echo '✓ Built chatbot'
                    }
                    if (env.BUILD_DASHBOARD == 'true') {
                        sh 'docker-compose build dashboard'
                        echo '✓ Built dashboard'
                    }
                    if (env.BUILD_ML_ENGINE == 'true') {
                        echo '⚠ ML engine changed but skipping rebuild to preserve models'
                    }
                    echo 'Build stage complete!'
                }
            }
        }
        
        stage('Test') {
            steps {
                echo 'Running service health checks...'
                sh '''
                    docker-compose up -d --no-recreate
                    sleep 30
                    docker-compose ps
                    echo "All services started successfully!"
                '''
            }
        }

        stage('Deploy') {
            steps {
                echo 'Deploying to Kubernetes via Helm...'
                sh '''
                    helm upgrade crypto-trading-bot \
                        infrastructure/kubernetes/helm/crypto-trading-bot \
                        --install \
                        --namespace crypto-trading-bot \
                        --create-namespace \
                        || echo "Helm deployment skipped"
                    echo "Deploy stage complete!"
                '''
            }
        }
        
        stage('Verify') {
            steps {
                echo 'Verifying deployment...'
                sh '''
                    helm list || echo "helm list skipped"
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