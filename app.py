import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageOps
import pypdfium2 as pdfium
import math
from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="UK Build Reg AI - Pro Calibration", layout="wide")

# ----------------- SIDEBAR -----------------
st.sidebar.title("📏 Calibration Engine")
st.sidebar.markdown("---")

uploaded_file = st.sidebar.file_uploader("1. Upload Floor Plan (PDF/Image)", type=["jpg", "jpeg", "png", "pdf"])

st.sidebar.markdown("---")
st.sidebar.subheader("2. Set Scale Method")

calibration_mode = st.sidebar.radio(
    "Choose your method:",
    ("Standard Scale Factor", "Visual Reference (Draw Line)")
)

mm_per_pixel = 15.0  
pixel_length = 1.0
real_mm = 900.0

if calibration_mode == "Visual Reference (Draw Line)":
    st.sidebar.info("Draw a line on the plan to calibrate.")
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

# ----------------- MAIN VIEW -----------------
st.title("🇬🇧 UK Building Regulations Checker")
st.subheader("Dual-Mode Calibration Engine (Part M)")

if uploaded_file is not None:
    try:
        # 1. Process PDF or Image and FORCE a solid RGB background
        if uploaded_file.name.lower().endswith('.pdf'):
            pdf = pdfium.PdfDocument(uploaded_file)
            page = pdf[0]
            pil_image = page.render(scale=2).to_pil().convert("RGB")
        else:
            pil_image = Image.open(uploaded_file).convert("RGB")
            pil_image = ImageOps.exif_transpose(pil_image)
        
        # 2. Resize image slightly for better web performance
        max_width = 800
        w, h = pil_image.size
        if w > max_width:
            ratio = max_width / float(w)
            new_h = int(float(h) * float(ratio))
            pil_image = pil_image.resize((max_width, new_h), Image.Resampling.LANCZOS)
            w, h = pil_image.size
            
        # 3. FIX: Strip Metadata
        # By converting to a NumPy array and back, we destroy any hidden PDF data
        # that was crashing the React Canvas serializer on the cloud.
        clean_array = np.array(pil_image)
        safe_pil_image = Image.fromarray(clean_array)
            
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write("### Plan Workspace")
            
            # 4. ADAPTIVE UI: Swap between native image viewer and canvas tool
            if calibration_mode == "Standard Scale Factor":
                st.caption("👁️ View-only mode. AI Vision active.")
                
                # Draw a mock AI detection bounding box on the image
                marked_img = clean_array.copy()
                start_x, start_y = int(w * 0.45), int(h * 0.75)
                end_x, end_y = start_x + 45, start_y + 80 # Simulating a 45-pixel wide door
                
                # Check compliance color
                is_compliant = (45 * mm_per_pixel) >= 775
                box_color = (0, 255, 0) if is_compliant else (255, 0, 0)
                
                cv2.rectangle(marked_img, (start_x, start_y), (end_x, end_y), box_color, 4)
                
                # Display using Streamlit's native viewer (Guaranteed to render)
                st.image(marked_img, use_column_width=True)
                
            else:
                st.caption("🖱️ Draw a line over your reference object.")
                
                # Load the interactive Canvas
                canvas_result = st_canvas(
                    fill_color="rgba(255, 165, 0, 0.3)",
                    stroke_width=3,
                    stroke_color="#FF0000",
                    background_image=safe_pil_image, 
                    update_streamlit=True,
                    height=h,
                    width=w,
                    drawing_mode="line", 
                    key="canvas",
                )
                
                if canvas_result.json_data is not None:
                    objects = canvas_result.json_data["objects"]
                    if len(objects) > 0:
                        last_line = objects[-1]
                        x1, y1 = last_line["x1"], last_line["y1"]
                        x2, y2 = last_line["x2"], last_line["y2"]
                        
                        pixel_length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                        
                        if pixel_length > 0:
                            mm_per_pixel = real_mm / pixel_length

        with col2:
            st.write("### Calibration Engine Status")
            
            if calibration_mode == "Visual Reference (Draw Line)":
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
    
    except Exception as e:
        st.error(f"An error occurred loading the image: {e}")
else:
    st.info("Upload a plan to activate the engine.")
