# onboard.py
import streamlit as st
from users import edit_user
from auth import sign_out

def get_all_businesses(supabase):
    """Fetches available corporate entries to fill onboarding options safely."""
    try:
        response = supabase.table("businesses").select("id, name").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error retrieving business associations: {e}")
        return []

def show_onboarding_screen(supabase, user_email, user_id):
    st.title("🚀 Complete Your Profile Onboarding")
    st.write("Welcome! Before continuing to the dashboard, please associate your identity with a registered business.")
    
    # Extract structural business data
    biz_data = get_all_businesses(supabase)
    if not biz_data:
        st.error("No active businesses found on system records. Contact systems supervisor.")
        if st.button("Logout"):
            sign_out(supabase)
        return

    biz_lookup = {b["name"]: b["id"] for b in biz_data}
    
    with st.form("User Onboarding Workspace"):
        chosen_biz_name = st.selectbox("Select Associated Business", options=list(biz_lookup.keys()))
        first_name = st.text_input("First Name", placeholder="Jane")
        last_name = st.text_input("Last Name", placeholder="Doe")
        status = st.selectbox("Employment Contract Status", options=["permanent", "part_time", "intern", "contract"])
        
        if st.form_submit_button("Complete Setup", type="primary"):
            if not first_name.strip() or not last_name.strip():
                st.error("Please provide both your First and Last name.")
            else:
                payload = {
                    "business_id": biz_lookup[chosen_biz_name],
                    "first_name": first_name.strip(),
                    "last_name": last_name.strip(),
                    "status": status
                }
                
                # Update table profile fields via the user engine tool
                result = edit_user(user_id, payload)
                if result:
                    st.success("Onboarding profiling completed successfully!")
                    # Instantly sync session state keys to bypass step on rerun
                    st.session_state.user_business_id = payload["business_id"]
                    st.rerun()