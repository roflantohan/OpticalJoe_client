# OpticJoe client - native app for using tracking system(prototype)

### How to start

Complete all instructions below and use start_app.sh/stop_app.sh for launch/stop app.
For testing you need to use RTSP to connect camera, you can find it on utils/gst_scripts/gst_rtsp_server.py(work only for Linux/MacOS)

### How to setup environment

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements
```

### How to install OpenCV with Gstreamer

Go to utils/opencv_scripts and choose guide for your OS

### How to setup drone's simulation (SITL)

https://ardupilot.org/dev/docs/setting-up-sitl-on-linux.html
