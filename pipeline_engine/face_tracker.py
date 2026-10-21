import cv2
import numpy as np
import mediapipe as mp

def render_cinematic_crop(input_video, output_temp_video):
    print("--- Initializing Cinematic Cropper (Dynamic Blur Fallback) ---")
    mp_face_mesh = mp.solutions.face_mesh
    
    cap = cv2.VideoCapture(input_video)
    if not cap.isOpened():
        print("Error: Could not open source video.")
        return

    orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    if fps <= 0 or np.isnan(fps): fps = 30.0
    if orig_w <= 0 or orig_h <= 0: orig_w, orig_h = 1920, 1080
    
    # Calculate target 9:16 dimensions
    target_w = int(orig_h * (9 / 16))
    if target_w % 2 != 0: target_w += 1 
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_temp_video, fourcc, fps, (target_w, orig_h))

    TOP_LIP, BOTTOM_LIP = 13, 14
    FRAME_WINDOW = 15
    TALKING_THRESHOLD = 0.004
    CUT_DELAY_FRAMES = 8
    CAMERA_SPEED = 0.15 
    
    history_left, history_right = [], []
    
    current_camera_x = orig_w // 2 
    target_camera_x = orig_w // 2
    left_speech_counter, right_speech_counter = 0, 0
    has_locked_initial_target = False 

    print("Analyzing frames and rendering vertical tracks... Please wait.")

    with mp_face_mesh.FaceMesh(max_num_faces=2, refine_landmarks=True, min_detection_confidence=0.5) as face_mesh:
        while cap.isOpened():
            success, frame = cap.read()
            if not success or frame is None: break
            
            try:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = face_mesh.process(rgb_frame)
                
                var_left, var_right = 0, 0
                pos_left_x, pos_right_x = None, None
                
                # --- SCENARIO 1: FACE(S) DETECTED -> FULLSCREEN CROPPED SHOT ---
                if results.multi_face_landmarks and len(results.multi_face_landmarks) > 0:
                    sorted_faces = sorted(results.multi_face_landmarks, key=lambda f: f.landmark[1].x)
                    
                    for i, face_landmarks in enumerate(sorted_faces):
                        if i > 1: break
                        
                        top_pt = face_landmarks.landmark[TOP_LIP]
                        bot_pt = face_landmarks.landmark[BOTTOM_LIP]
                        lip_dist = np.abs(top_pt.y - bot_pt.y)
                        nose_x = int(face_landmarks.landmark[1].x * orig_w)
                        
                        if i == 0: 
                            pos_left_x = nose_x
                            history_left.append(lip_dist)
                            if len(history_left) > FRAME_WINDOW: history_left.pop(0)
                            if len(history_left) >= FRAME_WINDOW: var_left = np.std(history_left)
                        elif i == 1: 
                            pos_right_x = nose_x
                            history_right.append(lip_dist)
                            if len(history_right) > FRAME_WINDOW: history_right.pop(0)
                            if len(history_right) >= FRAME_WINDOW: var_right = np.std(history_right)

                    # First Frame Lock
                    if not has_locked_initial_target:
                        if pos_left_x is not None:
                            current_camera_x = pos_left_x
                            target_camera_x = pos_left_x
                            has_locked_initial_target = True

                    # Active Speaker Selection
                    if var_left > var_right and var_left > TALKING_THRESHOLD:
                        left_speech_counter += 1
                        right_speech_counter = 0
                    elif var_right > var_left and var_right > TALKING_THRESHOLD:
                        right_speech_counter += 1
                        left_speech_counter = 0
                    else:
                        if left_speech_counter > 0: left_speech_counter -= 1
                        if right_speech_counter > 0: right_speech_counter -= 1

                    if left_speech_counter >= CUT_DELAY_FRAMES and pos_left_x is not None:
                        target_camera_x = pos_left_x  
                    elif right_speech_counter >= CUT_DELAY_FRAMES and pos_right_x is not None:
                        target_camera_x = pos_right_x  
                        
                    # Smooth Camera Move
                    current_camera_x += int((target_camera_x - current_camera_x) * CAMERA_SPEED)
                    crop_x = current_camera_x - (target_w // 2)
                    
                    # Boundary protection
                    if crop_x < 0: crop_x = 0
                    elif (crop_x + target_w) > orig_w: crop_x = max(0, orig_w - target_w)
                    
                    cropped_frame = frame[0:orig_h, crop_x:crop_x + target_w]
                    final_frame = cv2.resize(cropped_frame, (target_w, orig_h))
                    out.write(final_frame)

                # --- SCENARIO 2: NO FACE DETECTED -> CENTERED VIDEO WITH BLURRED TOP/BOTTOM ---
                else:
                    # 1. Create a heavily blurred background filling the 9:16 target canvas
                    bg_blurred = cv2.resize(frame, (target_w, orig_h))
                    bg_blurred = cv2.GaussianBlur(bg_blurred, (99, 99), 0)
                    
                    # 2. Scale the original 16:9 video down to fit the target width
                    scaled_h = int(target_w * (orig_h / orig_w))
                    scaled_video = cv2.resize(frame, (target_w, scaled_h))
                    
                    # 3. Calculate vertical center position
                    y_offset = (orig_h - scaled_h) // 2
                    
                    # 4. Overlay the crisp video in the middle of the blurred canvas
                    bg_blurred[y_offset:y_offset + scaled_h, 0:target_w] = scaled_video
                    
                    out.write(bg_blurred)
                    
            except Exception as e:
                print(f"Skipped frame rendering error: {e}")
                continue
            
    cap.release()
    out.release()