# FireFusion 🔥
### AI-Driven Bushfire Forecasting Platform
**Deakin University SIT Capstone | InnovAIte | Trimester 1, 2026**
 
---
 
## Overview
 
FireFusion is a capstone research project that combines AI-powered bushfire spread forecasting with misinformation detection to support emergency decision-making in Victoria, Australia. The platform prototypes an integrated dashboard that visualises both physical fire risks and emerging information risks during bushfire events.
 
The primary focus for Sprint 1 is the **bushfire forecasting model** — predicting where fires start and how they spread using historical Victorian fire data, weather drivers, and terrain context.
 
---
 
## Project Goals
 
1. Prototype a simplified bushfire risk forecasting model using publicly available Victorian datasets
2. Develop a basic misinformation detection workflow using sample social media text data
3. Design and implement a unified dashboard displaying physical and information risk indicators
4. Demonstrate a human-in-the-loop review concept for flagged misinformation
5. Provide technical documentation and recommendations for future scaling
 
> **Scope note:** This project focuses on feasibility and prototype development only. Live integration with emergency management systems or statewide deployment is out of scope. The final deliverable is a working proof-of-concept dashboard with clear documentation and a roadmap for future development.
 
---
 
## Team Structure
 
| Stream | Responsibilities |
|---|---|
| AI Modelling | Dataset validation, model architecture, API schema design |
| Data Engineering | ETL pipeline implementation, data storage, pipeline automation |
| Backend | API development, model serving, database integration |
| Frontend | Dashboard UI, GeoJSON map rendering, data visualisation |
 
---

## GitHub Version Control Guidelines

This document outlines the version control strategy used in this project. It defines branch structure, development workflow, pull request process, and access control to ensure consistency across the team.

## 1. Branch Structure

The repository uses the following branches:

1. main - Contains production-ready and approved code only.
2. developer - Integration branch for completed and reviewed features.
3. release - Used for release preparation, final testing, and validation.
4. backup - Maintains a stable backup copy of the project.
5. feature - Task-based branches created for individual development work.
6. bugfix - Branches created to fix defects or issues.

   
## 2. Branch Creation

Each new task must begin with a separate branch created from the developer branch.

Naming conventions
 1. feature-taskId-task-name
 2. bugfix-issueId-issue-name

This approach keeps development work isolated and improves traceability.

## 3. Development Process

Each developer should follow these steps:

1. Pull the latest code from the developer branch
2. Create a new task-based branch
3. Complete the assigned work within that branch
4. Commit changes with clear and meaningful commit messages
5. Push the branch to GitHub

## 4. Pull Request Process

Once the task is complete, a pull request must be created from the feature or bugfix branch into the developer branch.

Each pull request should include:

 1. A clear title with task or issue ID
 2. A short description of the changes
 3. Details of affected files or modules
 4. Confirmation that testing has been completed

At least one integration lead or an approved reviewer must review the pull request before merging.

## 5. Review and Approval

Before approval, reviewers should check:

 1. Code quality and readability
 2. Branch conflicts
 3. Naming consistency
 4. Build and test results
 5. No unintended changes to unrelated files

Only approved pull requests should be merged.

## 6. Merging Rules

 1. Developers must not merge directly into the main branch
 2. All regular development merges go into the developer branch
 3. Only tested and approved code moves from developer to release, then to main
 4. The main and developer branches should have restricted access

## 7. Release Process

 1. Create a release branch from the developer branch when features are ready
 2. Perform testing and final review in the release branch
 3. Fix only release-related issues in this branch
 4. Merge the release branch into main once stable
 5. Update the backup branch after confirming stability
    
## 8. Backup and Safety

The backup branch maintains a recent stable version of the project.

1. It should be updated only after stable and approved releases
2. It provides a fallback option in case of issues in other branches
   
## 9. Access Control
 1. main - Merge access limited to integration leads or authorised members
 2. developer - Controlled merge access
 3. feature / bugfix branches - Developers can manage their own branches

Branch protection rules should be enabled wherever possible to enforce these controls.
 
