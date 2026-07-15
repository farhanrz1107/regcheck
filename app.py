import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageOps
import pypdfium2 as pdfium
import math
from streamlit_image_coordinates import streamlit_image_coordinates

# --- PAGE CONFIGURATION & CSS ---
st.set_page_config(page_title="UK Build Reg AI | Enterprise", layout="wide", initial_sidebar_state="expanded")

# Inject Custom CSS for a highly professional, modern UI
st.markdown("""
    <style>
        /* Main Theme & Typography */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        html, body, [class*="css"]  {
            font-family: 'Inter', sans-serif;
        }
        
        /* Dashboard Metric Cards */
        div[data-testid="metric-container"] {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        
        /* Headers */
        h1, h2, h3 { color: #0f172a; }
        
        /* Success/Fail Badges */
        .status-pass { color: #15803d; font-weight: 600; background: #dcfce7; padding: 4px 8px; border-radius: 4px; }
        .status-fail { color: #b91c1c; font-weight: 600; background: #fee2e2; padding: 4px 8px; border-radius: 4px; }
        
        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background-color: #0f172a;
            color: #f8fafc;
        }
        /* Override sidebar text colors */
        .css-17lntkn { color: #f8fafc; }
        .stRadio label, .stSelectbox label, .stNumberInput label { color: #cbd5e1 !important; }
    </style>
""", unsafe_allow_html=True)


# --- SESSION STATE INITIALIZATION ---
if "calib_points" not in st.session_state:
    st.session_state["calib_points"] = []
if "last_click" not in st.session_state:
    st.session_state["last_click"] = None

# ----------------- SIDEBAR: CALIBRATION ENGINE -----------------
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/ae/HM_Government_logo.svg/512px-HM_Government_logo.svg.png", width=150)
    st.title("Automated Plan Audit")
    st.markdown("---")

    uploaded_file = st.file_uploader("1. Upload Application File (PDF/IMG)", type=["jpg", "jpeg", "png", "pdf"])

    st.markdown("---")
    st.subheader("2. Calibration Engine")

    calibration_mode = st.radio(
        "Scaling Method:",
        ("Standard Scale Factor", "Visual Reference (Click 2 Points)")
    )

    mm_per_pixel = 15.0  
    pixel_length = 1.0
    real_mm = 900.0

    if calibration_mode == "Visual Reference (Click 2 Points)":
        st.info("Click two points on the plan to measure a known length.")
        unit_type = st.selectbox("Unit:", ("Millimeters (mm)", "Meters (m)", "Inches (in)", "Feet (ft)"))
        raw_value = st.number_input("Known Length:", min_value=0.1, value=900.0, step=10.0)
        
        if unit_type == "Meters (m)": real_mm = raw_value * 1000
        elif unit_type == "Inches (in)": real_mm = raw_value * 25.4
        elif unit_type == "Feet (ft)": real_mm = raw_value * 304.8
        else: real_mm = raw_value
            
    else:
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
            
        st.session_state["calib_points"] = []
        st.session_state["last_click"] = None


# ----------------- MAIN VIEW -----------------
st.title("Building Regulations Validation Engine")
st.markdown("AI-Powered Geometric Compliance Scanning for UK Local Planning Authorities")

