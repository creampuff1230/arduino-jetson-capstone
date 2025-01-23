from ultralytics import YOLO
import cv2
import time

# Load the trained model
model = YOLO('/home/rat/Desktop/cv/runs/runs/detect/maze_navigation_model2/weights/best.pt')

# Function to process YOLO results and output [color_code, position]
def process_results(results, img_width):
    output_vectors = []
    tol_x = 2 
    color_xs = []
    color_ys = []
    print(img_width)

    color_map = {
        'red': 0,
        'green': 1,
        'blue': 2,
    }

    for box in results[0].boxes:  # Access detected boxes
        cls = int(box.cls[0])  # Class ID
        x_center = box.xywh[0][0].item()  # Center x-coordinate of the bounding box
        y_center = box.xywh[0][1].item()  # Center y-coordinate of the bounding box
        color_xs.append(x_center)
        color_ys.append(y_center)
        print(x_center)
        
        color_name = results[0].names[cls]  # Map class ID to color name
        color_code = color_map.get(color_name, 3)  # Function to map color name to code
        position = 1  # Default position is forward (1)

        # Logic to determine position based on bounding box coordinates
    if len(color_xs) == 2:
        print((color_ys[0])/img_width - (color_ys[2])/img_width)
        if (color_xs[0])/img_width - (color_xs[1])/img_width > 0.15:
            output_vectors[0][3] = 0
            output_vectors[1][3] = 2
        else:
            if color_ys[0] > color_ys[1]:
                output_vectors[0][3] = 1
                output_vectors[1][3] = 2
            else:
                output_vectors[0][3] = 0
                output_vectors[1][3] = 1

    else:
        output_vectors[0][3] = 0
        output_vectors[1][3] = 1
        output_vectors[2][3] = 2

        # Append [color_code, position] to output
    output_vectors.append([color_code, position])

    return output_vectors

# Initialize the camera
camera = cv2.VideoCapture(0)  # Change to your camera index if needed

# Check if the camera is ready
start_time = time.time()
timeout = 10  # 10 seconds timeout for the camera to initialize
while not camera.isOpened():
    if time.time() - start_time > timeout:
        raise RuntimeError("Camera failed to initialize within the timeout period.")
    print("Waiting for camera to initialize...")
    time.sleep(0.5)

print("Camera is ready!")

# Read a frame from the camera
ret, img = camera.read()
if not ret:
    raise RuntimeError("Failed to read from the camera.")

# Perform inference with YOLO
img_height, img_width, _ = img.shape
results = model(img)

new_start_time = time.time()
timeout = 10
while ((len(results[0].boxes) < 2) and ((time.time() - new_start_time) < timeout)):
    ret, img = camera.read()

# Process results to get [color_code, position] vectors
vectors = process_results(results, img_width)

# Print output vectors
print("Output Vectors:", vectors)

# Release the camera
camera.release()
