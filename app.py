import os
import sys

# Detect if running on Streamlit Cloud
IS_CLOUD = os.getenv('STREAMLIT_RUNTIME_ENV') == 'cloud' or \
           'streamlit' in os.getenv('HOME', '')

# Configure Chrome for cloud environment
if IS_CLOUD:
    from selenium.webdriver.chrome.options import Options
    def get_chrome_options():
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.binary_location = '/usr/bin/chromium'
        return options
import streamlit as st
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from src.scraper_selenium import scrape_olx_listings
 
# Cache scraper results to avoid repeated downloads during interactive use
@st.cache_data(ttl=60 * 10)
def cached_scrape(model_name: str, pages: int = 1, headless: bool = True, wait: int = 3):
    try:
        return scrape_olx_listings(model_name, pages=pages, headless=headless, wait=wait)
    except Exception as e:
        st.error(f"Scraping error: {e}")
        return []

# --- Model load (robust) ---
MODEL_PATH = Path("models/wheel_deal_pipeline.pkl")
model = None
load_error = None
try:
    model = joblib.load(MODEL_PATH)
except Exception as e:
    load_error = str(e)

# --- Page config ---
st.set_page_config(page_title="Wheel Deal 🚘", page_icon="🚗", layout="centered")

# --- Dark / Light Mode Toggle ---
dark_mode = st.checkbox("🌙 Dark Mode", value=True)

# --- Styling (keeping your existing styles) ---
background_url = "https://images.unsplash.com/photo-1605559424843-9b57d8d8b1d8?auto=format&fit=crop&w=1650&q=80"

if dark_mode:
    text_color = "#E6EDF3"
    box_bg = "rgba(22,27,34,0.85)"
    accent = "#FF6B6B"
else:
    text_color = "#222"
    box_bg = "rgba(255,255,255,0.92)"
    accent = "#FF4B4B"

overlay = 'rgba(0,0,0,0.45)' if dark_mode else 'rgba(255,255,255,0.75)'
card_shadow = '0 10px 30px rgba(2,6,23,0.45)' if dark_mode else '0 8px 24px rgba(20,20,30,0.06)'
card_text_color = text_color
# Subtle background gradient to give a classy layered look
if dark_mode:
    gradient_start = 'rgba(6,18,28,0.60)'
    gradient_end = 'rgba(28,42,66,0.45)'
else:
    gradient_start = 'rgba(255,245,235,0.55)'
    gradient_end = 'rgba(245,230,255,0.40)'

