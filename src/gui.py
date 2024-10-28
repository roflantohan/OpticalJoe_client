import cv2
import math
import time
import numpy as np

from src.libs.shared_memory import SharedMemory
from src.gst_receiver import GstReceiver

class TrackerAppGUI(SharedMemory):

    def __init__(self, shared_dict):
        super().__init__(shared_dict)
        self.name_app = "TrackerApp"

        cam_type = "UDP"
        cam_path = ""

        # camera param
        self.cap = None # VideoCapture()
        self.cam_pipeline = "" 
        self.cam_param = (cam_type, cam_path)

        # frame param
        self.center_points = [(0,0), (0,0), (0,0)] # [left, middle, right]

        # fps
        self.time_period = [None, None] # [start, end]
        self.frames_count = 0
        self.fps = 0

        # mouse param
        self.mouse_xy = (-1, -1) # [x,y]
        self.is_drawing = False

        # tracking param for request
        self.roi_size = 50 # pixels one of side
        self.init_roi = None # (x, y, h, w)

        self.border_size = 0.3 # max value = 1.0
        self.is_center = False
        self.is_osd = True

        # utils
        self.color_green = (0, 255, 51)
        self.color_red = (68, 36, 204)
        self.color_orange = (0, 176, 255)
        
        self.server_param = dict()

    def connect_camera(self):
        path = "gst-launch-1.0 udpsrc port=6000 ! application/x-rtp,encoding-name=H264 ! rtph264depay ! avdec_h264  ! videoconvert ! videoscale ! video/x-raw,format=BGR ! appsink drop=1"
        self.cap = cv2.VideoCapture(path, cv2.CAP_GSTREAMER)
    
    def to_draw_preview_roi(self, frame):
        center_p1 = self.center_points[0]
        center_p2 = self.center_points[2]

        top_left = (self.mouse_xy[0] - self.roi_size // 2, self.mouse_xy[1] - self.roi_size // 2)
        bottom_right = (self.mouse_xy[0] + self.roi_size // 2, self.mouse_xy[1] + self.roi_size // 2)
        self.to_draw_border(frame, top_left, bottom_right, 10, 2, self.color_red) #mouse targer
        self.to_draw_border(frame, center_p1, center_p2, 10, 2, self.color_red) #center target

    def start(self):
        video = GstReceiver()
        self.connect_camera()

        cv2.namedWindow(self.name_app)
        cv2.setMouseCallback(self.name_app, self.mouse_handler)
        cv2.namedWindow(self.name_app, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(self.name_app, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        self.time_period[0] = time.time()

        while(True):
            if not video.frame_available():
                continue

            new_frame = video.frame()
            frame = np.copy(new_frame)

            # ret, frame = self.cap.read()

            # if not ret: 
            #     continue

            self.receive_incoming_param()
            self.get_center_frame(frame)
            self.calculate_fps()

            if self.is_drawing:
                self.to_draw_preview_roi(frame)

            if self.is_osd:
                self.to_draw_OSD(frame)

            cv2.imshow(self.name_app, frame)

            # Key control 
            key = cv2.waitKey(1) & 0xFF

            if key == 27:
                break
            
            if key == ord("q"):
                (x, y) = (self.mouse_xy[0] - self.roi_size // 2, self.mouse_xy[1] - self.roi_size // 2)
                self.init_roi = (x, y, self.roi_size, self.roi_size)
                self.is_center = False
                self.send_init_roi()
                continue
            if key == ord("s"):
                self.init_roi = False
                self.is_center = False
                self.send_init_roi()
                continue
            if key == ord('w'):
                (x, y) = self.center_points[0]
                self.init_roi = (x, y, self.roi_size, self.roi_size)
                self.speed_factor = False
                self.send_init_roi()
                continue
            if key == ord('g'):
                self.send_autopilot()
                continue
            if key == ord('='):
                if self.roi_size < 100:
                    self.roi_size += 10
                    continue
            if key == ord('-'):
                if self.roi_size > 30:
                    self.roi_size -= 10
                    continue
            if key == ord("r"):
                if self.server_param["target_roi"] and self.init_roi:
                    self.send_retarget()
                    continue
            if key == ord("l"):
                self.is_osd = not self.is_osd

        self.cap.release()
        cv2.destroyAllWindows()


    def to_draw_OSD(self, frame):
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        font_thickness = 1

        text = f'FPS: {self.fps}'
        font_color = self.color_green if self.fps > 12 else self.color_red
        text_position = (10, 20)
        cv2.putText(frame, text, text_position, font, font_scale, font_color, font_thickness, cv2.LINE_AA)

        text = f"WS: {"YES" if self.server_param["is_server_connection"] else "NO.Reconnect..."}"
        font_color = self.color_green if self.server_param["is_server_connection"] else self.color_red
        text_position = (100, 20)
        cv2.putText(frame, text, text_position, font, font_scale, font_color, font_thickness, cv2.LINE_AA)

        roi = self.server_param["target_roi"]
        target_x = 0
        target_y = 0
        if roi:
            (x, y, h, w) = roi
            target_x = x + w // 2
            target_y = y + h // 2
        
        text = f"Tracking(q): {f"({target_x}, {target_y})" if self.server_param["is_tracking"] else "OFF"}"
        font_color = self.color_green if self.server_param["is_tracking"] else self.color_red
        text_position = (10, 40)
        cv2.putText(frame, text, text_position, font, font_scale, font_color, font_thickness, cv2.LINE_AA)

        if self.server_param["new_course"]:
            text = f"Autopilot(g): ({self.server_param["new_course"][0]: .2f}, {self.server_param["new_course"][1]: .2f}, {self.server_param["new_course"][2]: .2f}, {self.server_param["new_course"][3]: .2f}) "
        else:
            text = f"Autopilot(g): (0, 0, 0, 0) "
        font_color = self.color_green if self.server_param["is_autopilot"] else self.color_red
        text_position = (10, 60)
        cv2.putText(frame, text, text_position, font, font_scale, font_color, font_thickness, cv2.LINE_AA)



    def mouse_handler(self, event, x, y, flags, param):
        if event == cv2.EVENT_RBUTTONDOWN:
            self.init_roi = None

        if event == cv2.EVENT_LBUTTONDOWN:
            self.init_roi = (x - self.roi_size // 2, y - self.roi_size // 2, self.roi_size, self.roi_size)
            self.send_init_roi()
        
        if event == cv2.EVENT_MOUSEMOVE:
            self.mouse_xy = (x, y)
            self.is_drawing = True

    def get_rect_param(self, square):
        w = math.floor(math.sqrt(square*(16/9)))
        h = math.floor(square / w)
        return (w, h)

    def get_center_frame(self, frame):
        height, width, _ = frame.shape
        len = self.roi_size
        x = width // 2
        y = height // 2
        self.center_points[0] = (x - len // 2, y - len // 2)
        self.center_points[1] = (x,y)
        self.center_points[2] = (x + len // 2, y + len // 2)
    
    def to_draw_border(self, frame, p1, p2, length=5, thickness=2, color=(0, 0, 255)):
        # top left corner
        cv2.line(frame, p1, (p1[0] + length, p1[1]), color, thickness)
        cv2.line(frame, p1, (p1[0], p1[1] + length), color, thickness)
        # top right corner
        cv2.line(frame, (p2[0], p1[1]), (p2[0] - length, p1[1]), color, thickness)
        cv2.line(frame, (p2[0], p1[1]), (p2[0], p1[1] + length), color, thickness)
        # bottom left corner
        cv2.line(frame, (p1[0], p2[1]), (p1[0] + length, p2[1]), color, thickness)
        cv2.line(frame, (p1[0], p2[1]), (p1[0], p2[1] - length), color, thickness)
        # bottom right corner
        cv2.line(frame, p2, (p2[0] - length, p2[1]), color, thickness)
        cv2.line(frame, p2, (p2[0], p2[1] - length), color, thickness)

    def calculate_fps(self):
        self.frames_count += 1
        if(self.frames_count == 5):
            self.time_period[1] = time.time()
            seconds = self.time_period[1] - self.time_period[0]
            self.fps = self.frames_count // seconds
            self.frames_count = 0
            self.time_period[0] = time.time()

    def to_draw_line(self, frame, p1, p2):
        cv2.line(frame, p1, p2,  self.color_green, 1)

    def is_belong_rect(self, point_top_left, point_bottom_right):
        roi = self.server_param["target_roi"]
        if roi == None:
            return None
        return point_top_left[0] <= roi[0] <= point_bottom_right[0] and point_top_left[1] <= roi[1] <= point_bottom_right[1]
    
    def receive_incoming_param(self):
        headers = ["is_server_connection", "is_tracking", "is_autopilot", "target_roi", "error_px", "new_course", "altitude", "airspeed", "groundspeed", "heading", "vertical_speed", "ground_distance"]
        for name in headers:
            self.server_param[name] = self.read_data(name)

    def send_init_roi(self):
        self.write_data("init_roi", self.init_roi)
        self.write_data("roi_size", self.roi_size)

    def send_retarget(self):
        self.write_data('is_retarget', True)
        self.write_data("roi_size", self.roi_size)

    def send_autopilot(self):
        self.write_data("new_is_autopilot", not self.server_param["is_autopilot"])
