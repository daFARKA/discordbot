import cv2
import pytesseract
import numpy as np
from PIL import Image
import re

import calendar_tool

pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'  # your path may be different^

bilplan_global = []
times_global = []
inlets_control_global = 0


def find_template_occurrences(image_path, template_path, threshold):
    img = cv2.imread(image_path)
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    w, h = template.shape[::-1]

    res = cv2.matchTemplate(gray_img, template, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res >= threshold)

    # Apply non-maximum suppression to get only one bounding box for each match
    matches = []
    for pt in zip(*loc[::-1]):
        match_rect = [pt[0], pt[1], pt[0] + w, pt[1] + h]
        overlap = False
        for m in matches:
            if intersect(match_rect, m):
                overlap = True
                break
        if not overlap:
            matches.append(match_rect)
    
    for match in matches:
        cv2.rectangle(img, (match[0], match[1]), (match[2], match[3]), (0, 255, 0), 2)

    
    resized_img = cv2.resize(img, (1920, 1080))
    cv2.imshow('Matches', resized_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    
    return matches


# Checks if two rectangles intersect
def intersect(rect1, rect2):
    return not (rect1[2] < rect2[0] or rect1[0] > rect2[2] or rect1[3] < rect2[1] or rect1[1] > rect2[3])


def splice_image_into_cinemas(image_path, offset):
    match1 = find_template_occurrences(image_path, 'testimages/1-template-scan.jpg', 0.85)
    match8 = find_template_occurrences(image_path, 'testimages/8-template-scan.jpg', 0.85)   

    img_pil = Image.open(image_path)
    #box = (x0, y0, x1, y1)
    box = (match1[0][0], match1[0][1], match8[0][0]-offset, match8[0][1])
    cinema1 = img_pil.crop(box)
    cinema1.save('slices/cinema1.jpg')

    cinema_template = cv2.imread('slices/cinema1.jpg', cv2.IMREAD_GRAYSCALE)
    # Cinemas 2-6
    w, h = cinema_template.shape[::-1]
    for cinema_nr in range(2,7):
        w = w * (cinema_nr - 1)
        h = h * (cinema_nr - 1)
        box = (match1[0][0], match1[0][1] + h, match8[0][0]-offset, match8[0][1] + h)
        cinema_img = img_pil.crop(box)
        cinema_img.save('slices/cinema' + str(cinema_nr) + '.jpg')
        w, h = cinema_template.shape[::-1]

    # Cinemas 7-12
    w, h = cinema_template.shape[::-1]
    for cinema_nr in range(7,13):
        h = h * (cinema_nr - 7)
        box = (match1[0][0] + w + offset, match1[0][1] + h, match8[0][0] + w - offset, match8[0][1] + h)
        cinema_img = img_pil.crop(box)
        cinema_img.save('slices/cinema' + str(cinema_nr) + '.jpg')
        w, h = cinema_template.shape[::-1]

def extract_text_from_splice_using_pytesseract(splice_path):
    low_red = np.array([0, 0, 0])
    high_red = np.array([0, 255, 255])

    img = cv2.imread(splice_path)
    # convert BGR to HSV
    imgHSV = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # create the Mask
    mask = cv2.inRange(imgHSV, low_red, high_red)
    # inverse mask
    mask = 255-mask
    res = cv2.bitwise_and(img, img, mask=mask)

    img_text = pytesseract.image_to_string(img)
    mask_text = pytesseract.image_to_string(mask)
    res_text = pytesseract.image_to_string(res)

    norm = np.zeros((img.shape[0], img.shape[1]))
    norm_img = cv2.normalize(img, norm, 0, 255, cv2.NORM_MINMAX)

    rem_noise = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 15)

    # Add padding with the color of the top left pixel
    pad_color = img[0, 0, :]
    padded_img = np.full((img.shape[0]+10, img.shape[1]+10, 3), pad_color, np.uint8)
    padded_img[5:-5, 5:-5, :] = img

    cv2.floodFill(padded_img, None, (0, 0), (255, 100, 100), loDiff=(10, 10, 10), upDiff=(10, 10, 10))  # Fill the background with blue color.

    # Convert from BGR to HSV color space, and extract the saturation channel.
    hsv = cv2.cvtColor(padded_img, cv2.COLOR_BGR2HSV)
    s = hsv[:, :, 1]

    # Apply thresholding (use cv2.THRESH_OTSU for automatic thresholding)
    thresh = cv2.threshold(s, 0, 255, cv2.THRESH_OTSU)[1]

    norm_img_text = pytesseract.image_to_string(norm_img)
    rem_noise_text = pytesseract.image_to_string(rem_noise)
    thresh_text = pytesseract.image_to_string(thresh)

    img_texts = [img_text, mask_text, res_text, norm_img_text, rem_noise_text, thresh_text]

    extracted_text = img_text
    return extracted_text



