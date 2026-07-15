import streamlit as st
import cv2
import numpy as np
from PIL import Image

# 1. Page Configuration
st.set_page_config(page_title="UK Build Reg AI - Calibration Suite", layout="wide")

# 2. Sidebar Interface - Calibration & Scale
st.sidebar.title("📏 Scale & Calibration Suite")
st.sidebar.write("Configure the plan's real-world dimensions.")
st.sidebar.markdown("---")

# Method Selection
calibration_method = st.sidebar.radio(
    "Choose Calibration Method:",
    ("Standard Scale Ratio", "Known Reference Object")
)

# Initialize scale variable (how many millimeters is 1 pixel?)
mm_per_pixel = 15.0 

if calibration_method == "Standard Scale Ratio":
    scale_system = st.sidebar.selectbox("Measurement System:", ("Metric (UK/EU)", "Imperial (US/Historic)"))
    
    if scale_system == "Metric (UK/EU)":
        metric_scale = st.sidebar.selectbox("Select Scale:", ("1:50", "1:100", "1:200"))
        # Mock conversions based on standard target DPI resolution
        if metric_scale == "1:50":
            mm_per_pixel = 10.0
        elif metric_scale == "1:100":
            mm_per_pixel = 20.0
        else:
            mm_per_pixel = 40.0
            
    else:
        imperial_scale = st.sidebar.selectbox("Select Scale:", ("1/4\" = 1'-0\"", "1/8\" = 1'-0\"", "3/16\" = 1'-0\""))
        # Convert imperial targets to metric mm equivalents for the UK engine
        if imperial_scale == "1/4\" = 1'-0\"":
            mm_per_pixel = 12.7
        elif imperial_scale == "1/8\" = 1'-0\"":
            mm_per_pixel = 25.4
        else:
            mm_per_pixel = 16.9

elif calibration_method == "Known Reference Object":
    st.sidebar.info("👉 Use a known dimension on the drawing (e.g., a structural wall length or standard door) to calibrate.")
    
    unit_type = st.sidebar.selectbox("Reference Unit:", ("Millimeters (mm)", "Meters (m)", "Inches (in)", "Feet (ft)"))
    raw_value = st.sidebar.number_input("Enter Known Real-World Length:", min_value=0.1, value=900.0, step=10.0)
    
    # Simulate drawing a reference line across pixels
    pixel_length = st.sidebar.slider("Reference Length in Pixels (Adjust to match object on plan):", min_value=10, max_value=500, value=60)
    
    # Convert input to millimeters for the core engine calculation
    if unit_type == "Meters (m)":
        real_mm = raw_value * 1000
    elif unit_type == "Inches (in)":
        real_mm = raw_value * 25.4
    elif unit_type == "Feet (ft)":
        real_mm = raw_value * 304.8
    else:
        real_mm = raw_value
        
    mm_per_pixel = real_mm / pixel_length

st.sidebar.markdown("---")
uploaded_file = st.sidebar.file_uploader("Upload Floor Plan to Analyze", type=["jpg", "jpeg", "png"])

# Simulating AI detecting a door width of 45 pixels
detected_door_pixels = 45
real_world_width = round(detected_door_pixels * mm_per_pixel, 1)

# 3. Main Interface View
st.title("🇬🇧 UK Building Regulations Compliance Checker")
st.subheader("Advanced Part M Validation with Active Scale Calibration")

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    img_array = np.array(image)
    h, w, _ = img_array.shape
    
    col1, col2 = st.columns([2, 1])
    
    # Run Approved Document M Rule Engine (Entrance door minimum 775mm)
    is_compliant = real_world_width >= 775
    box_color = (0, 255, 0) if is_compliant else (255, 0, 0)
    
    with col1:
        st.write("### Live Visual Inspection Map")
        
        # Draw simulated bounding box over the entrance door
        start_point = (int(w * 0.45), int(h * 0.75))
        end_point = (int(w * 0.55), int(h * 0.85))
        marked_img = cv2.rectangle(img_array.copy(), start_point, end_point, box_color, 4)
        
        # Add a text overlay on the plan showing the calculated dimension
        label = f"Door: {real_world_width}mm"
        cv2.putText(marked_img, label, (start_point[0], start_point[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, box_color, 2)
        
        st.image(marked_img, use_column_width=True)
        
    with col2:
        st.write("### Dynamic Compliance Report")
        
        # Display active scale stats so the council sees how it calculated the math
        st.write("🔧 **Active Calibration Math:**")
        st.caption(f"1 Pixel on this drawing = {round(mm_per_pixel, 2)} mm in the real world.")
        st.caption(f"Detected Door size: {detected_door_pixels} pixels.")
        
        st.metric(label="Calculated Real Opening Width", value=f"{real_world_width} mm")
        
        if is_compliant:
            st.success("✅ PASSED: ELEMENT COMPLIANT")
            st.write("**Element:** Principal Entrance Door")
            st.write("**Regulation:** Approved Document M, Section 1.14")
            st.info(f"The calculated width of {real_world_width}mm safely meets or exceeds the UK 775mm accessible minimum.")
        else:
            st.error("🚨 FAILED: ACCESSIBILITY VIOLATION")
            st.write("**Element:** Principal Entrance Door")
            st.write("**Regulation:** Approved Document M, Section 1.14")
            st.markdown("### Action Required:")
            st.write(f"The calibrated layout shows a clear opening of only **{real_world_width}mm**. This will block wheelchair access. The plan must be modified to provide an additional **{round(775 - real_world_width, 1)}mm** of width before building control approval can be granted.")
            
else:
    st.info("Please upload a floor plan image in the sidebar to activate the calibration engine.")
