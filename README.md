# Smart Gym Exercise Form Detection

Real-time CV gym assistant with:
- BlazePose landmark extraction (33 keypoints)
- Multi-exercise angle + form analysis (5 exercises)
- FSM rep counting with smoothing
- Novel fatigue detection (ROM + velocity degradation)
- Bilateral asymmetry scoring and trend logging
- Form-score + XP gamification engine
- SQLite persistence + Streamlit app (exercise selection, live launch, analytics)

## Setup

### WSL or Linux (bash)

```bash
cd /path/to/CV_project
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

Deactivate later with `deactivate`.

**WSL tip (Conda):** If your prompt still shows `(base)`, run `conda deactivate` until only `(.venv)` remains. Otherwise `pip` and `python` can point at different interpreters and you may get missing modules (e.g. `cv2`).

**If `ModuleNotFoundError: No module named 'cv2'`:** the import comes from OpenCV’s wheel — install with `python3 -m pip install opencv-python` (do **not** run `pip install cv2`; that package name does not exist on PyPI). Then verify:

```bash
python3 -c "import cv2; print(cv2.__version__)"
```

### Windows (PowerShell)

```powershell
cd C:\path\to\CV_project
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Windows (Command Prompt)

```bat
cd C:\path\to\CV_project
py -3 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Use **either** WSL **or** native Windows for the same folder; venv layouts differ (`bin` vs `Scripts`), so do not mix activators across OSes for one `.venv`.

### Troubleshooting

**`AttributeError: module 'mediapipe' has no attribute 'solutions'`**  
Newer Python wheels ship MediaPipe **Tasks** only (no `mp.solutions`). This project **auto-switches** to the Tasks Pose Landmarker when `solutions` is missing. Use **`mediapipe>=0.10.33`** (`pip install -U -r requirements.txt`). The first run downloads `pose_landmarker_lite.task` into `src/gymcv/pose/models/` (needs internet once).

**Live video does not appear in the browser**  
That is expected: the camera feed opens in a **separate desktop window** titled **Smart Gym — Live**. On Windows, a **console window** may also open so you can see errors from the child process. Check the taskbar and Alt+Tab. Allow camera access for **Python** in Windows privacy settings if the window is black.

**If MediaPipe fails to load native libraries**  
Use a **64-bit Python 3.10–3.12** virtual environment on Windows; Python **3.13** is supported when the `mediapipe` wheel loads correctly—if you still see DLL/ctypes errors, try Python **3.11** and reinstall dependencies.

## Run (recommended)

From the **project root**:

```bash
streamlit run src/dashboard.py
```

1. Open the **Live workout** tab, choose an exercise and webcam index, then click **Open webcam & start session**.
2. A separate **Smart Gym — Live** window opens: live pose, reps, form score, fatigue, asymmetry, and XP on the video.
3. Press **`q`** in that window to stop and write results to SQLite.
4. Open the **Analytics** tab for charts and session tables (use the sidebar DB path if needed).

## CLI only (no Streamlit)

Running `python src/main.py` without flags prints a short hint. For a direct webcam session:

```bash
python src/main.py --no-launcher --exercise squat --camera 0
```

**Video file** (must match `--exercise` to the movement in the clip):

```bash
python src/main.py --video path/to/video.mp4 --exercise squat
```
