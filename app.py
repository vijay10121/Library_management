import streamlit as st
import pandas as pd
from datetime import date
import time
from db import get_connection
import mysql.connector


# Page configuration
st.set_page_config(
    page_title="Library Management System",
    page_icon="📚",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.5rem;
    }
    .sub-text {
        color: #4B5563;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F3F4F6;
        border-radius: 8px;
        padding: 1rem;
        border-left: 4px solid #3B82F6;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None


def authenticate(username, password):
    """
    Check username and password against users table.
    Never exposes passwords.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT user_id, username, role FROM users WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user
    except mysql.connector.Error as err:
        st.error(f"Database Error: {err}")
        return None


def logout():
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.role = None
    st.rerun()


# ==========================================
# AUTHENTICATION SCREEN (LOGIN / SIGN UP)
# ==========================================
if not st.session_state.logged_in:
    st.markdown('<div class="main-header">📚 Library Management System</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-text">Please log in or create a new account to access the system.</div>', unsafe_allow_html=True)
    
    col1, col2, _ = st.columns([1.2, 1, 0.8])
    with col1:
        auth_tab1, auth_tab2 = st.tabs(["🔑 Sign In", "📝 Sign Up"])
        
        # --- TAB 1: SIGN IN ---
        with auth_tab1:
            with st.form("login_form"):
                st.subheader("Sign In")
                username_input = st.text_input("Username").strip()
                password_input = st.text_input("Password", type="password")
                submit = st.form_submit_button("Sign In", use_container_width=True)
                
                if submit:
                    if not username_input or not password_input:
                        st.warning("Please provide both username and password.")
                    else:
                        user = authenticate(username_input, password_input)
                        if user:
                            st.session_state.logged_in = True
                            st.session_state.user_id = user["user_id"]
                            st.session_state.username = user["username"]
                            st.session_state.role = user["role"]
                            st.success(f"Welcome back, {user['username']} ({user['role']})!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password.")
                            
        # --- TAB 2: SIGN UP ---
        with auth_tab2:
            with st.form("signup_form"):
                st.subheader("Create New Account")
                new_username = st.text_input("Choose Username", key="signup_username").strip()
                new_password = st.text_input("Choose Password", type="password", key="signup_password")
                confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")
                role_choice = st.selectbox("Select Role", ["issuer", "admin"], help="Choose issuer for issuing desk staff, or admin for inventory and return management.")
                
                signup_submit = st.form_submit_button("Sign Up", use_container_width=True)
                
                if signup_submit:
                    if not new_username or not new_password or not confirm_password:
                        st.warning("Please fill in all fields.")
                    elif len(new_username) < 3:
                        st.warning("Username must be at least 3 characters long.")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match!")
                    else:
                        try:
                            conn = get_connection()
                            cursor = conn.cursor(dictionary=True)
                            
                            # Check if username already exists
                            cursor.execute("SELECT user_id FROM users WHERE username = %s", (new_username,))
                            existing = cursor.fetchone()
                            
                            if existing:
                                st.error(f"Username '{new_username}' is already taken. Please choose another.")
                            else:
                                insert_q = "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)"
                                cursor.execute(insert_q, (new_username, new_password, role_choice))
                                conn.commit()
                                st.success("🎉 Account created successfully! Please switch to the 'Sign In' tab to log in.")
                                
                            cursor.close()
                            conn.close()
                        except mysql.connector.Error as err:
                            st.error(f"Database error during registration: {err}")
                        except Exception as e:
                            st.error(f"An error occurred: {e}")
                        
    with col2:
        st.info("💡 **Project Roles & Permissions**\n\n- **Admin**: Manage book catalog (view, add, update copies), process book returns (`after_book_return` trigger), and view all issue history.\n- **Issuer**: Issue books to students via stored procedure (`issue_book`), browse catalog, and track issued books.")


# ==========================================
# DASHBOARD (AFTER LOGIN)
# ==========================================
else:
    # Sidebar
    st.sidebar.markdown(f"### 👤 {st.session_state.username.title()}")
    st.sidebar.caption(f"Role: **{st.session_state.role.upper()}** (ID: {st.session_state.user_id})")
    # Navigation based on role with persistent key in session_state
    if st.session_state.role == "admin":
        admin_options = ["📖 Book Inventory", "➕ Add New Book", "📥 Active Issues & Returns", "📑 All Issue History"]
        menu = st.sidebar.radio(
            "Navigation",
            admin_options,
            key="admin_nav_menu"
        )
    else:  # issuer
        issuer_options = ["📤 Issue Book", "📖 Browse Books", "📑 My Issued History"]
        menu = st.sidebar.radio(
            "Navigation",
            issuer_options,
            key="issuer_nav_menu"
        )
        
    st.sidebar.divider()
    
    # Manual Sync / Refresh
    st.sidebar.subheader("🔄 Data Sync")
    if st.sidebar.button("Refresh Current View", use_container_width=True):
        st.rerun()
        
    st.sidebar.divider()
    if st.sidebar.button("Log Out", use_container_width=True):
        logout()



    # ----------------------------------------------------
    # ADMIN VIEWS
    # ----------------------------------------------------
    if st.session_state.role == "admin":
        st.markdown(f'<div class="main-header">Admin Portal - {menu}</div>', unsafe_allow_html=True)
        
        # 1. Book Inventory
        if menu == "📖 Book Inventory":
            st.subheader("Current Book Catalog")
            try:
                conn = get_connection()
                query = "SELECT book_id, title, author, total_copies, available_copies FROM books ORDER BY book_id ASC"
                df = pd.read_sql(query, conn)
                conn.close()
                
                # Overview stats
                col1, col2, col3 = st.columns(3)
                total_titles = len(df)
                total_copies = df["total_copies"].sum() if not df.empty else 0
                avail_copies = df["available_copies"].sum() if not df.empty else 0
                col1.metric("Total Titles", total_titles)
                col2.metric("Total Copies", int(total_copies))
                col3.metric("Available Copies", int(avail_copies))
                
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Update copies section
                st.divider()
                st.subheader("Update Book Inventory")
                if not df.empty:
                    book_options = {f"ID {row['book_id']}: {row['title']} by {row['author']}": row for _, row in df.iterrows()}
                    selected_label = st.selectbox("Select Book to Update", list(book_options.keys()))
                    selected_book = book_options[selected_label]
                    
                    with st.form("update_copies_form"):
                        new_total = st.number_input("Total Copies", min_value=1, value=int(selected_book["total_copies"]), step=1)
                        new_avail = st.number_input("Available Copies", min_value=0, max_value=int(new_total), value=min(int(selected_book["available_copies"]), int(new_total)), step=1)
                        
                        update_btn = st.form_submit_button("Update Book Copies")
                        if update_btn:
                            conn = get_connection()
                            cursor = conn.cursor()
                            update_q = "UPDATE books SET total_copies = %s, available_copies = %s WHERE book_id = %s"
                            cursor.execute(update_q, (new_total, new_avail, selected_book["book_id"]))
                            conn.commit()
                            cursor.close()
                            conn.close()
                            st.success(f"Updated inventory for '{selected_book['title']}' successfully!")
                            st.rerun()
            except Exception as e:
                st.error(f"Error loading book inventory: {e}")
                
        # 2. Add New Book
        elif menu == "➕ Add New Book":
            st.subheader("Add Book to Library")
            with st.form("add_book_form"):
                title = st.text_input("Book Title").strip()
                author = st.text_input("Author").strip()
                copies = st.number_input("Initial Copies", min_value=1, value=1, step=1)
                submit_book = st.form_submit_button("Save Book")
                
                if submit_book:
                    if not title or not author:
                        st.warning("Please fill in both title and author.")
                    else:
                        try:
                            conn = get_connection()
                            cursor = conn.cursor()
                            insert_q = """
                                INSERT INTO books (title, author, total_copies, available_copies)
                                VALUES (%s, %s, %s, %s)
                            """
                            cursor.execute(insert_q, (title, author, copies, copies))
                            conn.commit()
                            cursor.close()
                            conn.close()
                            st.success(f"Book '{title}' by {author} successfully added!")
                        except Exception as e:
                            st.error(f"Error saving book: {e}")
                            
        # 3. Active Issues & Returns (Admin Handles Returns)
        elif menu == "📥 Active Issues & Returns":
            st.subheader("Active Book Issues & Process Returns")
            st.caption("When admin marks a book as returned, setting `return_date` fires the MySQL trigger `after_book_return` to restore available copies.")
            
            try:
                conn = get_connection()
                active_query = """
                    SELECT 
                        i.issue_id,
                        i.book_id,
                        b.title AS book_title,
                        b.author,
                        i.student_name,
                        i.issue_date,
                        u.username AS issued_by_user
                    FROM issues i
                    JOIN books b ON i.book_id = b.book_id
                    JOIN users u ON i.issued_by = u.user_id
                    WHERE i.return_date IS NULL
                    ORDER BY i.issue_id DESC
                """
                active_df = pd.read_sql(active_query, conn)
                conn.close()
                
                if active_df.empty:
                    st.info("No active issues currently. All books are returned!")
                else:
                    st.dataframe(
                        active_df[["issue_id", "book_title", "author", "student_name", "issue_date", "issued_by_user"]],
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    st.divider()
                    st.subheader("Process Book Return")
                    
                    issue_options = {
                        f"Issue #{row['issue_id']} - '{row['book_title']}' (Student: {row['student_name']}, Issued by: {row['issued_by_user']})": row['issue_id']
                        for _, row in active_df.iterrows()
                    }
                    
                    with st.form("return_book_form"):
                        selected_issue_label = st.selectbox("Select Active Issue to Return", list(issue_options.keys()))
                        return_btn = st.form_submit_button("Mark as Returned Today")
                        
                        if return_btn:
                            issue_id = issue_options[selected_issue_label]
                            try:
                                conn = get_connection()
                                cursor = conn.cursor()
                                
                                # Updating return_date fires trigger: after_book_return
                                update_return_q = "UPDATE issues SET return_date = CURDATE() WHERE issue_id = %s AND return_date IS NULL"
                                cursor.execute(update_return_q, (issue_id,))
                                conn.commit()
                                cursor.close()
                                conn.close()
                                
                                st.success("✅ Book marked as returned! Available copies restored via database trigger.")
                                st.toast("Book returned successfully!", icon="📥")
                                time.sleep(2.5)
                                st.rerun()

                            except mysql.connector.Error as err:
                                st.error(f"Database error during return: {err}")
                            except Exception as e:
                                st.error(f"Error: {e}")
            except Exception as e:
                st.error(f"Error loading active issues: {e}")

        # 4. All Issue History
        elif menu == "📑 All Issue History":
            st.subheader("System Issue Records")
            try:
                conn = get_connection()
                history_query = """
                    SELECT 
                        i.issue_id,
                        b.title AS book_title,
                        i.student_name,
                        u.username AS issued_by_user,
                        i.issue_date,
                        i.return_date,
                        CASE 
                            WHEN i.return_date IS NULL THEN 'Issued (Active)'
                            ELSE 'Returned'
                        END AS status
                    FROM issues i
                    JOIN books b ON i.book_id = b.book_id
                    JOIN users u ON i.issued_by = u.user_id
                    ORDER BY i.issue_id DESC
                """
                history_df = pd.read_sql(history_query, conn)
                conn.close()
                
                if history_df.empty:
                    st.info("No issue records found.")
                else:
                    st.dataframe(history_df, use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"Error loading history: {e}")

    # ----------------------------------------------------
    # ISSUER VIEWS
    # ----------------------------------------------------
    else:
        st.markdown(f'<div class="main-header">Issuer Portal - {menu}</div>', unsafe_allow_html=True)
        
        # 1. Issue Book (Uses Stored Procedure: issue_book)
        if menu == "📤 Issue Book":
            st.subheader("Issue a Book to a Student")
            st.caption("Transactions are executed securely via MySQL Stored Procedure `issue_book`.")
            
            try:
                conn = get_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT book_id, title, author, available_copies FROM books WHERE available_copies > 0 ORDER BY title ASC")
                available_books = cursor.fetchall()
                cursor.close()
                conn.close()
                
                if not available_books:
                    st.warning("⚠️ No books are currently available for issue.")
                else:
                    book_dict = {
                        f"{b['title']} (by {b['author']}) - [Copies Available: {b['available_copies']}]": b['book_id']
                        for b in available_books
                    }
                    
                    with st.form("issue_book_form"):
                        selected_book_label = st.selectbox("Select Book", list(book_dict.keys()))
                        student_name = st.text_input("Student Name").strip()
                        issue_btn = st.form_submit_button("Confirm Issue")
                        
                        if issue_btn:
                            if not student_name:
                                st.warning("Please enter the student's name.")
                            else:
                                book_id = book_dict[selected_book_label]
                                try:
                                    conn = get_connection()
                                    cursor = conn.cursor()
                                    
                                    # Call the stored procedure: issue_book(p_book_id, p_student_name, p_issued_by)
                                    cursor.callproc("issue_book", [book_id, student_name, st.session_state.user_id])
                                    conn.commit()
                                    cursor.close()
                                    conn.close()
                                    
                                    st.success(f"✅ Successfully issued '{selected_book_label.split(' (by')[0]}' to {student_name}!")
                                    st.toast(f"Book issued to {student_name}!", icon="📚")
                                    time.sleep(2.5)
                                    st.rerun()

                                except mysql.connector.Error as err:
                                    st.error(f"Failed to issue book: {err.msg if hasattr(err, 'msg') else err}")
                                except Exception as e:
                                    st.error(f"An unexpected error occurred: {e}")
            except Exception as e:
                st.error(f"Error fetching books: {e}")

        # 2. Browse Books
        elif menu == "📖 Browse Books":
            st.subheader("Library Book Catalog")
            try:
                conn = get_connection()
                query = "SELECT book_id, title, author, total_copies, available_copies FROM books ORDER BY title ASC"
                df = pd.read_sql(query, conn)
                conn.close()
                st.dataframe(df, use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"Error fetching catalog: {e}")

        # 3. My Issued History
        elif menu == "📑 My Issued History":
            st.subheader("Books Issued By You")
            try:
                conn = get_connection()
                query = """
                    SELECT 
                        i.issue_id,
                        b.title AS book_title,
                        i.student_name,
                        i.issue_date,
                        i.return_date,
                        CASE 
                            WHEN i.return_date IS NULL THEN 'Issued (Active)'
                            ELSE 'Returned'
                        END AS status
                    FROM issues i
                    JOIN books b ON i.book_id = b.book_id
                    WHERE i.issued_by = %s
                    ORDER BY i.issue_id DESC
                """
                history_df = pd.read_sql(query, conn, params=(st.session_state.user_id,))
                conn.close()
                
                if history_df.empty:
                    st.info("You haven't issued any books yet.")
                else:
                    st.dataframe(history_df, use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"Error loading issue history: {e}")
