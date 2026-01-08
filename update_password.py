"""
Script para actualizar la contraseña del admin con hash correcto
"""
import os
import psycopg2
import bcrypt
from dotenv import load_dotenv

load_dotenv()

def update_admin_password():
    database_url = os.getenv('DATABASE_URL')
    
    # Generar hash correcto
    password = 'admin123'.encode('utf-8')
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password, salt).decode('utf-8')
    
    print(f"Nuevo hash: {password_hash}")
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE usuarios 
            SET password_hash = %s 
            WHERE email = 'admin@ecomove.com'
        """, (password_hash,))
        
        conn.commit()
        print("✅ Contraseña del admin actualizada correctamente")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    update_admin_password()
