# Packaging Seer's Orb

This project is configured to be packaged as a standalone desktop application for both **Windows** and **macOS** using **GitHub Actions**.

## How to Build

Since you are developing on Windows but need a Mac version for your team, the easiest way is to let GitHub build it for you.

### 1. Push to GitHub
Ensure this repository is pushed to GitHub.

```bash
git add .
git commit -m "Configure packaging"
git push
```

### 2. Trigger the Build
1. Go to your repository on GitHub.
2. Click the **Actions** tab.
3. Select **Build Application** from the left sidebar.
4. Click the **Run workflow** button (dropdown) on the right.
5. Click **Run workflow**.

### 3. Download Artifacts
1. Wait for the `build-windows` and `build-macos` jobs to complete (usually 3-5 minutes).
2. Click on the run (e.g., "Build Application #1").
3. Scroll down to the **Artifacts** section.
4. Download `SeersOrb-Windows` or `SeersOrb-macOS`.

### 4. Distribute to Team
- **Windows**: Unzip the file. Run `SeersOrb/SeersOrb.exe`.
- **macOS**: Unzip the file. Run the `SeersOrb` executable inside the folder.
  - *Note*: Since the app is not code-signed with an Apple Developer ID, your team might need to right-click open it and allow it in Security settings ("App is from an unidentified developer").

## Local Building (Windows Only)
If you want to build the Windows version locally:

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Run the build command:
   ```bash
   pyinstaller packaging/SeersOrb.spec --noconfirm
   ```
3. The app will be in `dist/SeersOrb`.

## Data Persistence
When running the packaged "portable" version (the folder you unzip), all data (decks, cache) will be saved **inside that folder** within the `data/` subdirectory. This makes it easy for your team to back up their data by just keeping the folder.
