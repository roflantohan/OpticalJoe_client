import cv2

class VideoCapture():
    def __init__(self, port=600):
        self.port=port

    def connect_camera(self):
        path = (
            f"gst-launch-1.0 udpsrc port=6000 ! "
            f"application/x-rtp,encoding-name=H264 ! rtph264depay ! avdec_h264 ! "
            f"videoconvert ! videoscale ! video/x-raw,format=BGR ! appsink drop=1"
        )
        return cv2.VideoCapture(path, cv2.CAP_GSTREAMER)
