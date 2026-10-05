# TKU EMI Suckless (Android)

A lightweight Android and mobile/web client for Tamkang University (TKU) Educational Management Information System (EMIS).

Built with a local Python Flask service and an Android WebView bootstrap via Buildozer (`python-for-android`), this app provides a clean, responsive interface to manage and track your academic progress at TKU without the bloated web portal.

## Features

- **Authentication**: Secure single sign-on (SSO) login with local session caching.
- **Student Profile**: View student details, department, and academic study progress.
- **Graduation Tracker**: Calculate earned vs. required credits and track missing mandatory courses.
- **Grade History**: View comprehensive course grades across all academic years.
- **Course Planner**: Search courses available this semester and manage custom class schedules.
- **Android Internal Storage**: Stores session data and cached user data in the app's internal writable directory (`.userData/`).

## Architecture & Tech Stack

- **Backend**: Python 3, Flask, `requests`, `beautifulsoup4`
- **Frontend**: Responsive HTML5, CSS3, JavaScript (REST API bridge via `fetch`)
- **Android Runtime**: [Buildozer](https://buildozer.readthedocs.io/) & [python-for-android](https://python-for-android.readthedocs.io/) using `p4a.bootstrap = webview`

## Running Locally (Development / Web)

You can run and test the app locally in any modern desktop or mobile browser:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/GGQQmax/tku-emi-suckless-android.git
   cd tku-emi-suckless-android
   ```

2. **Set up a virtual environment and install dependencies**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Launch the local server**:
   ```bash
   python3 main.py
   ```

4. **Open in browser**:
   Navigate to [http://127.0.0.1:5000/](http://127.0.0.1:5000/).

---

## Building the Android APK

### Automated GitHub Actions (Recommended)
This repository includes a GitHub Actions workflow (`.github/workflows/android.yml`) that automatically builds the Android APK:
- Every push to `main` or `master` compiles the debug APK and uploads it as a workflow artifact.
- Pushing a version tag (`v*`) automatically builds and publishes the APK to GitHub Releases.

### Building Locally with Buildozer
To compile the APK locally, follow the [Buildozer Installation Guide](https://buildozer.readthedocs.io/en/latest/installation/):

#### 1. System Dependencies (Ubuntu / Debian)
```bash
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip python3-virtualenv \
  autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev \
  libtinfo6 cmake libffi-dev libssl-dev automake autopoint gettext
```

For **Fedora**:
```bash
sudo dnf install java-17-openjdk-devel git zip unzip autoconf automake libtool \
  pkgconfig zlib-devel ncurses-devel cmake libffi-devel openssl-devel gettext-devel
```

#### 2. Install Buildozer & Cython
```bash
pip install --upgrade buildozer cython
```

#### 3. Build APK
```bash
# Build debug APK
buildozer android debug

# Build release APK
buildozer android release
```

The compiled `.apk` will be output in the `bin/` directory.

---

## License

[BEER-WARE LICENSE (Revision 42)](https://raw.githubusercontent.com/GGQQmax/tku-emi-suckless/master/LICENSE)
