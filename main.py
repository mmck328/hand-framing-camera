import os
import sys
import time
import cv2
import numpy as np
import ctypes
sys.path.insert(0, "./lib")
import Leap
import pygame.mixer as pgmix

OFFSET = [80, 0, -15]
SCALE = 2.4

try: 
    os.mkdir('./photos')
except OSError:
    pass

pgmix.init()
shutter_sound = pgmix.Sound('./shutter.wav')
framing_sound = pgmix.music.load('./pipi.wav')

def inner_division(vec1, vec2, ratio):
    return Leap.Vector(*(ratio * np.array(vec1.to_float_array()) + (1 - ratio) * np.array(vec2.to_float_array())))

def vector_to_point(vector):
    x = (- (vector.x + OFFSET[0]) / vector.y ) * SCALE
    y = ((vector.z + OFFSET[2]) / vector.y) * SCALE
    return [x, y]

def image_info(img):
    if len(img.shape) == 3:
        height, width, channels = img.shape[:3]
    else:
        height, width = img.shape[:2]
        channels = 1
    return [height, width, channels]

def main():
    controller = Leap.Controller()
    controller.set_policy(Leap.Controller.POLICY_IMAGES)
    controller.set_policy(Leap.Controller.POLICY_OPTIMIZE_HMD)

    cap = cv2.VideoCapture(3)

    cv2.namedWindow('Preview',cv2.WINDOW_NORMAL)

    while not (controller.is_connected and cap.isOpened()):
        time.sleep(0.01)

    print('Connected to Devices')

    while True:
        frame = controller.frame()
        image = frame.images[0]

        # if image.is_valid:
        #     image_buffer_ptr = image.data_pointer
        #     ctype_array_def = ctypes.c_ubyte * image.width * image.height

        #     # as ctypes array
        #     as_ctype_array = ctype_array_def.from_address(int(image_buffer_ptr))
        #     # as numpy array
        #     image_np = np.ctypeslib.as_array(as_ctype_array)

        #     image_np.shape = (image.height, image.width)
        #     cv2.imshow('IR image', image_np)


        canvas = np.zeros((500, 500, 3), np.uint8)
        
        dummy, cam_image = cap.read()
        cam_image = cv2.flip(cam_image, -1)
        canvas = np.copy(cam_image)
        radius = 640


        pinch = False

        for hand in frame.hands:
            for finger in hand.fingers:
                for i in range(4):
                    vec = finger.bone(i).next_joint
                    x, y = vector_to_point(vec)
                    cv2.circle(canvas, (int(radius + x * radius), int(radius + y * radius)), 5, [255, 255, 255], 2)

        if len(frame.hands) == 2:
            if not pgmix.music.get_busy():
                pgmix.music.play(-1)

            corners = []
            for hand in frame.hands:
                for finger in hand.fingers:
                    if finger.type == 0: # thumb
                        thumbbase = finger.bone(1).next_joint
                    elif finger.type == 1: # index
                        indexbase = finger.bone(1).next_joint
                vec = inner_division(thumbbase, indexbase, 0.7)
                x, y = vector_to_point(vec)
                corners.append((x, y))

                if hand.pinch_strength > 0.85:
                    color = [0, 0, 255]
                    pinch = True
                else:
                    color = [255, 0, 0]
                cv2.circle(canvas, (int(radius + x * radius), int(radius + y * radius)), 5, color, -1)

            lefttop = (int(radius + radius * min(corners[0][0], corners[1][0])), int(radius + radius * min(corners[0][1], corners[1][1])))
            rightbottom = (int(radius + radius * max(corners[0][0], corners[1][0])), int(radius + radius * max(corners[0][1], corners[1][1])))
            cv2.rectangle(canvas, lefttop, rightbottom, (0, 255, 0), 2)
            cv2.imshow('Preview', canvas)

            if pinch:
                photo = cam_image[lefttop[1]:rightbottom[1], lefttop[0]:rightbottom[0]]
                height, width, channel = image_info(photo)
                if height != 0 and width != 0:
                    pgmix.music.stop()
                    shutter_sound.play()
                    filename = "./photos/%s.jpg" % time.strftime("%Y%m%d%H%M%S", time.localtime())
                    cv2.imwrite(filename, photo)
                    print("Saved: %s" % filename)
                    cv2.imshow('Preview', photo)
                    cv2.waitKey(1500)

        else:
            pgmix.music.stop()
            cv2.imshow('Preview', canvas)

        k = cv2.waitKey(33) & 0xFF
        if k == 27:
            return


if __name__ == "__main__":
    main()