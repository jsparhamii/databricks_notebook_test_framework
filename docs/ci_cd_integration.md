# CI/CD Integration Guide

This guide shows how to integrate the Databricks Notebook Test Framework into your CI/CD pipelines.

## GitHub Actions

### Basic Setup

Create `.github/workflows/test.yml`:

```yaml
name: Test Databricks Notebooks

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -e .
        pip install nutter
    
    - name: Run tests
      env:
        DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
        DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
      run: |
        dbx_test run --remote --tests-dir tests
    
    - name: Publish results
      uses: EnricoMi/publish-unit-test-result-action@v2
      if: always()
      with:
        files: .dbx_test-results/**/report.xml
```

### Advanced Setup with Multiple Environments

```yaml
name: Multi-Environment Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test-local:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install and test locally
      run: |
        pip install -e . nutter
        dbx_test run --local --tests-dir tests
    
    - name: Upload results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: local-test-results
        path: .dbx_test-results/

  test-remote:
    runs-on: ubuntu-latest
    needs: test-local
    strategy:
      matrix:
        environment: [dev, test, prod]
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install
      run: pip install -e .
    
    - name: Run remote tests
      env:
        DATABRICKS_TOKEN: ${{ secrets[format('DATABRICKS_TOKEN_{0}', matrix.environment)] }}
        DATABRICKS_HOST: ${{ secrets[format('DATABRICKS_HOST_{0}', matrix.environment)] }}
      run: |
        dbx_test run --remote \
          --env ${{ matrix.environment }} \
          --config config/test_config_${{ matrix.environment }}.yml
    
    - name: Publish results
      uses: EnricoMi/publish-unit-test-result-action@v2
      if: always()
      with:
        files: .dbx_test-results/**/report.xml
        check_name: Tests (${{ matrix.environment }})
```

## Azure DevOps

### Basic Pipeline

Create `azure-pipelines.yml`:

```yaml
trigger:
  branches:
    include:
    - main
    - develop

pool:
  vmImage: 'ubuntu-latest'

variables:
  pythonVersion: '3.10'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: $(pythonVersion)

- script: |
    pip install -e .
    pip install nutter
  displayName: 'Install dependencies'

- script: |
    dbx_test run --remote --tests-dir tests
  displayName: 'Run tests'
  env:
    DATABRICKS_TOKEN: $(DATABRICKS_TOKEN)
    DATABRICKS_HOST: $(DATABRICKS_HOST)

- task: PublishTestResults@2
  condition: always()
  inputs:
    testResultsFormat: 'JUnit'
    testResultsFiles: '**/report.xml'
    searchFolder: '.dbx_test-results'
```

### Multi-Stage Pipeline

```yaml
stages:
- stage: Test
  jobs:
  - job: LocalTests
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '3.10'
    
    - script: pip install -e . nutter
      displayName: 'Install'
    
    - script: dbx_test run --local --tests-dir tests
      displayName: 'Run local tests'
    
    - task: PublishTestResults@2
      condition: always()
      inputs:
        testResultsFormat: 'JUnit'
        testResultsFiles: '**/report.xml'
        searchFolder: '.dbx_test-results'

- stage: DeployDev
  dependsOn: Test
  condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/develop'))
  jobs:
  - job: TestDev
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '3.10'
    
    - script: pip install -e .
      displayName: 'Install'
    
    - script: |
        dbx_test run --remote --env dev --config config/test_config_dev.yml
      displayName: 'Test in Dev'
      env:
        DATABRICKS_TOKEN: $(DATABRICKS_DEV_TOKEN)

- stage: DeployProd
  dependsOn: DeployDev
  condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
  jobs:
  - job: TestProd
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '3.10'
    
    - script: pip install -e .
      displayName: 'Install'
    
    - script: |
        dbx_test run --remote --env prod --config config/test_config_prod.yml
      displayName: 'Test in Prod'
      env:
        DATABRICKS_TOKEN: $(DATABRICKS_PROD_TOKEN)
```

## GitLab CI

Create `.gitlab-ci.yml`:

```yaml
stages:
  - test
  - deploy

variables:
  PYTHON_VERSION: "3.10"

.test_template:
  image: python:${PYTHON_VERSION}
  before_script:
    - pip install -e .
    - pip install nutter
  artifacts:
    when: always
    reports:
      junit: .dbx_test-results/**/report.xml
    paths:
      - .dbx_test-results/

test:local:
  extends: .test_template
  stage: test
  script:
    - dbx_test run --local --tests-dir tests

test:remote:dev:
  extends: .test_template
  stage: test
  script:
    - dbx_test run --remote --env dev --config config/test_config_dev.yml
  only:
    - develop
    - merge_requests

test:remote:prod:
  extends: .test_template
  stage: deploy
  script:
    - dbx_test run --remote --env prod --config config/test_config_prod.yml
  only:
    - main
```

## Jenkins

Create `Jenkinsfile`:

