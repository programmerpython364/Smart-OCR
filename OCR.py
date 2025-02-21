import easyocr
import numpy as np
from PIL import Image
import cv2


def ImageOCR(img):
    OCRModel_path = "model"
    
    reader = easyocr.Reader(["en","ar"],model_storage_directory=OCRModel_path)
    
    if isinstance(img, np.ndarray):  
        image = img
        results = reader.readtext(image,detail=1)
    else:        

        image = Image.open(img)            
        results = reader.readtext(np.array(image),detail=1)
    
    return results

def VideoOCR(video):
    OCR_for_frames = [] 
            
    cap = cv2.VideoCapture(video)
    
    while cap.isOpened():
        ret, frame = cap.read()
        
        if not ret:
            break
        OCR_frame = ImageOCR(frame)
        OCR_for_frames.append(OCR_frame)
        
    cap.release()

    
    return OCR_for_frames

        
        
    
    