pipeline {
    agent any
    environment {
        OS_TEST_PATH = "$WORKSPACE/tests/functional"
        OS_LOG_PATH = "$WORKSPACE/.logs"
    }
    triggers { 
        pollSCM('H */6 * * 1-5')
    }
    stages {
        stage('Build') {
            steps {
                sh '''
                if [[ ! -d "../venv" ]]; then
                virtualenv ../venv
                curl https://bootstrap.pypa.io/get-pip.py | python - 'pip==9.0.3'
                pip install -U setuptools distutils wheel
                fi

                . ../venv/bin/activate
                pip install -U certifi
                pip install --find-links=~/wheels -r tests/test-requirements.txt
                pip install --find-links=~/wheels -r requirements/requirements.txt
                pip install pbr==0.11.0
                pip install certifi==2015.4.28
                python setup.py install
                '''
            }
        }
        stage('Run Tests') {
            parallel {
                stage('PyLint') {
                    steps {
                        echo 'uncomment the following to enable pylint:'
                        sh '''
                        #. venv/bin/activate
                        # pycodestyle --max-line-length=119 --statistics --first
                        '''
                    }
                }
                stage('Unit-Tests') {
                    steps {
                        sh '''
                        . ../venv/bin/activate
                        nosetests --with-coverage --cover-package=poppy --with-xunit --xunit-file=unit-tests.xml tests/unit
                        '''
                    }
                    post {
                        always {
                            junit 'unit-tests.xml'
                        }
                    }
                }
                stage('Functional-Tests') {
                    steps {
                        sh '''
                        . ../venv/bin/activate
                        nosetests --with-coverage --cover-package=poppy --with-xunit --xunit-file=functional-tests.xml tests/functional
                        '''
                    }
                    post {
                        always {
                            junit 'functional-tests.xml'
                        }
                    }
                    
                }
            }
        }
        stage('Build-Python-Packages') {
            steps {
                sh '''
                . ../venv/bin/activate
                rm -rf dist
                pip install -U setuptools distutils wheel
                PBR_VERSION=2017.11.${BUILD_NUMBER} python setup.py bdist_wheel upload -v -r prev
                '''
            }
        }
        stage('Deploy-To-Preview') {
            steps {
                sh 'ssh jenkins@salt-test.altcdn.com  "bash preview-deploy.sh"'
            }
        }
    }

    post {
        success {
            echo "post success msg to slack: Build success -> ${env.JOB_NAME}"
        }
        failure {
            echo  "post fail msg to slack: Deployment failed for branch ${env.JOB_NAME} to environment ${DEPLOY_ENV} build ${env.BUILD_NUMBER}"
        }
    }
}
