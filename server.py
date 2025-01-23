import socket
from ultralytics import YOLO
import cv2
import time
from PIL import Image


model = YOLO('/home/rat/Desktop/master/mazeJunction.pt')
MAIN_COLOR = -1
MAIN_COLOR_DECIDER = []

# --- Utility Functions ---
def get_dominant_color(pil_img):
    # makes pixel 1 pixel lol
    # then gets color
    img = pil_img.copy()
    img = img.convert("RGBA")
    img = img.resize((1,1), resample=0)
    dom_color = img.getpixel((0,0))
    return dom_color

def classify_color(color, tolerance=50):
    """
    Classifies a color into 0 (red), 1 (green), 2 (blue), or 3 (other).

    Parameters:
        color (tuple): RGB or RGBA tuple (e.g., (255, 0, 0) or (255, 0, 0, 255)).
        tolerance (int): Tolerance value for mixed colors (default 50).

    Returns:
        int: 0 for red, 1 for green, 2 for blue, 3 for other.
    """
    # Extract RGB values, ignore Alpha val
    r, g, b = color[:3]

    # Check for red, green, or blue dominance
    if r > g + tolerance and r > b + tolerance:
        return 0  # Red
    elif g > r + tolerance and g > b + tolerance:
        return 1  # Green
    elif b > r + tolerance and b > g + tolerance:
        return 2  # Blue
    else:
        return 3  # Other (e.g., yellow, purple, etc.)

def process_junction_results(results, img_width):
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


def decode_packet(packet):
    """Decode incoming packet into a message type and data."""
    try:
        parts = packet.decode().strip().split(":")
        message = parts[0]
        data = int(parts[1]) if len(parts) > 1 else None
        return message, data
    except Exception as e:
        print(f"Failed to decode packet: {e}")
        return None, None

def encode_packet(message, data):
    """Encode message and optional data into a packet."""
    if data is not None:
        return f"{message}:{data}\n".encode()
    return f"{message}\n".encode()

# --- Processing Functions ---
def process_checkpoint_start():
    """Process checkpoint_start message."""
    print("Processing checkpoint_start")
    global MAIN_COLOR_DECIDER

    camera = cv2.VideoCapture(0)
    start_time = time.time()
    timeout = 10  # 10 seconds timeout for the camera to initialize
    while not camera.isOpened():
        if time.time() - start_time > timeout:
            raise RuntimeError("Camera failed to initialize within the timeout period.")
        print("Waiting for camera to initialize...")
        time.sleep(0.5)

    print("Camera is ready!")
    # Capture one frame
    ret, image = camera.read()

    if not ret:
        print("Failed to grab frame")
        camera.release()
        return
    
    dominant_color = classify_color(get_dominant_color(image))
    MAIN_COLOR_DECIDER.append(dominant_color)

    camera.release()
    data = dominant_color  # Example: calculate or fetch the appropriate response data
    return "checkpoint_end", data


######################################################################################
#### AUDIO
### todo
def process_audio_start():
    """Process audio_start message."""
    print("Processing audio_start")
    data = 0  
    return "audio_end", data



######################################################################################
#### MAZE JUNCTION
def process_maze_junction_start():
    """Process maze_junction_start message."""
    global MAIN_COLOR
    print("Processing maze_junction_start")
    

    if MAIN_COLOR != -1:
        MAIN_COLOR = max(set(MAIN_COLOR_DECIDER), key=MAIN_COLOR_DECIDER.count) if MAIN_COLOR_DECIDER else -1
        
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
    timeout = 15
    while ((len(results[0].boxes) < 2) and ((time.time() - new_start_time) < timeout)):
        ret, img = camera.read()
        results = model(img)

    # Process results to get [color_code, position] vectors
    vectors = process_junction_results(results, img_width)

    print("Output Vectors:", vectors)
    camera.release()

    # choose direction
    data = 1
    for vec in vectors:
        if vec[0] == MAIN_COLOR:
            data = vec[1]
    
    return "maze_junction_end", data

def process_message(message, data):
    """Process incoming message and determine the response."""
    if message == "checkpoint_start":
        return process_checkpoint_start()
    elif message == "audio_start":
        return process_audio_start()
    elif message == "maze_junction_start":
        return process_maze_junction_start()
    else:
        print(f"Unknown message received: {message}")
        return None, None

# --- Main Server Logic ---
def handle_client(client):
    """Handle communication with a connected client."""
    while True:
        # Receive data from the client
        content = client.recv(64)
        #if not content:
        if len(content) == 0:  # Connection closed
            break
        
        # Decode the received packet
        message, data = decode_packet(content)
        print(f"Received message: {message}, data: {data}")

        # Process the message and get the response
        response_message, response_data = process_message(message, data)
        print(f"response is: {response_message}, data: {response_data}")
        if response_message is not None:
            print("response message isnt none oh yeah... sending msg")
            # Send the response back to the client
            print(encode_packet(response_message, response_data))
            client.sendall(encode_packet(response_message, response_data))
            

    print("Closing connection")

    client.close()

def start_server():
    """Start the server and listen for incoming connections."""
    print("Creating server...")
    server_socket = socket.socket()
    server_socket.bind(('0.0.0.0', 10000))
    server_socket.listen(0)

    while True:
        client, addr = server_socket.accept()
        print(f"Connected to: {addr}")
        handle_client(client)

# --- Entry Point ---
if __name__ == "__main__":
    start_server()
