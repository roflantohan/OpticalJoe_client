import gi
import numpy as np

gi.require_version('Gst', '1.0')
from gi.repository import Gst

class VideoCapture():
    def __init__(self, port=6000):
        Gst.init(None)
        self.port = port
        self._frame = None
        self.video_source = f'udpsrc port={self.port} '
        # Cam -> CSI-2 -> H264 Raw (YUV 4-4-4 (12bits) I420)
        #self.video_codec = '! application/x-rtp, payload=96 ! rtph264depay ! h264parse ! avdec_h264'
        self.video_codec = '! queue ! application/x-rtp,encoding-name=H264 ! rtph264depay ! avdec_h264'
        self.video_decode = ' ! videoconvert ! videoscale ! video/x-raw,format=BGR'
        self.video_sink_conf = '! appsink emit-signals=true sync=false max-buffers=2 drop=true'
        self.video_pipe = None
        self.video_sink = None
        self.run()

    def start_gst(self, config):
        command = ' '.join(config)
        self.video_pipe = Gst.parse_launch(command)
        self.video_pipe.set_state(Gst.State.PLAYING)
        self.video_sink = self.video_pipe.get_by_name('appsink0')

    @staticmethod
    def gst_to_opencv(sample):
        buf = sample.get_buffer()
        caps = sample.get_caps()
        frame = np.ndarray(
            (
                caps.get_structure(0).get_value('height'),
                caps.get_structure(0).get_value('width'),
                3
            ),
            buffer=buf.extract_dup(0, buf.get_size()), 
            dtype=np.uint8
        )
        return frame

    def frame(self):
        return self._frame

    def frame_available(self):
        return type(self._frame) != type(None)

    def run(self):
        self.start_gst([
            self.video_source,
            self.video_codec,
            self.video_decode,
            self.video_sink_conf
        ])
        self.video_sink.connect('new-sample', self.callback)

    def callback(self, sink):
        sample = sink.emit('pull-sample')
        new_frame = self.gst_to_opencv(sample)
        self._frame = new_frame
        return Gst.FlowReturn.OK


# if __name__ == '__main__':
#     # Create the video object
#     # Add port= if is necessary to use a different one
#     video = GstReceiver()

#     while True:
#         # Wait for the next frame
#         if not video.frame_available():
#             continue

#         frame = video.frame()
#         cv2.imshow('frame', frame)
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break
