#pip install pycairo PyGObject
#https://stackoverflow.com/questions/71369726/no-module-named-gi

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GObject

Gst.init(None)

class RTSPServer(GstRtspServer.RTSPMediaFactory):
    def __init__(self):
        super(RTSPServer, self).__init__()
        # builded camera like a source (h265)
        # self.set_launch("( autovideosrc ! videoconvert ! x265enc tune=zerolatency bitrate=1000  speed-preset=ultrafast ! rtph265pay name=pay0 pt=96 )")
        self.set_launch("( autovideosrc ! video/x-raw,width=1280,height=720,framerate=30/1 ! videoconvert ! x264enc tune=zerolatency bitrate=1000  speed-preset=ultrafast ! rtph264pay name=pay0 pt=96 )")
        # another rtsp stream like a source
        # self.set_launch("( rtspsrc location=rtsp://192.168.1.100:8559/test latency=0 ! rtph265depay ! rtph265pay name=pay0 pt=96 )")


class Server:
    def __init__(self):
        self.server = GstRtspServer.RTSPServer()
        self.server.set_service("8554")
        factory = RTSPServer()
        factory.set_shared(True)
        mount_points = self.server.get_mount_points()
        mount_points.add_factory("/main.264", factory)
        self.server.attach(None)
        print("RTSP server is running at rtsp://0.0.0.0:8554/main.264")

if __name__ == '__main__':
    loop = GObject.MainLoop()
    server = Server()
    loop.run()

# for connect to server (procotols=tcp)
# gst-launch-1.0 rtspsrc location=rtsp://0.0.0.0:8554/main.264 latency=0 buffer-mode=auto protocols=udp ! rtph265depay ! h265parse ! avdec_h265 ! videoconvert ! autovideosink
