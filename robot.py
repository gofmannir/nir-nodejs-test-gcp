from networktables import NetworkTables


def main():

    # To see messages from networktables, you must setup logging
    import logging
    logging.basicConfig(level=logging.DEBUG)

    # Init Networktables Settings
    NetworkTables.initialize(server='127.0.0.1')

    sd = NetworkTables.getTable('SmartDashboard')
    sd.putString('VisionState', "start")

    while True:

        visionState = sd.getString('VisionState', "none")
        if visionState == "SendingData":
            center = sd.getNumber('center', -1)
            widthFrame = sd.getNumber('widthFrame', -1)
            if abs(widthFrame / 2 - center) == 20:
                #Centered! close the session
                sd.putString('VisionState', "done")

        elif visionState == "none":
            print("Error getting state from network tables")
            print("git test")
    
    

main()
