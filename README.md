# 🔄 MLOps CI/CD Pipeline with CircleCI

> **A hands-on project to learn CircleCI** by building an end-to-end CI/CD pipeline that containerizes a Flask ML application, pushes it to Google Artifact Registry, and deploys it to Google Kubernetes Engine (GKE).

---

## 📑 Table of Contents

- [Project Overview](#-project-overview)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Understanding the CircleCI Pipeline](#-understanding-the-circleci-pipeline)
  - [Config File Anatomy](#1-config-file-anatomy-circleciconfigyml)
  - [Executors](#2-executors)
  - [Jobs](#3-jobs)
  - [Workflows](#4-workflows)
- [CircleCI Environment Variables](#-circleci-environment-variables)
- [How the Pipeline Works (Step-by-Step)](#-how-the-pipeline-works-step-by-step)
- [Dockerfile Breakdown (uv-based)](#-dockerfile-breakdown-uv-based)
- [Kubernetes Deployment](#-kubernetes-deployment)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Setup](#local-setup)
  - [Setting Up CircleCI](#setting-up-circleci)
- [Key CircleCI Concepts Learned](#-key-circleci-concepts-learned)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Project Overview

This project demonstrates how to use **CircleCI** as a CI/CD tool to automate the deployment lifecycle of a machine learning application. The ML app itself is a simple **Iris Flower Classifier** built with Flask and scikit-learn — the real focus is on the **automation pipeline**.

**What happens on every `git push`:**

```
Code Push → CircleCI Triggered → Docker Image Built → Pushed to Artifact Registry → Deployed to GKE
```

---

## 🏗 Architecture

```
┌─────────────┐      ┌──────────────────┐      ┌──────────────────────────┐      ┌──────────────┐
│  Developer   │──▶  │    CircleCI       │──▶  │  Google Artifact Registry │──▶  │   GKE        │
│  git push    │      │  Pipeline         │      │  Docker Image             │      │  Kubernetes  │
└─────────────┘      │                    │      └──────────────────────────┘      │  Cluster     │
                      │  1. Checkout       │                                        │              │
                      │  2. Build & Push   │                                        │  2 Replicas  │
                      │  3. Deploy to GKE  │                                        │  Port 5000   │
                      └──────────────────┘                                        └──────────────┘
```

---

## 🛠 Tech Stack

| Component | Technology |
|-----------|-----------|
| **CI/CD** | CircleCI |
| **Language** | Python 3.13 |
| **Web Framework** | Flask |
| **ML Library** | scikit-learn |
| **Package Manager** | uv |
| **Containerization** | Docker (multi-stage build) |
| **Container Registry** | Google Artifact Registry |
| **Orchestration** | Kubernetes (GKE) |
| **Cloud Provider** | Google Cloud Platform |

---

## 📁 Project Structure

```
MLOps-Minor-Project-1-Using-Circle-CI/
├── .circleci/
│   └── config.yml               # ⭐ CircleCI pipeline configuration
├── src/
│   ├── data_processing.py       # Data ingestion & feature engineering
│   ├── model_training.py        # Model training with scikit-learn
│   ├── custom_exception.py      # Custom exception handling
│   └── logger.py                # Logging utility
├── pipeline/
│   └── training_pipeline.py     # Orchestrates the ML pipeline
├── artifacts/
│   └── models/model.pkl         # Trained model artifact
├── templates/
│   └── index.html               # Flask frontend for predictions
├── static/                      # Static assets (CSS)
├── main.py                      # Flask application entry point
├── Dockerfile                   # Multi-stage Docker build with uv
├── kubernetes-deployment.yaml   # K8s Deployment + Service manifest
├── pyproject.toml               # Python project config & dependencies
├── uv.lock                      # Locked dependency versions
└── README.md                    # This file
```

---

## 🔍 Understanding the CircleCI Pipeline

### 1. Config File Anatomy (`.circleci/config.yml`)

CircleCI is configured entirely through a **YAML file** located at `.circleci/config.yml`. This is the heart of your CI/CD pipeline. Here's a breakdown of every section:

```yaml
version: 2.1   # CircleCI configuration version
```

> **Learning Note:** Version `2.1` is the latest and supports features like **executors**, **orbs**, and **reusable commands**. Always use `2.1` for new projects.

---

### 2. Executors

An **executor** defines the environment where your jobs run. Think of it as the "machine" that executes your pipeline steps.

```yaml
executors:
  docker-executor:
    docker:
      - image: google/cloud-sdk:latest    # Base image with gcloud CLI pre-installed
    resource_class: large                  # More CPU/RAM for faster builds
    working_directory: ~/repo              # Where your code gets checked out
```

**Key Concepts:**
| Concept | Description |
|---------|------------|
| `docker` executor | Runs jobs inside a Docker container — lightweight and fast |
| `machine` executor | Runs on a full VM — needed for Docker-in-Docker (not used here) |
| `resource_class` | Controls the compute power: `small`, `medium`, `medium+`, `large`, `xlarge` |
| `working_directory` | The directory where CircleCI checks out your repository |

> **Why `google/cloud-sdk:latest`?** This image comes with `gcloud`, `gsutil`, and `kubectl` pre-installed, so we don't need to install them ourselves.

---

### 3. Jobs

Jobs are the **building blocks** of a CircleCI pipeline. Each job runs in its own isolated environment and performs a specific task.

#### Job 1: `checkout_code`

```yaml
checkout_code:
  executor: docker-executor
  steps:
    - checkout        # Built-in step: clones your repo into working_directory
```

This is the simplest job — it just pulls your code from GitHub. The `checkout` step is a **built-in CircleCI step** that automatically clones the repository at the triggered commit.

---

#### Job 2: `build_docker_image`

```yaml
build_docker_image:
  executor: docker-executor
  steps:
    - checkout
    - setup_remote_docker                              # ⭐ Enables Docker commands
    - run:
        name: Authenticate with Google Cloud
        command: |
          echo "$GCLOUD_SERVICE_KEY" | base64 --decode > gcp-key.json
          gcloud auth activate-service-account --key-file=gcp-key.json
          gcloud auth configure-docker us-central1-docker.pkg.dev
    - run:
        name: Build and Push Image
        command: |
          docker build -t us-central1-docker.pkg.dev/$GOOGLE_PROJECT_ID/circleci-mlops/circleci-mlops:latest .
          docker push us-central1-docker.pkg.dev/$GOOGLE_PROJECT_ID/circleci-mlops/circleci-mlops:latest
```

**Key Concepts:**

| Step | What It Does |
|------|-------------|
| `setup_remote_docker` | Creates a remote Docker engine so you can run `docker build` and `docker push` inside a Docker executor. Without this, Docker commands would fail. |
| `$GCLOUD_SERVICE_KEY` | A **base64-encoded** GCP service account key stored as a CircleCI environment variable |
| `gcloud auth configure-docker` | Configures Docker to use GCP credentials when pushing to Artifact Registry |
| `docker build -t <tag> .` | Builds the Docker image using the project's `Dockerfile` |
| `docker push` | Pushes the built image to Google Artifact Registry |

> **Learning Note:** `setup_remote_docker` is essential when using a `docker` executor and you need to build images. It spins up a separate, privileged Docker daemon.

---

#### Job 3: `deploy_to_gke`

```yaml
deploy_to_gke:
  executor: docker-executor
  steps:
    - checkout
    - setup_remote_docker
    - run:
        name: Authenticate with Google Cloud
        command: |
          echo "$GCLOUD_SERVICE_KEY" | base64 --decode > gcp-key.json
          gcloud auth activate-service-account --key-file=gcp-key.json
    - run:
        name: Configure GKE
        command: |
          gcloud container clusters get-credentials $GKE_CLUSTER \
            --region $GOOGLE_COMPUTE_REGION --project $GOOGLE_PROJECT_ID
    - run:
        name: Deploy to GKE
        command: |
          kubectl apply -f kubernetes-deployment.yaml
```

**Key Concepts:**

| Step | What It Does |
|------|-------------|
| `gcloud container clusters get-credentials` | Fetches the kubeconfig for your GKE cluster, allowing `kubectl` commands to work |
| `kubectl apply -f` | Applies the Kubernetes manifest — creates or updates the Deployment and Service |

---

### 4. Workflows

Workflows define the **order** and **dependencies** between jobs. This is where you orchestrate your pipeline.

```yaml
workflows:
  version: 2
  deploy_pipeline:
    jobs:
      - checkout_code
      - build_docker_image:
          requires:
            - checkout_code          # ⬅️ Only runs after checkout succeeds
      - deploy_to_gke:
          requires:
            - build_docker_image     # ⬅️ Only runs after build succeeds
```

This creates a **sequential pipeline**:

```
checkout_code ──▶ build_docker_image ──▶ deploy_to_gke
```

**Workflow Features You Can Explore:**

| Feature | Description |
|---------|------------|
| `requires` | Defines job dependencies (sequential execution) |
| `filters` | Run jobs only on specific branches or tags |
| `approval` | Add manual approval gates before deploying to production |
| `parallelism` | Run jobs in parallel when they have no dependencies |
| `scheduled triggers` | Run workflows on a cron schedule (e.g., nightly builds) |

---

## 🔐 CircleCI Environment Variables

These are configured in **CircleCI Project Settings → Environment Variables** (never hardcode secrets!):

| Variable | Description | Example |
|----------|------------|---------|
| `GCLOUD_SERVICE_KEY` | Base64-encoded GCP service account JSON key | `base64 gcp-key.json` |
| `GOOGLE_PROJECT_ID` | Your GCP project ID | `golden-index-465218-f7` |
| `GOOGLE_COMPUTE_REGION` | GCP region for your GKE cluster | `us-central1` |
| `GKE_CLUSTER` | Name of your GKE cluster | `mlops-cluster` |

> **How to Base64 encode your key:**
> ```bash
> base64 -w 0 gcp-key.json   # Linux
> base64 -i gcp-key.json     # macOS
> ```

---

## 🚀 How the Pipeline Works (Step-by-Step)

```
 ① Developer pushes code to GitHub
               │
               ▼
 ② CircleCI detects the push via webhook
               │
               ▼
 ③ checkout_code: Clones the repository
               │
               ▼
 ④ build_docker_image:
    ├─ Authenticates with GCP using service account
    ├─ Builds Docker image (multi-stage with uv)
    └─ Pushes image to Google Artifact Registry
               │
               ▼
 ⑤ deploy_to_gke:
    ├─ Authenticates with GCP
    ├─ Connects to GKE cluster via kubeconfig
    └─ Runs `kubectl apply` to deploy the new image
               │
               ▼
 ⑥ Kubernetes pulls the latest image and rolls out
    ├─ 2 pod replicas are created/updated
    └─ LoadBalancer Service exposes port 80 → 5000
               │
               ▼
 ⑦ Application is live! 🎉
```

---

## 🐳 Dockerfile Breakdown (uv-based)

The project uses a **multi-stage Docker build** with **uv** (a fast Python package manager by Astral):

```dockerfile
# --- Build Stage ---
FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/   # Install uv from official image

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1     # Pre-compile for faster cold starts
ENV UV_LINK_MODE=copy         # Better Docker layer caching

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev    # ① Install deps only (cached layer)

COPY . .
RUN uv sync --frozen --no-dev                         # ② Install the project itself

# --- Runtime Stage ---
FROM python:3.13-slim                                 # Clean, minimal image
WORKDIR /app
COPY --from=builder /app /app                         # Copy only what's needed
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 5000
CMD ["uv", "run", "main.py"]
```

**Why multi-stage?** The builder stage contains build tools and caches; the runtime stage only contains the final app — resulting in a **much smaller image**.

---

## ☸️ Kubernetes Deployment

The `kubernetes-deployment.yaml` defines two resources:

### Deployment (2 replicas)
- Runs 2 identical pods of the Flask app for **high availability**
- Pulls the latest image from Google Artifact Registry
- Exposes port `5000` inside the container

### Service (LoadBalancer)
- Type `LoadBalancer` provision an external IP on GKE
- Routes external traffic on port `80` to container port `5000`
- Automatically load-balances between the 2 pods

---

## 🏁 Getting Started

### Prerequisites

- [Python 3.13+](https://www.python.org/)
- [uv](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- [Docker](https://docs.docker.com/get-docker/)
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
- A GCP project with Artifact Registry and GKE enabled
- A [CircleCI](https://circleci.com/) account connected to your GitHub repository

### Local Setup

```bash
# Clone the repository
git clone https://github.com/<your-username>/MLOps-Minor-Project-1-Using-Circle-CI.git
cd MLOps-Minor-Project-1-Using-Circle-CI

# Install dependencies with uv
uv sync

# Run the Flask app
uv run main.py

# Visit http://localhost:5000
```

### Setting Up CircleCI

1. **Connect Repository:** Go to [CircleCI Dashboard](https://app.circleci.com/) → **Projects** → **Set Up Project** → Select your GitHub repo.

2. **Add Environment Variables:** Navigate to **Project Settings** → **Environment Variables** and add:
   - `GCLOUD_SERVICE_KEY`
   - `GOOGLE_PROJECT_ID`
   - `GOOGLE_COMPUTE_REGION`
   - `GKE_CLUSTER`

3. **Trigger a Build:** Push any commit to trigger the pipeline:
   ```bash
   git add .
   git commit -m "trigger circleci pipeline"
   git push origin main
   ```

4. **Monitor:** Watch the pipeline progress in the CircleCI dashboard — each job will show real-time logs.

---

## 📚 Key CircleCI Concepts Learned

| Concept | What It Means | Where Used |
|---------|--------------|------------|
| **Config as Code** | Entire CI/CD pipeline defined in `.circleci/config.yml` | Root of the pipeline |
| **Executors** | Reusable execution environment definitions | `docker-executor` with `google/cloud-sdk` |
| **Jobs** | Isolated units of work with their own steps | `checkout_code`, `build_docker_image`, `deploy_to_gke` |
| **Steps** | Individual commands within a job | `checkout`, `setup_remote_docker`, `run` |
| **Workflows** | Orchestration layer defining job order and dependencies | `deploy_pipeline` workflow |
| **`requires`** | Creates a dependency chain between jobs | Build requires checkout, deploy requires build |
| **`setup_remote_docker`** | Enables Docker-in-Docker for building images | Used in build and deploy jobs |
| **Environment Variables** | Securely store secrets and config | GCP credentials, project ID, cluster name |
| **Resource Classes** | Control compute power for jobs | `large` for faster builds |
| **Webhooks** | Automatic pipeline trigger on git push | GitHub → CircleCI integration |

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|---------|
| `docker: command not found` | Make sure `setup_remote_docker` is included in the job steps |
| `Permission denied` on Artifact Registry | Verify `GCLOUD_SERVICE_KEY` has Artifact Registry Writer role |
| `kubectl: connection refused` | Check that `GKE_CLUSTER` and `GOOGLE_COMPUTE_REGION` match your actual cluster |
| Pipeline not triggering | Ensure CircleCI is connected to your GitHub repo and `.circleci/config.yml` exists on the branch |
| `uv sync` fails in Docker | Ensure both `pyproject.toml` and `uv.lock` are committed to the repo |

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.