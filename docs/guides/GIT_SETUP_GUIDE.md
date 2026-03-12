# Git Setup and Version Control Guide

## Initial Setup

### 1. Initialize Git Repository

```bash
# Navigate to project directory
cd "c:\Users\peterson\trading bot"

# Initialize git repository
git init

# Configure user information
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### 2. Create .gitignore

```bash
# Create .gitignore file
echo "# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
logs/
*.log

# Database
*.db
*.sqlite
*.sqlite3

# Environment variables
.env
.env.local

# Test coverage
htmlcov/
.coverage
.coverage.*
coverage.xml
*.cover

# Jupyter Notebook
.ipynb_checkpoints

# Trading bot specific
test_reports/
backups/
autonomous_backups/
evolution_backups/
fix_backups/
temp_*.db
profile.stats

# API Keys and Secrets
*_keys.json
*_secrets.yaml
api_keys.txt

# Large data files
*.csv
*.parquet
data/historical/
" > .gitignore
```

### 3. Initial Commit

```bash
# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Trading bot v1.0 with comprehensive features"
```

## Branch Strategy

### Main Branches
- `main` - Production-ready code
- `develop` - Development branch for integration
- `staging` - Pre-production testing

### Feature Branches
```bash
# Create feature branch
git checkout -b feature/new-strategy

# Work on feature...

# Commit changes
git add .
git commit -m "feat: Add momentum strategy with ML enhancement"

# Push to remote
git push origin feature/new-strategy
```

### Hotfix Branches
```bash
# Create hotfix from main
git checkout main
git checkout -b hotfix/critical-bug

# Fix bug...

# Commit and merge
git commit -m "fix: Resolve critical execution bug"
git checkout main
git merge hotfix/critical-bug
git push origin main
```

## Commit Message Convention

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements

### Examples
```bash
git commit -m "feat(strategy): Add MACD crossover strategy"
git commit -m "fix(risk): Correct position sizing calculation"
git commit -m "docs: Update README with installation instructions"
git commit -m "refactor(execution): Simplify order routing logic"
git commit -m "test: Add unit tests for risk manager"
git commit -m "perf(data): Optimize data fetching pipeline"
```

## Remote Repository Setup

### GitHub
```bash
# Add remote repository
git remote add origin https://github.com/yourusername/trading-bot.git

# Push to remote
git push -u origin main

# Push all branches
git push --all origin
```

### GitLab
```bash
# Add remote repository
git remote add origin https://gitlab.com/yourusername/trading-bot.git

# Push to remote
git push -u origin main
```

## Workflow

### Daily Development
```bash
# 1. Pull latest changes
git checkout develop
git pull origin develop

# 2. Create feature branch
git checkout -b feature/my-feature

# 3. Make changes and commit
git add .
git commit -m "feat: Description of changes"

# 4. Push to remote
git push origin feature/my-feature

# 5. Create Pull Request on GitHub/GitLab
```

### Code Review Process
1. Create Pull Request
2. Request review from team members
3. Address review comments
4. Get approval
5. Merge to develop
6. Delete feature branch

### Release Process
```bash
# 1. Merge develop to staging
git checkout staging
git merge develop
git push origin staging

# 2. Test on staging

# 3. Merge staging to main
git checkout main
git merge staging

# 4. Tag release
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# 5. Push main
git push origin main
```

## Git Hooks

### Pre-commit Hook
Create `.git/hooks/pre-commit`:

```bash
#!/bin/sh
# Pre-commit hook for code quality checks

echo "Running pre-commit checks..."

# Run tests
python -m pytest tests/ -q
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi

# Run linter
python -m flake8 trading_bot/
if [ $? -ne 0 ]; then
    echo "Linting failed. Commit aborted."
    exit 1
fi

# Format code
python -m black trading_bot/ --check
if [ $? -ne 0 ]; then
    echo "Code formatting required. Run: python -m black trading_bot/"
    exit 1
fi

echo "Pre-commit checks passed!"
exit 0
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

## Best Practices

### 1. Commit Often
- Make small, focused commits
- Commit working code
- Don't commit broken code

### 2. Write Good Commit Messages
- Use imperative mood ("Add feature" not "Added feature")
- First line: brief summary (50 chars max)
- Blank line
- Detailed description if needed

### 3. Keep Branches Up to Date
```bash
# Update feature branch with latest develop
git checkout feature/my-feature
git fetch origin
git rebase origin/develop
```

### 4. Use .gitignore
- Never commit sensitive data (API keys, passwords)
- Don't commit generated files
- Don't commit large binary files

### 5. Review Before Committing
```bash
# Check what will be committed
git status
git diff

# Stage specific files
git add file1.py file2.py

# Review staged changes
git diff --staged
```

## Useful Commands

### Status and History
```bash
# Check status
git status

# View commit history
git log --oneline --graph --all

# View changes
git diff

# View file history
git log --follow filename.py
```

### Undoing Changes
```bash
# Discard changes in working directory
git checkout -- filename.py

# Unstage file
git reset HEAD filename.py

# Amend last commit
git commit --amend

# Revert commit
git revert commit_hash

# Reset to previous commit (dangerous!)
git reset --hard commit_hash
```

### Branching
```bash
# List branches
git branch -a

# Switch branch
git checkout branch_name

# Create and switch
git checkout -b new_branch

# Delete branch
git branch -d branch_name

# Delete remote branch
git push origin --delete branch_name
```

### Stashing
```bash
# Stash changes
git stash

# List stashes
git stash list

# Apply stash
git stash apply

# Apply and remove stash
git stash pop
```

### Tagging
```bash
# Create tag
git tag -a v1.0.0 -m "Version 1.0.0"

# List tags
git tag

# Push tag
git push origin v1.0.0

# Push all tags
git push origin --tags

# Delete tag
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0
```

## Troubleshooting

### Merge Conflicts
```bash
# When conflict occurs
git status  # See conflicted files

# Edit files to resolve conflicts
# Look for <<<<<<< HEAD markers

# After resolving
git add resolved_file.py
git commit -m "Resolve merge conflict"
```

### Accidentally Committed Sensitive Data
```bash
# Remove file from git but keep locally
git rm --cached sensitive_file.txt
git commit -m "Remove sensitive file"

# Add to .gitignore
echo "sensitive_file.txt" >> .gitignore
git add .gitignore
git commit -m "Update .gitignore"
```

### Large File Issues
```bash
# Use Git LFS for large files
git lfs install
git lfs track "*.csv"
git add .gitattributes
git commit -m "Add Git LFS tracking"
```

## Backup Strategy

### 1. Remote Backup
- Push to GitHub/GitLab regularly
- Use private repository for sensitive code

### 2. Multiple Remotes
```bash
# Add backup remote
git remote add backup https://gitlab.com/yourusername/trading-bot-backup.git

# Push to both remotes
git push origin main
git push backup main
```

### 3. Local Backup
```bash
# Create backup branch
git branch backup-$(date +%Y%m%d)

# Archive repository
git archive --format=zip --output=backup.zip HEAD
```

## Collaboration

### Code Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] No sensitive data committed
- [ ] Performance impact considered
- [ ] Error handling implemented

### Pull Request Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
```

## Resources

- [Git Documentation](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
