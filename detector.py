from ultralytics import YOLO

print("Loading YOLO model...")
#load the model
detector = YOLO("croed_ofc_head_det.pt") 
#Inform user that the model is loaded
print("Model loaded")