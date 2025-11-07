# 🚀 GitHub Push Commands - Quick Reference

## ✅ **Step 1: Check Current Status**

```bash
cd C:\Users\vaddi\Downloads\chatbot_crsr
git status
```

---

## ✅ **Step 2: Initialize Git (If Not Done)**

```bash
git init
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

---

## ✅ **Step 3: Add Only Important Files (Selective)**

**Add source code:**
```bash
git add src/app.py
git add src/requirements.txt
git add src_proxy/app.py
git add src_proxy/requirements.txt
```

**Add configuration:**
```bash
git add template.yaml
git add .gitignore
```

**Add website:**
```bash
git add index.html
```

**Add documentation (only what you want):**
```bash
git add README.md
# git add FINAL_PROJECT_REPORT.md  # Uncomment if you want it
```

**OR add everything except .md files:**
```bash
git add src/
git add src_proxy/
git add index.html
git add template.yaml
git add .gitignore
git add README.md
```

---

## ✅ **Step 4: Check What Will Be Committed**

```bash
git status
```

**Verify:** Only files you want should be listed!

---

## ✅ **Step 5: Create Commit**

```bash
git commit -m "Initial commit: AWS Chatbot with PDF Knowledge Base"
```

---

## ✅ **Step 6: Create GitHub Repository**

1. Go to: https://github.com/new
2. Repository name: `aws-chatbot-pdf-kb`
3. Description: "Intelligent AWS Cloud Chatbot with PDF Knowledge Base"
4. **Don't** check "Initialize with README"
5. Click **"Create repository"**

---

## ✅ **Step 7: Connect and Push**

```bash
# Add remote (REPLACE YOUR_USERNAME and REPO_NAME)
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# Rename branch
git branch -M main

# Push to GitHub
git push -u origin main
```

---

## 🗑️ **How to Delete Files from GitHub Later (If Needed):**

### **Option 1: Delete Files from Local + GitHub**

```bash
# Delete file locally
git rm FILE_ORGANIZATION_GUIDE.md
git rm GITHUB_PUSH_GUIDE.md
git rm TEMPLATE_YAML_EXPLANATION.md

# Commit the deletion
git commit -m "Remove unnecessary documentation files"

# Push to GitHub
git push
```

### **Option 2: Delete Files from GitHub Only (Keep Locally)**

```bash
# Remove from Git tracking but keep local file
git rm --cached FILE_ORGANIZATION_GUIDE.md
git rm --cached GITHUB_PUSH_GUIDE.md

# Commit
git commit -m "Remove files from repository"

# Push
git push
```

### **Option 3: Delete via GitHub Website**

1. Go to your repository on GitHub
2. Click on the file you want to delete
3. Click **"Delete"** button (trash icon)
4. Commit the deletion

---

## 📋 **Recommended Files to Push:**

✅ **Push these:**
- `src/app.py` - Your Lambda code
- `src/requirements.txt` - Dependencies
- `src_proxy/app.py` - API proxy code
- `src_proxy/requirements.txt` - Dependencies
- `index.html` - Website
- `template.yaml` - Infrastructure code
- `.gitignore` - Git ignore rules
- `README.md` - Project documentation

❌ **Don't push these:**
- `*.md` files (except README.md) - Personal docs
- `boto3/`, `PyPDF2/` folders - Auto-installed
- `*.zip` files - Deployment packages
- `__pycache__/` - Python cache
- `PROJECT_REPORT.md` - Personal report
- `FINAL_PROJECT_REPORT.md` - Personal report (unless you want it)

---

## 🎯 **Quick Push (Recommended Approach):**

```bash
# 1. Initialize
git init
git config user.name "Your Name"
git config user.email "your.email@example.com"

# 2. Add only important files
git add src/ src_proxy/ index.html template.yaml .gitignore README.md

# 3. Commit
git commit -m "Initial commit: AWS Chatbot with PDF Knowledge Base"

# 4. Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
git branch -M main
git push -u origin main
```

---

## 💡 **Pro Tip:**

**The `.gitignore` file I updated will automatically exclude:**
- All those .md files you don't want
- Dependency folders (boto3, PyPDF2)
- Zip files
- Cache files

**So you can safely use:**
```bash
git add .
```

**And it will only add files NOT in `.gitignore`!** 🎉

---

**Ready to push? Use the commands above!** 🚀

