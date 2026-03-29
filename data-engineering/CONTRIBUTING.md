# Contribution Guidelines: Data Engineering Stream

To ensure our data pipelines remain stable and our final database aligns perfectly with our architecture, please follow these stream-specific contribution rules.

## Branch Protection and Merging Rules

The main branch is our source of truth. It holds the production-ready extraction scripts and official documentation.

* Direct pushes to `main` are strictly forbidden.
* All code, documentation, and architecture changes must be submitted via Pull Requests (PRs).
* **Strict Merging Rule:** A PR cannot be merged into `main` until it has a total of 3 approved reviews. At least one of these approvals must come from a Senior or Lead team member.

## Code Review Requirements

Reviewers are responsible for protecting the integrity of our data pipelines. Before approving a PR, reviewers must check for:

* **Architecture Alignment:** Does the output of the script match the column names and data types defined in `architecture/database_architecture.md` (our Star Schema)?
* **Data Validation:** Does the code handle missing values, API timeouts, or incorrect data types safely?
* **Security:** Are there any hardcoded API keys or passwords? (These must be rejected immediately).
* **Storage Limits:** Are there any `.csv`, `.json`, or `.zip` files included in the commit? (These must be rejected immediately).

## How to Contribute (Forking Workflow)

We use a Fork and Pull Request workflow. Follow these exact steps whenever you want to contribute Python scripts, pipeline updates, or documentation.

### Step 1: Fork the Repository

You will not work directly on the main InnovAIte repository. Instead, you will create a personal copy (a fork) on your own GitHub account.

1. Go to the main project repository: https://github.com/InnovAIte-Deakin/InnovAIte_FireFusion_Project
2. Click the **Fork** button in the top right corner.
3. Keep the default settings and click **Create fork**.

> **Guide:** <img width="628" height="318" alt="fork" src="https://github.com/user-attachments/assets/b74bd711-f87a-4de0-8980-45bc98d43eb2" />

### Step 2: Clone Your Fork Locally

Now, download your personal copy to your local computer so you can write code.

1. Open your terminal or command prompt.
2. Run the following command, replacing `<your-username>` with your actual GitHub username:

```bash
git clone https://github.com/<your-username>/InnovAIte_FireFusion_Project.git
cd InnovAIte_FireFusion_Project/data-engineering
```

> **Guide:** <img width="586" height="228" alt="clone" src="https://github.com/user-attachments/assets/e2a223c4-0a5c-4699-82cf-b869e102a43b" />


### Step 3: Add the Upstream Remote (The Original Repo)

To keep your local copy updated with the rest of the team's work, you need to link it back to the original InnovAIte repository.

Run this command in your terminal:

```bash
git remote add upstream https://github.com/InnovAIte-Deakin/InnovAIte_FireFusion_Project.git
```

> **Guide:** <img width="583" height="80" alt="Screenshot 2026-03-25 at 2 40 42 pm" src="https://github.com/user-attachments/assets/8b029b28-1c3f-4336-b05f-fc1d8927e2eb" />


### Step 4: Create a Feature Branch

Always create a new branch for your specific task before writing any code. Never work on your main branch.

Branch names should follow this format: `feature/<short-description>` or `fix/<short-description>`.

```bash
git checkout -b feature/open mateo
```

### Step 5: Make Your Changes Locally

Write your extraction scripts or update documentation. Ensure you test your Python code locally to verify it outputs the correct data format and does not throw errors.

### Step 6: Stage and Commit Your Changes

Save your work with a clear, descriptive commit message explaining exactly what you changed.

```bash
git add .  
git commit -m "feat: add Open-Meteo historical extraction script"
```

### Step 7: Push Your Branch to Your Fork

Upload your new code to your personal GitHub fork.

```bash
git push origin feature/open-meteo-pipeline
```

### Step 8: Open a Pull Request (PR)

Finally, submit your work to the main InnovAIte repository for review.

1. Go to the main project repository on GitHub: https://github.com/InnovAIte-Deakin/InnovAIte_FireFusion_Project
2. You should see a green button that says **Compare & pull request**. Click it.
3. Set the base repository to `InnovAIte-Deakin/InnovAIte_FireFusion_Project` (branch: `main`).
4. Set the head repository to your fork (branch: your feature branch).
5. Add a clear title and description of your changes.
6. Click **Create pull request** and add your reviewers (remember, you need 3 total approvals, including 1 lead).

## Data Engineering Best Practices

* **Protect Passwords and Keys:** Never commit sensitive data. API keys must be stored locally in a `.env` file. We use `python-dotenv` to load these into our scripts.
* **Keep Data Local:** Always use the `.gitignore` file to block raw datasets (`.csv`, `.zip`) from being uploaded. GitHub is for pipeline code, not data storage.
