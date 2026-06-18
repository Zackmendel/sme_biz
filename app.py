# app.py
import os
import streamlit as st
from dotenv import load_dotenv
from supabase import Client, create_client

# Modular feature imports
from home import show_dashboard_ui
from users import show_user_management_ui
from sales import show_sales_management_ui
from auth import show_auth_screen, sign_out
from onboard import show_onboarding_screen
from products import show_products_management_ui
from dashboard import show_dashboard_metrics

# Initialize core page settings
st.set_page_config(layout="wide", page_title="Business Portal")

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_PUBLISHABLE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# --- MAIN APP LAYOUT ---

def main_app(user_email, user_role, user_business_id):
    # 🛑 CORE GATEKEEPER: Redirect to onboarding window if user has no assigned business_id
    if not user_business_id:
        show_onboarding_screen(supabase, user_email, st.session_state.user_id)
        return

    # --- SIDEBAR NAVIGATION PANEL (Only accessible if onboarded) ---
    with st.sidebar:
        st.title("Navigation Menu")
        st.write(f"👤 **{user_email}**\nRole: `{user_role.upper()}`")
        st.divider()
        
        nav_options = ["Home"]
        if user_role in ["admin", "owner"]:
            nav_options.extend(["Dashboard", "Sales Matrix", "Product Catalog", "User Controls"])

        if user_role == "staff":
            nav_options.extend(["Dashboard", "Sales Matrix", "Product Catalog"])
            
        chosen_page = st.radio("Go to Page:", options=nav_options)
        
        st.divider()
        if st.button("🚪 Log Out Systems", type="secondary", width='stretch'):
            sign_out(supabase)

    # --- MAIN VIEW ROUTING LOGIC ---
    if chosen_page == "Home":
        show_dashboard_ui(user_role=user_role, business_uuid=user_business_id)

    elif chosen_page == "Dashboard" and user_role in ["admin", "owner", "staff"]:
        show_dashboard_metrics(supabase, user_business_id)

    elif chosen_page == "Sales Matrix" and user_role in ["admin", "owner", "staff"]:
        show_sales_management_ui()

    elif chosen_page == "User Controls" and user_role in ["admin", "owner"]:
        show_user_management_ui()

    elif chosen_page == "Product Catalog" and user_role in ["admin", "owner", "staff"]:
        show_products_management_ui()

# --- INITIALIZATION & ROUTING ENGINE ---

if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "user_business_id" not in st.session_state:
    st.session_state.user_business_id = None

# Boot router switch 
if st.session_state.user_email:
    main_app(st.session_state.user_email, st.session_state.user_role, st.session_state.user_business_id)
else:
    show_auth_screen(supabase)