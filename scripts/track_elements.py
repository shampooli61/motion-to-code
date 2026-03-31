import cv2
import numpy as np

class ElementTracker:
    def __init__(self, video_source):
        self.video_source = video_source
        self.cap = cv2.VideoCapture(video_source)
        self.tracker = cv2.TrackerKCF_create()
        self.is_tracking = False
        self.bbox = None  # bounding box for tracking

    def start_tracking(self):
        ret, frame = self.cap.read()
        if ret:
            # Let the user select the bounding box
            self.bbox = cv2.selectROI('Tracking', frame, fromCenter=False, showCrosshair=True)
            self.tracker.init(frame, self.bbox)
            self.is_tracking = True

    def update(self):
        ret, frame = self.cap.read()
        if not ret:
            return frame, None
        if self.is_tracking:
            success, self.bbox = self.tracker.update(frame)
            if success:
                (x, y, w, h) = [int(v) for v in self.bbox]
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        return frame, self.bbox

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    video_source = 'path/to/video.mp4'  # Change this to your video path
    tracker = ElementTracker(video_source)
    tracker.start_tracking()

    while True:
        frame, bbox = tracker.update()
        cv2.imshow('Tracking', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    tracker.release()