if uploaded_file is not None:
    try:
        # 1. Load and process file
        if uploaded_file.name.lower().endswith('.pdf'):
            pdf = pdfium.PdfDocument(uploaded_file)
            page = pdf[0]
            pil_image = page.render(scale=2).to_pil().convert("RGB")
        else:
            pil_image = Image.open(uploaded_file).convert("RGB")
            pil_image = ImageOps.exif_transpose(pil_image)
        
        # 2. Resize for web performance
        max_width = 1000
        w, h = pil_image.size
        if w > max_width:
            ratio = max_width / float(w)
            new_h = int(float(h) * float(ratio))
            pil_image = pil_image.resize((max_width, new_h), Image.Resampling.LANCZOS)
            w, h = pil_image.size
            
        base_img_array = np.array(pil_image).copy()

        # 3. Handle Visual Calibration Logic BEFORE displaying the UI tabs
        if calibration_mode == "Visual Reference (Click 2 Points)":
            if len(st.session_state["calib_points"]) == 2:
                p1 = st.session_state["calib_points"][0]
                p2 = st.session_state["calib_points"][1]
                pixel_length = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
                if pixel_length > 0:
                    mm_per_pixel = real_mm / pixel_length

        # 4. Global KPIs
        st.markdown("### 📊 Document Overview")
        col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
        col_kpi1.metric("System Scale", f"1 px = {round(mm_per_pixel, 2)} mm")
        col_kpi2.metric("Regulations Scanned", "3 Frameworks")
        col_kpi3.metric("AI Confidence Score", "94.2%")
        col_kpi4.metric("Document Status", "Issues Detected", delta="-2 Minor Violations", delta_color="inverse")
        
        st.markdown("<br>", unsafe_allow_html=True)

        # 5. Dashboard Tabs
        tab_setup, tab_m, tab_b, tab_l = st.tabs([
            "⚙️ Calibration Workspace", 
            "♿ Part M (Access)", 
            "🔥 Part B (Fire Safety)", 
            "🌍 Part L (Energy)"
        ])
        
        # --- TAB 1: CALIBRATION WORKSPACE ---
        with tab_setup:
            st.markdown("Use this tab to establish drawing scale before reviewing the automated AI audits.")
            
            if calibration_mode == "Visual Reference (Click 2 Points)":
                interactive_img = base_img_array.copy()
                for idx, p in enumerate(st.session_state["calib_points"]):
                    cv2.circle(interactive_img, p, 5, (255, 0, 0), -1)
                    label = "A" if idx == 0 else "B"
                    cv2.putText(interactive_img, label, (p[0] + 10, p[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
                
                if len(st.session_state["calib_points"]) == 2:
                    cv2.line(interactive_img, st.session_state["calib_points"][0], st.session_state["calib_points"][1], (255, 0, 0), 2)
                
                click_data = streamlit_image_coordinates(interactive_img, key="calib_clicker")
                
                if click_data is not None:
                    point = (click_data["x"], click_data["y"])
                    if st.session_state["last_click"] != point:
                        st.session_state["last_click"] = point
                        if len(st.session_state["calib_points"]) >= 2:
                            st.session_state["calib_points"] = [point]
                        else:
                            st.session_state["calib_points"].append(point)
                        st.rerun()
            else:
                st.image(base_img_array, use_column_width=True, caption="View-Only Mode. Switch to Visual Reference in sidebar to calibrate manually.")

        # --- TAB 2: PART M (Access to and use of buildings) ---
        with tab_m:
            c1, c2 = st.columns([2, 1])
            
            # AI Mock Values for Part M
            detected_door_px = 45 
            real_door_width_mm = round(detected_door_px * mm_per_pixel, 1)
            is_door_compliant = real_door_width_mm >= 775
            
            with c1:
                img_m = base_img_array.copy()
                start_x, start_y = int(w * 0.45), int(h * 0.60)
                end_x, end_y = start_x + detected_door_px, start_y + 60 
                color_m = (0, 255, 0) if is_door_compliant else (255, 0, 0)
                
                cv2.rectangle(img_m, (start_x, start_y), (end_x, end_y), color_m, 4)
                cv2.putText(img_m, f"DOOR: {real_door_width_mm}mm", (start_x, start_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_m, 2)
                st.image(img_m, use_column_width=True)
                
            with c2:
                st.markdown("### Part M Audit Report")
                st.markdown("**(Vol 1: Dwellings) - Section 1.14**")
                st.write("Ensuring inclusive access via principal entrance dimensions.")
                st.markdown("---")
                
                st.metric(label="Calculated Clear Opening", value=f"{real_door_width_mm} mm", delta="Req: 775mm min")
                
                if is_door_compliant:
                    st.markdown("<span class='status-pass'>✔ COMPLIANT</span>", unsafe_allow_html=True)
                    st.write("The detected entrance meets accessibility thresholds.")
                else:
                    st.markdown("<span class='status-fail'>✖ VIOLATION DETECTED</span>", unsafe_allow_html=True)
                    st.error(f"Opening is {round(775 - real_door_width_mm, 1)}mm too narrow for wheelchair access.")

        # --- TAB 3: PART B (Fire Safety) ---
        with tab_b:
            c1, c2 = st.columns([2, 1])
            
            # AI Mock Values for Part B
            # Simulated pixel length of an escape route
            escape_route_px = 1350 
            real_escape_dist_m = round((escape_route_px * mm_per_pixel) / 1000, 1)
            max_escape_dist = 18.0 # 18 meters for a single direction escape
            is_fire_compliant = real_escape_dist_m <= max_escape_dist
            
            with c1:
                img_b = base_img_array.copy()
                color_b = (0, 255, 0) if is_fire_compliant else (255, 140, 0) # Orange for fire warning
                
                # Draw a mock zig-zag escape route line
                pts = np.array([
                    [int(w*0.8), int(h*0.2)], 
                    [int(w*0.8), int(h*0.5)], 
                    [int(w*0.4), int(h*0.5)], 
                    [int(w*0.4), int(h*0.9)]
                ], np.int32)
                pts = pts.reshape((-1, 1, 2))
                cv2.polylines(img_b, [pts], False, color_b, 5)
                
                # Mark Fire Exit
                cv2.circle(img_b, (int(w*0.4), int(h*0.9)), 15, (0,0,255), -1)
                cv2.putText(img_b, "FIRE EXIT", (int(w*0.4)+20, int(h*0.9)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)
                
                st.image(img_b, use_column_width=True)
                
            with c2:
                st.markdown("### Part B Audit Report")
                st.markdown("**(Vol 1: Dwellings) - Section 2.13**")
                st.write("Evaluating maximum travel distances for fire escape routes.")
                st.markdown("---")
                
                st.metric(label="Max Travel Distance to Exit", value=f"{real_escape_dist_m} m", delta="Limit: 18.0 m", delta_color="inverse")
                
                if is_fire_compliant:
                    st.markdown("<span class='status-pass'>✔ COMPLIANT</span>", unsafe_allow_html=True)
                    st.write("Escape route length is within safe limits.")
                else:
                    st.markdown("<span class='status-fail'>✖ WARNING DETECTED</span>", unsafe_allow_html=True)
                    st.warning(f"Travel distance exceeds single-direction escape limit by {round(real_escape_dist_m - max_escape_dist, 1)}m. Protected hallway required.")

        # --- TAB 4: PART L (Conservation of Fuel and Power) ---
        with tab_l:
            c1, c2 = st.columns([2, 1])
            
            # AI Mock Values for Part L
            # Glazing shouldn't exceed 25% of total floor area
            room_area_px2 = 200 * 300
            window_area_px2 = 120 * 20
            
            # Convert px^2 to m^2
            mm2_per_px2 = mm_per_pixel ** 2
            room_area_m2 = round((room_area_px2 * mm2_per_px2) / 1000000, 1)
            window_area_m2 = round((window_area_px2 * mm2_per_px2) / 1000000, 1)
            
            glazing_ratio = round((window_area_m2 / room_area_m2) * 100, 1) if room_area_m2 > 0 else 0
            is_energy_compliant = glazing_ratio <= 25.0
            
            with c1:
                img_l = base_img_array.copy()
                color_l = (0, 255, 0) if is_energy_compliant else (255, 0, 0)
                
                # Mock Room Box
                rx1, ry1 = int(w*0.1), int(h*0.1)
                rx2, ry2 = int(w*0.3), int(h*0.4)
                cv2.rectangle(img_l, (rx1, ry1), (rx2, ry2), (200, 200, 200), 2)
                cv2.putText(img_l, f"ROOM AREA: {room_area_m2}m2", (rx1, ry1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100,100,100), 2)
                
                # Mock Window Box
                wx1, wy1 = int(w*0.1), int(h*0.2)
                wx2, wy2 = int(w*0.1) + 20, int(h*0.3)
                cv2.rectangle(img_l, (wx1, wy1), (wx2, wy2), (0, 150, 255), -1) # Blue filled window
                cv2.putText(img_l, "GLAZING", (wx2 + 5, wy1 + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 150, 255), 2)
                
                st.image(img_l, use_column_width=True)
                
            with c2:
                st.markdown("### Part L Audit Report")
                st.markdown("**(Vol 1: Dwellings) - Section 1.5**")
                st.write("Calculating Glazing-to-Floor-Area limits to prevent heat loss.")
                st.markdown("---")
                
                st.metric(label="Calculated Glazing Ratio", value=f"{glazing_ratio}%", delta="Limit: 25.0%", delta_color="inverse")
                
                st.write(f"**Calculated Floor Area:** {room_area_m2} m²")
                st.write(f"**Calculated Glazing Area:** {window_area_m2} m²")
                
                if is_energy_compliant:
                    st.markdown("<span class='status-pass'>✔ COMPLIANT</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span class='status-fail'>✖ VIOLATION DETECTED</span>", unsafe_allow_html=True)
                    st.error("Glazing area exceeds the 25% baseline. Evidence of thermal compensation or SAP calculations must be provided.")

    except Exception as e:
        st.error(f"An error occurred loading the image: {e}")
else:
    st.info("Upload a plan to activate the engine.")
