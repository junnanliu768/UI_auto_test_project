pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install Python') {
            steps {
                sh '''
                python3 --version
                pip3 --version
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                pip3 install -r requirements.txt
                '''
            }
        }

        stage('Install Playwright Browser') {
            steps {
                sh '''
                playwright install
                '''
            }
        }

        stage('Run Test') {
            steps {
                sh '''
                python3 run_tests.py
                '''
            }
        }
    }
}
