# auth.py
import streamlit as st

def sign_up(supabase, email, password):
    try:
        return supabase.auth.sign_up({"email": email, "password": password})
    except Exception as e:
        st.error(f"Registration failed: {e}")

def sign_in(supabase, email, password):
    try:
        return supabase.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as e:
        st.error(f"Login failed: {e}")

def sign_out(supabase):
    try:
        supabase.auth.sign_out()
        st.session_state.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Logout failed: {e}")

def get_user_profile(supabase, email):
    """Fetches full profile information for state routing rules."""
    try:
        response = supabase.table("users").select("role, business_id").eq("email", email).execute()
        if response.data:
            return response.data[0]
        return {"role": "viewer", "business_id": None}
    except Exception as e:
        st.error(f"Error checking user permissions: {e}")
        return {"role": "viewer", "business_id": None}

def show_auth_screen(supabase):
    st.title("🔐 Streamlit & Supabase Auth App")
    option = st.selectbox("Choose an action:", ["Login", "Sign Up"])
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if option == "Sign Up":
        confirm_password = st.text_input("Retype Password", type="password")

    if option == "Sign Up" and st.button("Register"):
        if not email.strip() or not password.strip():
            st.error("Please fill in all fields.")
        elif password != confirm_password:
            st.error("❌ Passwords do not match!")
        elif len(password) < 6:
            st.error("⚠️ Password must be at least 6 characters long.")
        else:
            user = sign_up(supabase, email, password)
            if user and user.user:
                st.success("Registration successful. Please log in.")

    if option == "Login" and st.button("Login"):
        if not email.strip() or not password.strip():
            st.error("Please enter both email and password.")
        else:
            user = sign_in(supabase, email, password)
            if user and user.user:
                profile = get_user_profile(supabase, user.user.email)
                
                # Fetch and persist all context details inside session cache parameters
                st.session_state.user_id = user.user.id
                st.session_state.user_email = user.user.email
                st.session_state.user_role = profile.get("role")
                st.session_state.user_business_id = profile.get("business_id")
                
                st.success(f"Welcome back!")
                st.rerun()