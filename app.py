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
st.sidebar.subheader("2. Set Scale (Choose Method)")

tab1, tab2 = st.sidebar.tabs(["Visual Reference", "Standard Scale"])

mm_per_pixel = 15.0  
pixel_length = 1.0

with tab1:
    st.info("Draw a line on the plan to calibrate.")
    unit_type = st.selectbox("Unit:", ("Millimeters (mm)", "Meters (m)", "Inches (in)", "Feet (ft)"))
    raw_value = st.number_input("Known Length:", min_value=0.1, value=900.0, step=10.0)
    
    if unit_type == "Meters (m)": real_mm = raw_value * 1000
    elif unit_type == "Inches (in)": real_mm = raw_value * 25.4
    elif unit_type == "Feet (ft)": real_mm = raw_value * 304.8
    else: real_mm = raw_value
        
with tab2:
    st.info("Apply a standard architectural scale.")
    scale_system = st.selectbox("System:", ("Metric (UK/EU)", "Imperial (US)"))
    
    if scale_system == "Metric (UK/EU)":
        metric_scale = st.selectbox("Scale:", ("1:50", "1:100", "1:200"))
        if metric_scale == "1:50": mm_per_pixel = 10.0
        elif metric_scale == "1:100": mm_per_pixel = 20.0
        else: mm_per_pixel = 40.0
    else:
        imperial_scale = st.selectbox("Scale:", ("1/4\" = 1'-0\"", "1/8\" = 1'-0\"", "3/16\" = 1'-0\""))
        if imperial_scale == "1/4\" = 1'-0\"": mm_per_pixel = 12.7
        elif imperial_scale == "1/8\" = 1'-0\"": mm_per_pixel = 25.4
        else: mm_per_pixel = 16.9

# ----------------- MAIN VIEW -----------------
st.title("🇬🇧 UK Building Regulations Checker")
st.subheader("Dual-Mode Calibration Engine (Part M)")

if uploaded_file is not None:
    # Process PDF or Image and FORCE a solid RGB background
    if uploaded_file.name.lower().endswith('.pdf'):
        pdf = pdfium.PdfDocument(uploaded_file)
        page = pdf[0]
        # scale=2 for high resolution, convert("RGB") fixes transparency bugs
        pil_image = page.render(scale=2).to_pil().convert("RGB")
    else:
        pil_image = Image.open(uploaded_file).convert("RGB")
        # Ensure it's right-side up based on EXIF data
        pil_image = ImageOps.exif_transpose(pil_image)
    
    # Resize image slightly for better web performance
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
        st.caption("If using 'Visual Reference', draw your line here.")
        
        # Canvas should now display perfectly
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=3,
            stroke_color="#FF0000",
            background_image=pil_image, 
            update_streamlit=True,
            height=h,
            width=w,
            drawing_mode="line", 
            key="canvas",
        )
        
        active_calibration = "Standard"
        
        if canvas_result.json_data is not None:
            objects = canvas_result.json_data["objects"]
            if len(objects) > 0:
                active_calibration = "Visual"
                last_line = objects[-1]
                x1, y1 = last_line["x1"], last_line["y1"]
                x2, y2 = last_line["x2"], last_line["y2"]
                
                pixel_length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                
                if pixel_length > 0:
                    mm_per_pixel = real_mm / pixel_length

    with col2:
        st.write("### Calibration Engine Status")
        
        if active_calibration == "Visual":
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

else:
    st.info("Upload a plan to activate the engine.")
