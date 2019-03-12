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
                if [ ! -d ~/poppy_venv ]; then
                virtualenv ~/poppy_venv
                fi
                . ~/poppy_venv/bin/activate
                if [ $(pip -V | awk '{print $2}') != "9.0.3" ]; then
                curl -s https://bootstrap.pypa.io/get-pip.py | python - 'pip==9.0.3'
                fi
                pip install --find-links=~/wheels -U wheel
                pip install --find-links=~/wheels setuptools==35.0.2
                pip install --find-links=~/wheels pbr==0.11.0 certifi==2018.11.29
                pip install --find-links=~/wheels -r tests/test-requirements.txt
                pip install --find-links=~/wheels -r requirements/requirements.txt
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
                        echo "Pylint tests are temporarily disabled"
                        #. ~/poppy_venv/bin/activate
                        # pycodestyle --max-line-length=119 --statistics --first
                        '''
                    }
                }
                stage('Unit-Tests') {
                    steps {
                        sh '''
                        echo "Unit tests are temporarily disabled"
                        #. ~/poppy_venv/bin/activate
                        #nosetests --with-coverage --cover-package=poppy --with-xunit --xunit-file=unit-tests.xml tests/unit
                        '''
                    }
                    post {
                        always {
                            #junit 'unit-tests.xml'
                        }
                    }
                }
                stage('Functional-Tests') {
                    steps {
                        sh '''
                        echo "Functional tests are temporarily disabled"
                        #. ~/poppy_venv/bin/activate
                        #nosetests --with-coverage --cover-package=poppy --with-xunit --xunit-file=functional-tests.xml tests/functional
                        '''
                    }
                    post {
                        always {
                            #junit 'functional-tests.xml'
                        }
                    }

                }
            }
        }
        stage('Build-Python-Packages') {
            steps {
                sh '''
                . ~/poppy_venv/bin/activate
                rm -rf dist
                PBR_VERSION=2017.11.${BUILD_NUMBER} python setup.py bdist_wheel upload -v -r prev
                '''
            }
        }
        stage('Deploy-To-Preview') {
            parallel {
                stage('Deploy-To-Poppy-Workers') {
                    when {
                    branch 'pre-release'
                     }
                    steps {
                        sh '''
                        echo "deploy to pwkrs here"
                        ssh jenkins@salt-test.altcdn.com  "bash preview-deploy-pwkr.sh"
                        '''
                    }
                }
                stage('Deploy-To-Poppy-Servers') {
                    when {
                    branch 'pre-release'
                     }
                    steps {
                        sh '''
                        echo "deploy to cdn servers here"
                        ssh jenkins@salt-test.altcdn.com  "bash preview-deploy-cdn.sh"
                        '''
                    }
                }
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
