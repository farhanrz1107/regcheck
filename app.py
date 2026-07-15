import streamlit as st
import cv2
import numpy as np
from PIL import Image
import pypdfium2 as pdfium
import math
from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="UK Build Reg AI - Interactive Calibration", layout="wide")

# ----------------- SIDEBAR -----------------
st.sidebar.title("📏 Scale & Calibration")
st.sidebar.write("Calibrate by drawing a line on the plan.")
st.sidebar.markdown("---")

uploaded_file = st.sidebar.file_uploader("1. Upload Floor Plan", type=["jpg", "jpeg", "png", "pdf"])

st.sidebar.markdown("---")
st.sidebar.subheader("2. Define Reference Object")
st.sidebar.info("Tell the app the real-world size of the object you are about to draw a line over.")

unit_type = st.sidebar.selectbox("Reference Unit:", ("Millimeters (mm)", "Meters (m)", "Inches (in)", "Feet (ft)"))
raw_value = st.sidebar.number_input("Real-World Length:", min_value=0.1, value=900.0, step=10.0)

# Convert user input to mm for the engine
if unit_type == "Meters (m)":
    real_mm = raw_value * 1000
elif unit_type == "Inches (in)":
    real_mm = raw_value * 25.4
elif unit_type == "Feet (ft)":
    real_mm = raw_value * 304.8
else:
    real_mm = raw_value

st.sidebar.markdown("---")
st.sidebar.subheader("3. Draw to Calibrate")
st.sidebar.write("Use your mouse to draw a straight line over your reference object on the plan to the right.")

# Default fallback scale if the user hasn't drawn anything yet
pixel_length = 1.0 
mm_per_pixel = 15.0  

# ----------------- MAIN VIEW -----------------
st.title("🇬🇧 UK Building Regulations Checker")
st.subheader("Interactive Visual Calibration Engine")

if uploaded_file is not None:
    # Handle PDF or Image
    if uploaded_file.name.lower().endswith('.pdf'):
        pdf = pdfium.PdfDocument(uploaded_file)
        page = pdf[0]
        pil_image = page.render(scale=2).to_pil()
    else:
        pil_image = Image.open(uploaded_file)
        
    img_array = np.array(pil_image)
    if img_array.shape[-1] == 4:
        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
    
    h, w, _ = img_array.shape
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("### Interactive Plan Viewer")
        st.caption("Click and drag to draw a line over your known reference object.")
        
        # Create the interactive canvas over the uploaded image
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
            stroke_width=3,
            stroke_color="#FF0000",
            background_image=pil_image,
            update_streamlit=True,
            height=h,
            width=w,
            drawing_mode="line", # Forces the user to draw a straight measuring line
            key="canvas",
        )
        
        # If the user draws a line, calculate its length in pixels using the Pythagorean theorem
        if canvas_result.json_data is not None:
            objects = canvas_result.json_data["objects"]
            if len(objects) > 0:
                # Get the last line drawn by the user
                last_line = objects[-1]
                x1, y1 = last_line["x1"], last_line["y1"]
                x2, y2 = last_line["x2"], last_line["y2"]
                
                # Calculate pixel distance
                pixel_length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                
                # Prevent division by zero
                if pixel_length > 0:
                    mm_per_pixel = real_mm / pixel_length

    with col2:
        st.write("### Active Calibration Data")
        
        if canvas_result.json_data and len(canvas_result.json_data["objects"]) > 0:
            st.success("Reference line detected!")
            st.metric(label="Drawn Line Length (Pixels)", value=f"{round(pixel_length, 1)} px")
            st.metric(label="Assigned Real-World Length", value=f"{real_mm} mm")
            st.write("---")
            st.write("### System Scale Factor")
            st.info(f"**1 Pixel = {round(mm_per_pixel, 2)} mm**")
            
            st.write("---")
            st.write("### Simulated AI Check (Part M)")
            
            # Simulate the AI detecting a 45-pixel door using the NEW scale
            detected_door_pixels = 45 
            real_world_width = round(detected_door_pixels * mm_per_pixel, 1)
            
            st.write(f"The AI detected a door opening that is **45 pixels** wide on this drawing.")
            st.metric(label="Calculated Real Opening", value=f"{real_world_width} mm")
            
            if real_world_width >= 775:
                st.success("✅ PASSED: Minimum 775mm met.")
            else:
                st.error(f"🚨 FAILED: Door is {round(775 - real_world_width, 1)}mm too narrow.")
        else:
            st.warning("Awaiting calibration... Please draw a line on the plan.")

else:
    st.info("Upload a plan to begin.")
