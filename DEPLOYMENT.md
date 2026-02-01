# 🚀 Deploying to PythonAnywhere (FREE)

This guide will help you deploy the Course Diary System to PythonAnywhere for free.

## Step 1: Create a PythonAnywhere Account

1. Go to [pythonanywhere.com](https://www.pythonanywhere.com)
2. Click "**Pricing & signup**"
3. Select "**Create a Beginner account**" (FREE)
4. Fill in your details and create account

## Step 2: Upload Your Code

### Option A: Using Git (Recommended)

1. First, create a GitHub repository and push your code
2. On PythonAnywhere, open a **Bash console**
3. Run:
```bash
cd ~
git clone https://github.com/YOUR_USERNAME/course_diary_system.git
```

### Option B: Manual Upload

1. Go to **Files** tab on PythonAnywhere
2. Create folder: `course_diary_system`
3. Upload all project files (you can zip and upload)

## Step 3: Create Virtual Environment

In PythonAnywhere Bash console:

```bash
cd ~/course_diary_system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 4: Configure Web App

1. Go to **Web** tab
2. Click "**Add a new web app**"
3. Choose **Manual configuration** (NOT Flask)
4. Select **Python 3.9** or later

### Configure WSGI file:

1. Click on the WSGI configuration file link
2. Delete all content and paste:

```python
import sys
import os

project_path = '/home/YOUR_USERNAME/course_diary_system'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

src_path = os.path.join(project_path, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from app import app as application
```

3. Replace `YOUR_USERNAME` with your PythonAnywhere username

### Configure Virtual Environment:

1. In the **Virtualenv** section, enter:
   ```
   /home/YOUR_USERNAME/course_diary_system/venv
   ```

### Configure Static Files:

1. In **Static files** section, add:
   - URL: `/static/`
   - Directory: `/home/YOUR_USERNAME/course_diary_system/static`

## Step 5: Update app.py for PythonAnywhere

Edit `src/app.py` and update the paths at the top:

```python
# For PythonAnywhere, use absolute paths
import os
BASE_PATH = '/home/YOUR_USERNAME/course_diary_system'
CONFIG_PATH = os.path.join(BASE_PATH, 'config')
DATA_PATH = os.path.join(BASE_PATH, 'data')
OUTPUT_PATH = os.path.join(BASE_PATH, 'output')
```

## Step 6: Create Required Directories

In Bash console:
```bash
mkdir -p ~/course_diary_system/data
mkdir -p ~/course_diary_system/output
```

## Step 7: Reload Web App

1. Go back to **Web** tab
2. Click the green "**Reload**" button

## Step 8: Access Your App!

Your app will be live at:
```
https://YOUR_USERNAME.pythonanywhere.com
```

---

## 📝 Notes

- **Free tier limitations:**
  - 1 web app only
  - App may sleep after inactivity (auto-wakes on request)
  - Limited CPU time
  - Web app expires after 3 months (just click to renew)

- **To update code:**
  1. Pull latest from Git: `git pull`
  2. Click "Reload" in Web tab

---

## 🔧 Troubleshooting

### If you see errors:

1. Check **Error log** in Web tab
2. Make sure all paths use your username
3. Ensure virtual environment is activated

### If static files don't load:

1. Verify the static files path is correct
2. Make sure `/static/` URL mapping is set

---

**Your free Course Diary System is now live! 🎉**
