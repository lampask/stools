from AbstractPlugin import Plugin
import cv2
import math
import numpy as np
from pywinauto.keyboard import send_keys

TARGET_OFFSET = 20
OPERATOR_TRESHOLD = 35
OPERATOR_MINIMAL_AREA = 25
TARGET_MINIMAL_AREA = 20
TURNING_CONTROL_OFFSET = 15
MINING_SIGNIFICANCE_LIMIT = 20
MINING_ZOOM_FRAME_DROP = 0

target_lower = (185, 25, 25)
target_higher = (255, 60, 60)

operator_lower = (187, 104, 170)
operator_higher = (255, 255, 255)

laser_lower = (232, 82, 60)
laser_higher = (255, 210, 125)

class MiningPlugin(Plugin):

    def __init__(self, img):
        self.max_target_distance = 0
        self.master_center = [0, 0]

        self.target_points = []
        self.operator_points = []

        self.mining = False

        super.__init__(self, img)

    def process_img(self, screen):
        target_mask = cv2.inRange(screen, target_lower, target_higher)
        contours, _ = cv2.findContours(target_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # get target points
        for cont in contours:
            if cv2.contourArea(cont) <= TARGET_MINIMAL_AREA:
                cv2.drawContours(target_mask, [cont], 0, (0,0,0))
            else:
                M = cv2.moments(cont)
                self.target_points.append([M['m10']/M['m00'],M['m01']/M['m00']])
        if len(self.target_points) == 3:
            target_rect = cv2.boundingRect(target_mask)
            target_rect_xy = (target_rect[0]-TARGET_OFFSET, target_rect[1]-TARGET_OFFSET)
            target_rect_hw = (target_rect[0]+target_rect[2]+TARGET_OFFSET, target_rect[1]+target_rect[3]+TARGET_OFFSET)

            # operator
            operator_mask = cv2.inRange(screen[int(target_rect_xy[1]):int(target_rect_hw[1]), int(target_rect_xy[0]):int(target_rect_hw[0])], operator_lower, operator_higher)
            contours, _ = cv2.findContours(operator_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cont in contours:
                if cv2.contourArea(cont) <= OPERATOR_MINIMAL_AREA:
                    cv2.drawContours(target_mask, [cont], 0, (0,0,0))
                else:
                    M = cv2.moments(cont)
                    centeroid = [M['m10']/M['m00'],M['m01']/M['m00']]
                    isunique = True
                    for i in self.operator_points:
                        if abs(centeroid[0]-i[0]) <= OPERATOR_TRESHOLD and  abs(centeroid[1]-i[1]) <= OPERATOR_TRESHOLD:
                            for j in range(2):
                                i[j] = (centeroid[j]+i[j])/2
                                isunique = False
                    if isunique: self.operator_points.append(centeroid)

            master_center = [0, 0]
            for point in self.target_points:
                point[0] -= target_rect[0]-TARGET_OFFSET
                master_center[0] += point[0]
                point[1] -= target_rect[1]-TARGET_OFFSET
                master_center[1] += point[1]
            master_center = [x/3 for x in master_center]
        
            # mining check
            laser_mask = cv2.inRange(screen[int(target_rect_xy[1]):int(target_rect_hw[1]), int(target_rect_xy[0]):int(target_rect_hw[0])], laser_lower, laser_higher)
            if np.count_nonzero(laser_mask) > MINING_SIGNIFICANCE_LIMIT:
                mining = True
            else:
                if mining:
                    max_target_distance = 0
                mining = False

            for point in self.target_points:
                dist = math.sqrt((point[0]-master_center[0])**2+(point[1]-master_center[1])**2)
                if dist > max_target_distance:
                    max_target_distance = dist

            # Draw
            for point in self.target_points:
                cv2.drawMarker(screen, (target_rect[0]-TARGET_OFFSET+int(point[0]), target_rect[1]-TARGET_OFFSET+int(point[1])), (0,0,255), thickness=2)
            if len(self.operator_points) == 3:
                cv2.rectangle(screen, target_rect_xy, target_rect_hw, (0, 0, 255), 2)
                for point in self.operator_points:
                    cv2.drawMarker(screen, (target_rect[0]-TARGET_OFFSET+int(point[0]),  target_rect[1]-TARGET_OFFSET+int(point[1])), (177,0,177), thickness=2)
            else:
                cv2.rectangle(screen, target_rect_xy, target_rect_hw, (0, 255, 0), 2)  
            cv2.drawMarker(screen, (target_rect[0]-TARGET_OFFSET+int(master_center[0]),  target_rect[1]-TARGET_OFFSET+int(master_center[1])), (0,255,0), thickness=1)

            self.target_points.sort(key=lambda x: x[0])
            self.operator_points.sort(key=lambda x: x[0])

            # CONTROLS
            if not self.mining:
                if abs(self.operator_points[0][0]-self.target_points[0][0]) >= TURNING_CONTROL_OFFSET or abs(self.operator_points[0][1]-self.target_points[0][1]) >= TURNING_CONTROL_OFFSET:
                    if self.operator_points[0][1] > self.target_points[0][1]:
                        send_keys('{RIGHT}')
                    else:
                        send_keys('{LEFT}')
                elif frames >= MINING_ZOOM_FRAME_DROP:
                    dirs = [0, 0]
                    for p1, p2 in zip(self.operator_points, self.target_points):
                        if math.sqrt((p1[0]-master_center[0])**2+(p1[1]-master_center[1])**2) > (max_target_distance+math.sqrt((p2[0]-master_center[0])**2+(p2[1]-master_center[1])**2))/2:
                            dirs[0] += 1
                        else:
                            dirs[1] += 1
                    if (dirs[0] > 0 or dirs[1] > 0):
                        send_keys('{DOWN}' if not dirs.index(max(dirs)) else '{UP}')
                        #print(f"{abs(p1[0]-master_center[0])} {abs(p2[0]-master_center[0])} | {abs(p1[1]-master_center[1])} {abs(p2[1]-master_center[1])}")
                    frames = 0