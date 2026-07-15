import streamlit as st
import cv2
import numpy as np
from PIL import Image

# 1. Setup the Page Configuration
st.set_page_config(page_title="UK Build Reg AI - Part M Checker", layout="wide")

# 2. Sidebar Interface
st.sidebar.title("Build Reg AI Control Panel")
st.sidebar.write("Simulating UK Building Regulations - Part M (Access)")
st.sidebar.markdown("---")

# User Upload Button
uploaded_file = st.sidebar.file_uploader("Upload Floor Plan (JPG/PNG)", type=["jpg", "jpeg", "png"])

# Calibration Slider (Simulating what the AI or user measures)
st.sidebar.subheader("AI Geometric Calibration")
pixel_width = st.sidebar.slider("Detected Entrance Door Width (Pixels)", min_value=10, max_value=100, value=45)
scale_factor = st.sidebar.slider("Scale Factor (mm per pixel)", min_value=5, max_value=25, value=15)

# Calculate real world dimension
real_world_width = pixel_width * scale_factor

st.sidebar.markdown("---")
st.sidebar.write("**Target Framework:** Approved Document M (2026 update)")

# 3. Main Interface Logic
st.title("🇬🇧 UK Building Regulations Compliance Checker")
st.subheader("Automated 2D Plan Geometric Validation Engine")

if uploaded_file is not None:
    # Open and process the image
    image = Image.open(uploaded_file)
    img_array = np.array(image)
    h, w, _ = img_array.shape
    
    # Create two columns: Left for Image, Right for Report
    col1, col2 = st.columns([2, 1])
    
    # Run the Part M Rule Engine
    # Mandated standard: Main entrance clear opening must be >= 775mm
    is_compliant = real_world_width >= 775
    
    with col1:
        st.write("### Analyzed Floor Plan")
        
        # Draw a simulated AI Bounding Box in the center of the plan
        # If it fails, box is Red. If it passes, box is Green.
        box_color = (0, 255, 0) if is_compliant else (255, 0, 0)
        
        # Define mock coordinates for the main entrance door on the plan
        start_point = (int(w * 0.45), int(h * 0.75))
        end_point = (int(w * 0.55), int(h * 0.85))
        
        # Draw the box using OpenCV
        marked_img = cv2.rectangle(img_array.copy(), start_point, end_point, box_color, 4)
        
        # Display the image
        st.image(marked_img, use_column_width=True)
        
    with col2:
        st.write("### Compliance Audit Report")
        
        st.metric(label="Measured Entrance Width", value=f"{real_world_width} mm")
        
        if is_compliant:
            st.success("✅ PASSED: ELEMENT COMPLIANT")
            st.write("**Element:** Principal Entrance Door")
            st.write("**Regulation:** Approved Document M, Section 1.14")
            st.write("**Requirement:** Minimum clear opening of 775mm.")
            st.info("The detected width meets or exceeds national accessibility baselines.")
        else:
            st.error("🚨 FAILED: NON-COMPLIANCE DETECTED")
            st.write("**Element:** Principal Entrance Door")
            st.write("**Regulation:** Approved Document M, Section 1.14")
            st.write("**Requirement:** Minimum clear opening of 775mm.")
            st.markdown("### Required Changes:")
            st.write(f"The current layout shows a clear opening of only **{real_world_width}mm**. The structural opening must be widened by at least **{775 - real_world_width}mm** to meet legal wheelchair access guidelines.")
            
else:
    st.info("Please upload a floor plan image in the sidebar to run the automated compliance scan.")