def find_time_in_string(string, text, threshold):
    occurrences = []
    for match in re.finditer(text, string, flags=re.IGNORECASE):
        occurrences.append([match.start(), match.end()])

    if not occurrences:
        return('0')

    times = []
    substring = ""
    errors = 0
    for i in range(len(occurrences)):
        substring = string[occurrences[i][1]:occurrences[i][1]+threshold]
        time_pos = substring.find(':')
        if (time_pos == -1):
            errors += 1
            times.append('-1')
        else:
            time = substring[time_pos-2:time_pos] + substring[time_pos+1:time_pos+3]
            print(time)
            # If it is not a time I would expect, throw it out and write -1 and error++
            if (time[3] != '0' and time[3] != '5'):
                errors += 1
                times.append('-1')
            else:
                times.append(time)
                times_global.append(time)

    print("Errors: " + str(errors))
    return (times)


def sort_bilplan(bilplan):
    print("Times before sorting.")
    print(times_global)
    times_global.sort()
    print("Times after sorting.")
    print(times_global)

    prev_time = ""
    for time in times_global:
        if prev_time == time:
            continue
        # cinema_info[0] are the inlets of this cinema
        # cinema_info[1] is the number of the cinema
        for cinema_info in bilplan:
            for inlet in cinema_info[0]:
                if inlet == time:
                    bilplan_global.append([time, cinema_info[1]])

        prev_time = time  

    print("Adding misses and error info to the bilplan.")
    add_misses(bilplan)
    error_offset = inlets_control_global - len(bilplan_global)
    bilplan_global.append(["fatal_errors", error_offset])


def add_misses(bilplan):
    for cinema_info in bilplan:
        for inlet in cinema_info[0]:
            if inlet == '-1':
                bilplan_global.append(["missing", cinema_info[1]])


def create_calendar_events():
    calendar_tool.clear_calendar()
    for cinema_info in bilplan_global:
        time = cinema_info[0]
        cinema_nr = cinema_info[1]
        if time == 'missing':
            return
        else:
            calendar_tool.create_event_today("Einlass", cinema_nr, time)


'''
    Convert the image into 12 slices so the program knows which cinema is which. 
    In total 12 cinema_nr.jpg are being created and saved into slices
    Then run find_template_occurrences on every cinema slice to find out if I have this cinema.
    Add the number of occurrences (matches) to inlets_control, so it can be used later if some time cannot be read.
    Then extract the text from slice.
    From this text extract the position of Farka and the time.
    The result is an array where -1 represents an error, normal time the found time (which could also be false) and the # of errors.
    Add the result to a temporary bilplan to sort it.
    After sorting the temporary bilplan match the times to the cinema and build bilplan_global.
'''
def analyze_bilplan(image_path):
    #image_path = 'testimages/test1.jpg'
    template_path = 'testimages/Farka-template-scan.jpg'
    #find_template_occurrences(image_path, template_path, 0.75)
    print("Splicing the image into 12 jpgs.")
    splice_image_into_cinemas(image_path, 0)

    bilplan = []
    global inlets_control_global
    for i in range(1,13):
        print("Find template in cinema " + str(i))
        occurrences_control = find_template_occurrences('slices/cinema' + str(i) + '.jpg', template_path, 0.75)
        inlets_control_global += len(occurrences_control)
        print("Extract text from cinema " + str(i))
        extracted_text = extract_text_from_splice_using_pytesseract('slices/cinema' + str(i) + '.jpg')
        print("Extracted Text:")
        print(extracted_text)
        print("Finding the time in the string in cinema " + str(i))
        times_result = find_time_in_string(extracted_text, "farka", 10)
        print(times_result)
        bilplan.append([times_result, i])

    print("Temporary bilplan:")
    print(bilplan)

    print("Sorting bilplan...")
    sort_bilplan(bilplan);

    print("Inlets this day according to template matching: " + str(inlets_control_global))
    print("Inlets missed because of errors: " + str(inlets_control_global - len(bilplan_global)))

    print("Resulting bilplan:")
    print(bilplan_global)

    print("Creating calender events.")
    create_calendar_events()
    return bilplan_global


#find_template_occurrences('testimages/test1.jpg', 'testimages/Farka-template-scan.jpg', 0.75)
#analyze_bilplan('testimages/test1.jpg')