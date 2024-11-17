import cv2
import math
import time
from src.libs.shared_memory import SharedMemory

class TrackerAppGUI():

    def __init__(self, shmem: SharedMemory):
        self.shmem = shmem
        self.name_app = "TrackerApp"

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
        self.roi_size = 30 # pixels one of side
        self.init_roi = None # (x, y, h, w)

        self.border_size = 0.3 # max value = 1.0
        self.is_center = False
        self.is_osd = True

        # utils
        self.color_green = (0, 255, 51)
        self.color_red = (68, 36, 204)
        self.color_orange = (0, 176, 255)
        
        self.server_param = dict()

        self.headers = [
            "is_server_connection", 
            "is_tracking", 
            "is_autopilot", 
            "target_roi", 
            "error_px", 
            "new_course", 
            "altitude", 
            "airspeed", 
            "groundspeed", 
            "heading", 
            "vertical_speed", 
            "ground_distance", 
            "flight_mode",
            "throttle",
        ]

    def connect_camera(self):
        path = "gst-launch-1.0 udpsrc port=6000 ! application/x-rtp,encoding-name=H264 ! rtph264depay ! avdec_h264  ! videoconvert ! videoscale ! video/x-raw,format=BGR ! appsink drop=1"
        return cv2.VideoCapture(path, cv2.CAP_GSTREAMER)
    
    def to_draw_preview_roi(self, frame):
        center_p1 = self.center_points[0]
        center_p2 = self.center_points[2]

        top_left = (self.mouse_xy[0] - self.roi_size // 2, self.mouse_xy[1] - self.roi_size // 2)
        bottom_right = (self.mouse_xy[0] + self.roi_size // 2, self.mouse_xy[1] + self.roi_size // 2)
        self.to_draw_border(frame, top_left, bottom_right, 5, 2, self.color_red) #mouse targer
        self.to_draw_border(frame, center_p1, center_p2, 5, 2, self.color_red) #center target

    def start(self):
        cv2.namedWindow(self.name_app)
        cv2.setMouseCallback(self.name_app, self.mouse_handler)
        cv2.namedWindow(self.name_app, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(self.name_app, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        # cv2.setWindowProperty(self.name_app, 1920, 1080)

        cap = self.connect_camera()

        self.time_period[0] = time.time()

        while(True):
            ret, frame = cap.read()
            if not ret: 
                continue

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
            
            if key == ord('g'):
                self.send_flight_mode("GUIDED")
                continue
            if key == ord("m"):
                self.send_flight_mode("MANUAL")
                continue

        cap.release()
        cv2.destroyAllWindows()

    def to_draw_OSD(self, frame):
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        font_thickness = 1

        text = f'FPS: {self.fps}'
        font_color = self.color_green if self.fps > 12 else self.color_red
        text_position = (10, 20)
        cv2.putText(frame, text, text_position, font, font_scale, font_color, font_thickness, cv2.LINE_AA)

        text = f"WS"
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

        flight_mode = self.server_param.get("flight_mode", None)
        text = f"FMode: {flight_mode}"
        font_color = self.color_green if flight_mode else self.color_red
        text_position = (10, 100)
        cv2.putText(frame, text, text_position, font, font_scale, font_color, font_thickness, cv2.LINE_AA)

        air_speed = self.server_param.get("airspeed", 0) or 0
        text = f"AirS:{air_speed: .2f}"
        font_color = self.color_green if air_speed else self.color_red
        text_position = (10, 120)
        cv2.putText(frame, text, text_position, font, font_scale, font_color, font_thickness, cv2.LINE_AA)

        ground_speed = self.server_param.get("groundspeed", 0) or 0
        text = f"GndS:{ground_speed: .2f}"
        font_color = self.color_green if ground_speed else self.color_red
        text_position = (10, 140)
        cv2.putText(frame, text, text_position, font, font_scale, font_color, font_thickness, cv2.LINE_AA)

        vertical_speed = self.server_param.get("vertical_speed", 0) or 0
        text = f"VtlS:{vertical_speed: .2f}"
        font_color = self.color_green if vertical_speed else self.color_red
        text_position = (10, 160)
        cv2.putText(frame, text, text_position, font, font_scale, font_color, font_thickness, cv2.LINE_AA)

        heading = self.server_param.get("heading", 0) or 0
        text = f"Head: {heading}"
        font_color = self.color_green if heading else self.color_red
        text_position = (10, 180)
        cv2.putText(frame, text, text_position, font, font_scale, font_color, font_thickness, cv2.LINE_AA)

        altitude = self.server_param.get("altitude", 0) or 0
        text = f"Alt:{altitude: .2f}"
        font_color = self.color_green if altitude else self.color_red
        text_position = (10, 200)
        cv2.putText(frame, text, text_position, font, font_scale, font_color, font_thickness, cv2.LINE_AA)
        
        throttle = self.server_param.get("throttle", 0) or 0
        text = f"Tht:{throttle: .2f}"
        font_color = self.color_green if throttle else self.color_red
        text_position = (10, 220)
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
    
    def to_draw_border(self, frame, p1, p2, length=3, thickness=1, color=(0, 0, 255)):
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
        for name in self.headers:
            self.server_param[name] = self.shmem.read_data(name)

    def send_init_roi(self):
        self.shmem.write_data("init_roi", self.init_roi)
        self.shmem.write_data("roi_size", self.roi_size)

    def send_retarget(self):
        self.shmem.write_data('is_retarget', True)
        self.shmem.write_data("roi_size", self.roi_size)

    def send_flight_mode(self, mode):
        self.shmem.write_data("new_flight_mode", mode)