```groovy
pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.10'
    }
    
    stages {
        stage('Setup') {
            steps {
                sh '''
                    python${PYTHON_VERSION} -m venv venv
                    . venv/bin/activate
                    pip install -e .
                    pip install nutter
                '''
            }
        }
        
        stage('Test Locally') {
            steps {
                sh '''
                    . venv/bin/activate
                    dbx_test run --local --tests-dir tests
                '''
            }
        }
        
        stage('Test Remote') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([
                    string(credentialsId: 'databricks-token', variable: 'DATABRICKS_TOKEN'),
                    string(credentialsId: 'databricks-host', variable: 'DATABRICKS_HOST')
                ]) {
                    sh '''
                        . venv/bin/activate
                        dbx_test run --remote --tests-dir tests
                    '''
                }
            }
        }
    }
    
    post {
        always {
            junit '.dbx_test-results/**/report.xml'
            archiveArtifacts artifacts: '.dbx_test-results/**/*', allowEmptyArchive: true
        }
    }
}
```

## CircleCI

Create `.circleci/config.yml`:

```yaml
version: 2.1

executors:
  python-executor:
    docker:
      - image: cimg/python:3.10
    working_directory: ~/project

jobs:
  test-local:
    executor: python-executor
    steps:
      - checkout
      - restore_cache:
          keys:
            - v1-dependencies-{{ checksum "pyproject.toml" }}
      - run:
          name: Install dependencies
          command: |
            pip install -e .
            pip install nutter
      - save_cache:
          paths:
            - ~/.cache/pip
          key: v1-dependencies-{{ checksum "pyproject.toml" }}
      - run:
          name: Run local tests
          command: dbx_test run --local --tests-dir tests
      - store_test_results:
          path: .dbx_test-results
      - store_artifacts:
          path: .dbx_test-results

  test-remote:
    executor: python-executor
    steps:
      - checkout
      - run:
          name: Install dependencies
          command: pip install -e .
      - run:
          name: Run remote tests
          command: |
            dbx_test run --remote --tests-dir tests
          environment:
            DATABRICKS_TOKEN: ${DATABRICKS_TOKEN}
            DATABRICKS_HOST: ${DATABRICKS_HOST}
      - store_test_results:
          path: .dbx_test-results

workflows:
  version: 2
  test:
    jobs:
      - test-local
      - test-remote:
          requires:
            - test-local
          filters:
            branches:
              only:
                - main
                - develop
```

## Best Practices

### 1. Secrets Management

Never commit secrets to version control. Use your CI/CD platform's secrets management:

**GitHub Actions:**
- Repository Settings → Secrets → Actions
- Add `DATABRICKS_TOKEN` and `DATABRICKS_HOST`

**Azure DevOps:**
- Pipeline → Edit → Variables
- Mark as "Secret"

**GitLab:**
- Settings → CI/CD → Variables
- Mark as "Masked" and "Protected"

### 2. Test Stages

Organize tests in logical stages:

1. **Local tests** - Fast, run on every commit
2. **Dev environment** - Test against dev workspace
3. **Test environment** - Integration tests
4. **Prod environment** - Smoke tests only

### 3. Parallel Execution

Enable parallel execution for faster CI/CD:

```yaml
- name: Run tests in parallel
  run: |
    dbx_test run --remote --parallel --max-parallel-jobs 10
```

### 4. Caching

Cache dependencies to speed up builds:

```yaml
- name: Cache pip
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('pyproject.toml') }}
```

### 5. Failure Notifications

Configure notifications for test failures:

**Slack:**
```yaml
- name: Notify Slack
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {
        "text": "Tests failed on ${{ github.repository }}"
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

### 6. Test Reports

Always publish test reports:

```yaml
- name: Publish test report
  uses: EnricoMi/publish-unit-test-result-action@v2
  if: always()
  with:
    files: .dbx_test-results/**/report.xml
```

### 7. Quality Gates

Set quality thresholds:

```yaml
- name: Check test coverage
  run: |
    PASSED=$(cat .dbx_test-results/latest/results.json | jq '.summary.passed')
    TOTAL=$(cat .dbx_test-results/latest/results.json | jq '.summary.total')
    PASS_RATE=$(echo "scale=2; $PASSED / $TOTAL" | bc)
    
    if (( $(echo "$PASS_RATE < 0.95" | bc -l) )); then
      echo "Test pass rate $PASS_RATE below threshold 0.95"
      exit 1
    fi
```

## Troubleshooting CI/CD Issues

### Issue: Tests timeout in CI

**Solution:**
- Increase timeout in config
- Use smaller cluster size
- Enable parallel execution

### Issue: Authentication fails

**Solution:**
- Verify secrets are set correctly
- Check token hasn't expired
- Ensure proper secret naming

### Issue: Inconsistent test results

**Solution:**
- Ensure tests are independent
- Use fixed test data
- Avoid time-dependent assertions

### Issue: Slow pipeline execution

**Solution:**
- Enable caching
- Run tests in parallel
- Use matrix builds for environments

## Example Complete Setup

See the included files:
- `.github/workflows/test.yml` - GitHub Actions example
- `azure-pipelines.yml` - Azure DevOps example

These provide production-ready CI/CD configurations.

