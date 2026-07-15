import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageOps
import pypdfium2 as pdfium
import math
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="UK Build Reg AI - Pro Calibration", layout="wide")

# Initialize session state to remember where the user clicks
if "calib_points" not in st.session_state:
    st.session_state["calib_points"] = []

# ----------------- SIDEBAR -----------------
st.sidebar.title("📏 Calibration Engine")
st.sidebar.markdown("---")

uploaded_file = st.sidebar.file_uploader("1. Upload Floor Plan (PDF/Image)", type=["jpg", "jpeg", "png", "pdf"])

st.sidebar.markdown("---")
st.sidebar.subheader("2. Set Scale Method")

calibration_mode = st.sidebar.radio(
    "Choose your method:",
    ("Standard Scale Factor", "Visual Reference (Click 2 Points)")
)

mm_per_pixel = 15.0  
pixel_length = 1.0
real_mm = 900.0

if calibration_mode == "Visual Reference (Click 2 Points)":
    st.sidebar.info("Click two points on the plan to measure a known length.")
    unit_type = st.sidebar.selectbox("Unit:", ("Millimeters (mm)", "Meters (m)", "Inches (in)", "Feet (ft)"))
    raw_value = st.sidebar.number_input("Known Length:", min_value=0.1, value=900.0, step=10.0)
    
    if unit_type == "Meters (m)": real_mm = raw_value * 1000
    elif unit_type == "Inches (in)": real_mm = raw_value * 25.4
    elif unit_type == "Feet (ft)": real_mm = raw_value * 304.8
    else: real_mm = raw_value
        
else:
    st.sidebar.info("Apply a standard architectural scale.")
    scale_system = st.sidebar.selectbox("System:", ("Metric (UK/EU)", "Imperial (US)"))
    
    if scale_system == "Metric (UK/EU)":
        metric_scale = st.sidebar.selectbox("Scale:", ("1:50", "1:100", "1:200"))
        if metric_scale == "1:50": mm_per_pixel = 10.0
        elif metric_scale == "1:100": mm_per_pixel = 20.0
        else: mm_per_pixel = 40.0
    else:
        imperial_scale = st.sidebar.selectbox("Scale:", ("1/4\" = 1'-0\"", "1/8\" = 1'-0\"", "3/16\" = 1'-0\""))
        if imperial_scale == "1/4\" = 1'-0\"": mm_per_pixel = 12.7
        elif imperial_scale == "1/8\" = 1'-0\"": mm_per_pixel = 25.4
        else: mm_per_pixel = 16.9
        
    # Clear clicks if they switch back to standard mode
    st.session_state["calib_points"] = []

# ----------------- MAIN VIEW -----------------
st.title("🇬🇧 UK Building Regulations Checker")
st.subheader("Dual-Mode Calibration Engine (Part M)")

if uploaded_file is not None:
    try:
        # Load PDF or Image
        if uploaded_file.name.lower().endswith('.pdf'):
            pdf = pdfium.PdfDocument(uploaded_file)
            page = pdf[0]
            pil_image = page.render(scale=2).to_pil().convert("RGB")
        else:
            pil_image = Image.open(uploaded_file).convert("RGB")
            pil_image = ImageOps.exif_transpose(pil_image)
        
        # Resize for web performance
        max_width = 800
        w, h = pil_image.size
        if w > max_width:
            ratio = max_width / float(w)
            new_h = int(float(h) * float(ratio))
            pil_image = pil_image.resize((max_width, new_h), Image.Resampling.LANCZOS)
            w, h = pil_image.size
            
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write("### Plan Workspace")
            
            if calibration_mode == "Standard Scale Factor":
                st.caption("👁️ View-only mode. AI Vision Mockup active.")
                
                # Mock AI Box
                marked_img = np.array(pil_image).copy()
                start_x, start_y = int(w * 0.45), int(h * 0.75)
                end_x, end_y = start_x + 45, start_y + 80 
                
                is_compliant = (45 * mm_per_pixel) >= 775
                box_color = (0, 255, 0) if is_compliant else (255, 0, 0)
                
                cv2.rectangle(marked_img, (start_x, start_y), (end_x, end_y), box_color, 4)
                
                # Add text to clearly show it is a placeholder
                cv2.putText(marked_img, "MOCK AI DETECTION", (start_x - 50, start_y - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)
                
                st.image(marked_img, use_column_width=True)
                
            else:
                st.caption("🖱️ Click Point A, then click Point B to calibrate.")
                
                # Use the stable coordinate clicker instead of the canvas
                click_data = streamlit_image_coordinates(pil_image, key="pil")
                
                # Logic to track exactly 2 clicks
                if click_data is not None:
                    point = (click_data["x"], click_data["y"])
                    
                    # Prevent registering the exact same click twice in a row
                    if not st.session_state["calib_points"] or st.session_state["calib_points"][-1] != point:
                        st.session_state["calib_points"].append(point)
                        
                        # If they click a 3rd time, reset and start a new line
                        if len(st.session_state["calib_points"]) > 2:
                            st.session_state["calib_points"] = [point]

                # If 2 points are clicked, calculate the math
                if len(st.session_state["calib_points"]) == 2:
                    p1 = st.session_state["calib_points"][0]
                    p2 = st.session_state["calib_points"][1]
                    pixel_length = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
                    
                    if pixel_length > 0:
                        mm_per_pixel = real_mm / pixel_length

        with col2:
            st.write("### Calibration Engine Status")
            
            if calibration_mode == "Visual Reference (Click 2 Points)":
                if len(st.session_state["calib_points"]) == 0:
                    st.warning("Awaiting Click 1 (Point A)...")
                elif len(st.session_state["calib_points"]) == 1:
                    st.warning("Awaiting Click 2 (Point B)...")
                else:
                    st.success("Target Locked: Visual Calibration")
                    st.metric(label="Reference Length (Pixels)", value=f"{round(pixel_length, 1)} px")
                    st.metric(label="Assigned Size", value=f"{real_mm} mm")
            else:
                st.info("Target Locked: Standard Scale")
                
            st.write("---")
            st.write("### System Scale Multiplier")
            st.info(f"**1 Pixel = {round(mm_per_pixel, 2)} mm**")
            
            st.write("---")
            st.write("### AI Part M Compliance Check")
            
            detected_door_pixels = 45 
            real_world_width = round(detected_door_pixels * mm_per_pixel, 1)
            
            st.write("AI detected a main entrance door opening measuring **45 pixels**.")
            st.metric(label="Calculated Physical Width", value=f"{real_world_width} mm")
            
            if real_world_width >= 775:
                st.success("✅ COMPLIANT: Minimum 775mm met.")
            else:
                st.error(f"🚨 FAILED: Opening is {round(775 - real_world_width, 1)}mm too narrow.")
                
            st.caption("*Note: The bounding box on the plan is currently a UI placeholder. Real bounding box mapping requires integration of the YOLOv8 model file.*")
    
    except Exception as e:
        st.error(f"An error occurred loading the image: {e}")
else:
    st.info("Upload a plan to activate the engine.")
