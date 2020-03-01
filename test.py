
import cv2 as cv2
import numpy as np
from networktables import NetworkTables

def nothing(x):
    pass

def main():

    # To see messages from networktables, you must setup logging
    import logging
    logging.basicConfig(level=logging.DEBUG)

    # Init Networktables Settings
    NetworkTables.initialize(server='127.0.0.1')
    sd = NetworkTables.getTable('SmartDashboard')
    
    
    cap = cv2.VideoCapture("video3.mp4")

    cv2.namedWindow("Trackbars")
    cv2.createTrackbar("L-H", "Trackbars", 10, 255, nothing)
    cv2.createTrackbar("L-S", "Trackbars", 111, 255, nothing)
    cv2.createTrackbar("L-V", "Trackbars", 45, 180, nothing)
    cv2.createTrackbar("U-H", "Trackbars", 81, 255, nothing)
    cv2.createTrackbar("U-S", "Trackbars", 255, 255, nothing)
    cv2.createTrackbar("U-V", "Trackbars", 255, 255, nothing)
    cv2.createTrackbar("Brightness", "Trackbars", 0, 255, nothing)

    max_area = 9500
    min_area = 250


    cap.set(int(5), 30) # FPS

    while True:

       # cameraBrightness = cv2.getTrackbarPos("Brightness", "Trackbars")

        #cap.set(int(10), cameraBrightness) # Brightness 1-100
        #cap.set(10, cameraBrightness)
        _, frame = cap.read()

       
        sd.putString('VisionState', "start")
        visionState = sd.getString('VisionState', "none")
        print("visionState: " + visionState)
        if visionState == "start" or visionState == "SendingData":
            width  = cap.get(3) # float
            height = cap.get(4) # float

            kernel = np.ones((3,3), np.float32)/9
            smoothed = cv2.filter2D(frame, -1, kernel)
            blur = cv2.medianBlur(smoothed, 5)

            hsv = cv2.cvtColor(blur, cv2.COLOR_RGB2HSV)


            l_h = cv2.getTrackbarPos("L-H", "Trackbars")
            l_s = cv2.getTrackbarPos("L-S", "Trackbars")
            l_v = cv2.getTrackbarPos("L-V", "Trackbars")
            u_h = cv2.getTrackbarPos("U-H", "Trackbars")
            u_s = cv2.getTrackbarPos("U-S", "Trackbars")
            u_v = cv2.getTrackbarPos("U-V", "Trackbars")


            lower_red = np.array([l_h, l_s, l_v])
            upper_red = np.array([u_h ,u_s , u_v])

            # Log the selected HSV Parameters for Calibration
            #print([l_h, l_s, l_v])
            #print([u_h ,u_s , u_v])

            mask = cv2.inRange(hsv, lower_red, upper_red)

            # Contour Detection
            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            filteredContours = [];
            for cnt in contours:
                area = cv2.contourArea(cnt) #contour area

                # Conditions: If the Conotour stands for the area condition
                if area > max_area or area < min_area:
                    continue
                    
                
                x,y,w,h = cv2.boundingRect(cnt)

                # Condition: If The Rect/Contour areas in the range standart
                if w*h/area < 4.9 or w*h/area > 8:
                    continue


                if x < 10 or x > width - 10:
                    continue
                if y < 10 or y > height - 10:
                    continue
        

                filteredContours.append(cnt)

            #Select The Contour By the Biggest Rect area
            if len(filteredContours) != 0:
                maxArea = 0
                selectedIndex = 0
                i = 0
                for cont in filteredContours:
                    x,y,w,h = cv2.boundingRect(cont)
                    if w*h > maxArea:
                        maxArea = w*h
                        selectedIndex = i
                    i = i+1
                final_contour = filteredContours[selectedIndex]
                x,y,w,h = cv2.boundingRect(final_contour)
                area = cv2.contourArea(final_contour) #contour area
                cv2.rectangle(frame, (x,y), (x+w, y+h), (0, 255, 0), 3)

                # Rotated Rect:
                rect = cv2.minAreaRect(final_contour)
                box = cv2.boxPoints(rect)
                box = np.int0(box)
                cv2.drawContours(frame,[box],0,(0,0,255),2)

                # Calculate Angle
                angle = rect[2]
                if abs(angle) > 40: # Example -73 needs to be negative: -. On the left of the target
                    angle = 90 - abs(angle)
                else:
                    angle = abs(angle)

                angle = round(angle, 2)
                area = round(area, 2)

                centerContourPoint_X = int(x + w/2)
                centerContourPoint_Y = int(y + h/2)

                font = cv2.FONT_HERSHEY_SIMPLEX 

                # org 
                org = (x, y - 10) 
                
                # fontScale 
                fontScale = 0.4
                
                # Blue color in BGR 
                color = (255, 255, 255) 
                
                # Line thickness of 2 px 
                thickness = 1
                
                # Using cv2.putText() method 
                cv2.putText(frame, 'Contour Area: ' + str(area), org, font,fontScale, color, thickness, cv2.LINE_AA) 
                cv2.putText(frame, 'Rect Area: ' + str(w*h), (x, y - 30), font,fontScale, color, thickness, cv2.LINE_AA) 
                cv2.putText(frame, 'Rect/Contour Areas: ' + str(round(w*h/area, 2)), (x, y - 50), font,fontScale, color, thickness, cv2.LINE_AA) 
                cv2.putText(frame, 'Angle: ' + str(angle), (x, y - 70), font,fontScale, color, thickness, cv2.LINE_AA) 

                # Draw Center Line:
                cv2.line(frame, (int(width / 2),0), (int(width / 2), int(height)), (0,120,0), 1, cv2.LINE_AA, 0)
                cv2.arrowedLine(frame, (int(width / 2),centerContourPoint_Y), (centerContourPoint_X, centerContourPoint_Y), (255,0,23), 1, cv2.LINE_AA, 0)

                # Publish the data to NT:
                sd.putString('VisionState', "SendingData")
                sd.putNumber('center', centerContourPoint_X)
                sd.putNumber('widthFrame', width)

            cv2.imshow("Mask", mask)

        elif visionState == "none" or visionState == "done":
            print("Waiting for trigget")

        cv2.imshow("Original Image", frame)

        key = cv2.waitKey(1)
        if key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

main()
