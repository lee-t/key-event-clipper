# USAGE
# python save_key_events.py --output output

# import the necessary packages
from vidwriter.keyclipwriter import KeyClipWriter
from imutils.video import VideoStream
import argparse
import datetime
import imutils
import time
import cv2
import datetime

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-o", "--output", required=True,
    help="path to output directory")
ap.add_argument("-c", "--codec", type=str, default="MJPG",
    help="codec of output video")
ap.add_argument("-s", "--buffer-size", type=int, default=32,
    help="buffer size of video clip writer")
ap.add_argument("-v", "--video", 
    help="path to the video file")
ap.add_argument("-a", "--min-area", type=int, default=500, 
    help="minimum area size")
ap.add_argument('-b','--blur',type=int, 
    help='adjust blurring of edges. Default is 25', default=25, metavar='')
args = vars(ap.parse_args())

# initialize the video stream and allow the camera sensor to
# warmup

# initialize key clip writer and the consecutive number of
# frames that have *not* contained any action
kcw = KeyClipWriter(bufSize=args["buffer_size"])
consecFrames = 0
blursize=args["blur"]
vs = cv2.VideoCapture(args["video"])

# initialize the first frame in the video stream
firstFrame = None
currentsurface = 0
# keep looping if video is going
while (vs.isOpened()):
    # grab the current frame and initialize the occupied/unoccupied
    # text
    f_width = vs.get(cv2.CAP_PROP_FRAME_WIDTH)
    f_height = vs.get(cv2.CAP_PROP_FRAME_WIDTH)
    surface = f_width * f_height
    frame = vs.read()
    frame = frame if args.get("video", None) is None else frame[1]
    text = "Unoccupied"
    updateConsecFrames = True
    times=vs.get(cv2.CAP_PROP_POS_MSEC)
    timestamp = datetime.datetime.utcfromtimestamp(times//1000.0)
    currentsurface =0

    # if the frame could not be grabbed, then we have reached the end
    # of the video
    if frame is None:
        break

    #  convert frame to grayscale, and blur with "blursize"
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (blursize, blursize), 0)

    # if the first frame is None, initialize it
    if firstFrame is None:
        firstFrame = gray
        continue

    # compute the absolute difference between the current frame and
    # first frame
    frameDelta = cv2.absdiff(firstFrame, gray)
    thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]

    # dilate the thresholded image to fill in holes, then find contours
    # on thresholded image
    thresh = cv2.dilate(thresh, None, iterations=2)
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if imutils.is_cv2() else cnts[1]
    #DEBUG count countours
    count = len(cnts)
    print (str(count)+" / "+ str(timestamp.strftime("%H:%M:%S")))
    # loop ov(er the contours
    for c in cnts:
        # compute the area for each contour and increment surface
        currentsurface += cv2.contourArea(c)


        # compute the bounding box for the contour, draw it on the frame,
        # and update the text
        (x, y, w, h) = cv2.boundingRect(c)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
    #backcontours = contours #Save contours
    #avg = (currentsurface*100)/surface #Calculate the average of contour area on the total size

    if count > 5:
        updateConsecFrames = False
        consecFrames = 0
        currentsurface =0
        if not kcw.recording:
            p = "{}/{}.avi".format(args["output"],args["video"] + 
            str(timestamp.strftime("%H:%M:%S")))
            kcw.start(p, cv2.VideoWriter_fourcc(*args["codec"]),30)

    # otherwise, no action has taken place in this frame, so
    # increment the number of consecutive frames that contain
    # no action
    if updateConsecFrames:
        consecFrames += 1
    # if we are recording and reached a threshold on consecutive
    # number of frames with no action, stop recording the clip
    if kcw.recording and consecFrames == args["buffer_size"]:
        kcw.finish()
    
    # show the frame
    cv2.imshow("Video Feed", frame)
    cv2.imshow("Thresh", thresh)
    cv2.imshow("Frame Delta", frameDelta)
    key = cv2.waitKey(1) & 0xFF

    # if the `q` key is pressed, break from the lop
    if key == ord("q"):
        break

# cleanup the camera and close any open windows
vs.stop() if args.get("video", None) is None else vs.release()
cv2.destroyAllWindows()

