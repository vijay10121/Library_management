
import os
import streamlit as st
import mysql.connector

def get_connection():
    # Use Streamlit Cloud Secrets when deployed.
    # Fall back to .env variables for local development.
    if "mysql" in st.secrets:
        config = st.secrets["mysql"]
        host = config["host"]
        port = int(config["port"])
        user = config["user"]
        password = config["password"]
        database = config["database"]
        ssl_ca = config.get("ssl_ca")
    else:
        from dotenv import load_dotenv
        load_dotenv()

        host = os.getenv("DB_HOST", "localhost")
        port = int(os.getenv("DB_PORT", "3306"))
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        database = os.getenv("DB_NAME", "library_db")
        ssl_ca = os.getenv("DB_SSL_CA")

    connection_args = {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "database": database,
        "connection_timeout": 15,
    }

    if ssl_ca:
        connection_args["ssl_ca"] = ssl_ca
        connection_args["ssl_verify_cert"] = True
    elif host != "localhost" and host != "127.0.0.1":
        raise ValueError("SSL CA certificate is required for remote MySQL.")

    return mysql.connector.connect(**connection_args)