st.markdown(
    f"""
    <style>
    .stApp .main > div[role="main"], .stApp .block-container {{
        max-width: 1100px;
        margin: 0 auto;
        padding-top: 12px;
        padding-left: 18px;
        padding-right: 18px;
        background: transparent !important;
    }}
    .stApp > div:first-child {{
        /* layered background: soft diagonal gradient + overlay + image */
        background-image: linear-gradient(135deg, {gradient_start}, {gradient_end}),
                          linear-gradient(180deg, {overlay}, rgba(0,0,0,0.06)),
                          url("{background_url}");
        background-size: cover, cover, cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-position: center center;
        background-blend-mode: overlay, multiply, normal;
        padding-top: 18px;
        padding-bottom: 32px;
    }}
    .card {{
      background: {box_bg} !important;
      color: {card_text_color} !important;
      padding: 18px;
      border-radius: 12px;
      box-shadow: {card_shadow};
    }}
    .subtitle {{
        text-align: left;
        color: {card_text_color};
        margin-top: 6px;
        margin-bottom: 0px;
        opacity: 0.95;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<h1 class='main-title'>Wheel Deal 🚘</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>A modern, friendly car price estimator — enter details and get an instant estimate</p>", unsafe_allow_html=True)

# --- Input form ---
st.markdown("<h3 style='text-align:center; margin-top:24px;'>🚗 Choose Your Mode</h3>", unsafe_allow_html=True)
mode = st.radio("Mode", ["Single Car Estimate", "Compare Two Cars"], horizontal=True)

def predict_price(inputs):
    """Build a DataFrame with the features the pipeline expects and predict."""
    categorical_defaults = {
        "seller_type": "individual",
        "brand": "other",
        "transmission_type": "manual",
        "model": "unknown",
        "fuel_type": "petrol",
    }
    numeric_defaults = {"vehicle_age": 5, "km_driven": 20000, "mileage": 18.0,
                        "engine": 1200, "max_power": 80.0, "seats": 5}
    
    expected_cols = []
    try:
        if model is not None and hasattr(model, "named_steps") and "preproc" in model.named_steps:
            ct = model.named_steps["preproc"]
            for name, transformer, cols in getattr(ct, "transformers_", ct.transformers):
                if name == "remainder":
                    continue
                if isinstance(cols, (list, tuple, np.ndarray)):
                    expected_cols.extend(list(cols))
                elif isinstance(cols, str):
                    expected_cols.append(cols)
    except Exception:
        expected_cols = []
    
    if not expected_cols:
        expected_cols = list(numeric_defaults.keys()) + list(categorical_defaults.keys())
    
    row = {}
    for col in expected_cols:
        if col in inputs:
            row[col] = inputs[col]
        elif col in numeric_defaults:
            row[col] = inputs.get(col, numeric_defaults[col])
        elif col in categorical_defaults:
            row[col] = inputs.get(col, categorical_defaults[col])
        else:
            row[col] = inputs.get(col, "missing")
    
    df = pd.DataFrame([row])
    pred_log = model.predict(df)[0]
    if isinstance(pred_log, (list, tuple, np.ndarray)):
        pred_log = float(pred_log[0])
    price = np.expm1(pred_log)
    return max(price, 0)

# --- SINGLE CAR ESTIMATE ---
if mode == "Single Car Estimate":
    with st.form(key="single_form"):
        col1, col2 = st.columns(2)
        with col1:
            vehicle_age = st.slider("Vehicle age (years)", 0, 30, 5)
            km_driven = st.number_input("Kilometers driven", 0, 2_000_000, 20000, step=1000)
            mileage = st.number_input("Mileage (km/l)", 1.0, 60.0, 18.0, step=0.5)
        with col2:
            engine = st.number_input("Engine (cc)", 600, 5000, 1200, step=50)
            max_power = st.number_input("Max power (bhp)", 20.0, 800.0, 80.0, step=1.0)
            seats = st.number_input("Seats", 2, 8, 5, step=1)
        submit1 = st.form_submit_button("💫 Get My Car's Worth!")

    if submit1:
        inputs = dict(vehicle_age=vehicle_age, km_driven=km_driven, mileage=mileage,
                      engine=engine, max_power=max_power, seats=seats)
        with st.spinner("Estimating price..."):
            price = predict_price(inputs)
        
        # Store price in session state for OLX scraping
        st.session_state.estimated_price = price
        st.success(f"💰 Estimated Selling Price: ₹{price:,.0f}")

    # --- OLX Listings Section (FIXED) ---
    if 'estimated_price' in st.session_state:
        st.markdown("---")
        st.markdown("### 🔍 Find Similar Cars on OLX")
        
        # Create a form for scraping parameters
        with st.form(key="scrape_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                query = st.text_input("Search query (e.g., 'swift delhi', 'hyundai i20')", 
                                     value="used cars", 
                                     help="Be specific! Include car model or brand")
                pages = st.slider("Pages to scrape", 1, 3, 1, 
                                 help="More pages = more results but slower")
            with col_b:
                tol = st.slider("Price tolerance (%)", 5, 50, 20,
                               help="Find cars within ±this % of estimated price")
                debug = st.checkbox("Debug mode (show browser)", value=False)
            
            scrape_button = st.form_submit_button("🚀 Search OLX Listings")
        
        if scrape_button:
            price = st.session_state.estimated_price
            
            with st.spinner(f"Fetching live listings for '{query}' (this may take 10-30 seconds)..."):
                if debug:
                    st.info("🐛 Debug mode: Browser window will open. Check terminal for details.")
                    listings = scrape_olx_listings(query, pages=pages, headless=False, wait=6)
                else:
                    listings = cached_scrape(query, pages=pages, headless=True, wait=4)
            
            st.write(f"**Scraped {len(listings)} listings for query '{query}'**")
            
            if not listings:
                st.warning("⚠️ No listings found. Possible reasons:")
                st.info("""
                - Query returned no results on OLX
                - WebDriver failed (check terminal for errors)
                - OLX changed their website structure
                - Try a different search query (e.g., 'maruti swift', 'honda city delhi')
                """)
            else:
                # Show raw sample in expander
                with st.expander("📋 View raw data (first 3 listings)", expanded=False):
                    for i, item in enumerate(listings[:3], 1):
                        st.write(f"**Listing {i}:**")
                        st.json(item)
                
                # Filter by price
                low = price * (1 - tol / 100.0)
                high = price * (1 + tol / 100.0)
                filtered = [l for l in listings if (l.get("price") is not None and low <= l["price"] <= high)]
                
                st.write(f"**{len(filtered)} listings matched the price range ₹{low:,.0f} - ₹{high:,.0f} (±{tol}%)**")
                
                if not filtered:
                    st.info("No exact matches. Showing 10 closest listings by price:")
                    valid_listings = [l for l in listings if l.get('price')]
                    if valid_listings:
                        ranked = sorted(valid_listings, key=lambda x: abs(x['price'] - price))
                        results = ranked[:10]
                    else:
                        st.warning("No listings have valid prices to compare.")
                        results = []
                else:
                    results = filtered[:10]
                
                # Display results
                if results:
                    st.markdown("### 🚗 Similar Cars:")
                    for idx, l in enumerate(results, 1):
                        title = l.get('title', 'No title')
                        url = l.get('url', '#')
                        price_val = l.get('price')
                        meta = l.get('meta', '')
                        
                        price_str = f"₹{price_val:,}" if isinstance(price_val, (int, float)) else str(price_val or 'N/A')
                        
                        # Calculate price difference
                        if isinstance(price_val, (int, float)):
                            diff = price_val - price
                            diff_pct = (diff / price) * 100
                            diff_str = f"({diff_pct:+.1f}%)" if abs(diff_pct) > 1 else ""
                        else:
                            diff_str = ""
                        
                        st.markdown(f"""
                        **{idx}. [{title}]({url})**  
                        💰 Price: {price_str} {diff_str}  
                        📍 {meta}
                        """)
                        st.markdown("---")

# --- CAR COMPARISON MODE ---
else:
    st.markdown("<h3 style='text-align:center;'>Compare Two Cars Side by Side 🆚</h3>", unsafe_allow_html=True)
    colA, colB = st.columns(2, gap="large")

    with colA:
        st.subheader("Car A")
        a_age = st.slider("Vehicle age (years)", 0, 30, 5, key="a_age")
        a_km = st.number_input("Kilometers driven", 0, 2_000_000, 40000, step=1000, key="a_km")
        a_mileage = st.number_input("Mileage (km/l)", 1.0, 60.0, 18.0, step=0.5, key="a_mileage")
        a_engine = st.number_input("Engine (cc)", 600, 5000, 1200, step=50, key="a_engine")
        a_power = st.number_input("Max power (bhp)", 20.0, 800.0, 80.0, step=1.0, key="a_power")
        a_seats = st.number_input("Seats", 2, 8, 5, step=1, key="a_seats")

    with colB:
        st.subheader("Car B")
        b_age = st.slider("Vehicle age (years)", 0, 30, 8, key="b_age")
        b_km = st.number_input("Kilometers driven ", 0, 2_000_000, 60000, step=1000, key="b_km")
        b_mileage = st.number_input("Mileage (km/l) ", 1.0, 60.0, 20.0, step=0.5, key="b_mileage")
        b_engine = st.number_input("Engine (cc) ", 600, 5000, 1500, step=50, key="b_engine")
        b_power = st.number_input("Max power (bhp) ", 20.0, 800.0, 100.0, step=1.0, key="b_power")
        b_seats = st.number_input("Seats ", 2, 8, 5, step=1, key="b_seats")

    if st.button("⚖️ Compare Prices"):
        with st.spinner("Predicting both cars..."):
            price_a = predict_price(dict(vehicle_age=a_age, km_driven=a_km, mileage=a_mileage,
                                         engine=a_engine, max_power=a_power, seats=a_seats))
            price_b = predict_price(dict(vehicle_age=b_age, km_driven=b_km, mileage=b_mileage,
                                         engine=b_engine, max_power=b_power, seats=b_seats))

        diff = price_a - price_b
        better = "Car A" if diff > 0 else "Car B"
        color = "#4CAF50" if diff > 0 else "#FF6B6B"

        st.markdown(f"""
        <div style="text-align:center; margin-top:18px;">
            <h4>💰 Car A: ₹{price_a:,.0f}</h4>
            <h4>💰 Car B: ₹{price_b:,.0f}</h4>
            <h3 style="color:{color}; margin-top:12px;">{better} is worth ₹{abs(diff):,.0f} more</h3>
        </div>
        """, unsafe_allow_html=True)

        st.progress(min(int((price_a / (price_a + price_b)) * 100), 100))

# --- Footer ---
st.markdown(
    f"""
    <hr style="opacity:0.2"/>
    <p style='text-align:center; color: {text_color}; font-size: 14px;'>
         Made with ❤️ by <b>Rashi Kushwaha</b><br>
        <i>Powered by Random Forest · Streamlit · Wheel Deal 🚗</i>
    </p>
    """,
    unsafe_allow_html=True,
)