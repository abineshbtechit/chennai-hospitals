import mysql.connector
from mysql.connector import Error
import os
from urllib.parse import urlparse
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# Load .env (if present) so local DB config can be set globally
load_dotenv()


def read_env(*names, default=None):
    for name in names:
        value = os.getenv(name)
        if value not in (None, ""):
            return value
    return default


def read_int_env(*names, default=3306):
    value = read_env(*names, default=str(default))
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def read_db_config():
    database_url = read_env('DATABASE_URL')
    if database_url:
        parsed = urlparse(database_url)
        return {
            'host': parsed.hostname or 'localhost',
            'port': parsed.port or 3306,
            'user': parsed.username or 'root',
            'password': parsed.password or '',
            'database': (parsed.path or '/mediflow_db').lstrip('/') or 'mediflow_db',
        }

    return {
        'host': read_env('MYSQLHOST', 'DB_HOST', default='localhost'),
        'port': read_int_env('MYSQLPORT', 'DB_PORT', default=3306),
        'user': read_env('MYSQLUSER', 'DB_USER', default='root'),
        'password': read_env('MYSQLPASSWORD', 'DB_PASSWORD', default='0402'),
        'database': read_env('MYSQLDATABASE', 'DB_NAME', default='mediflow_db')
    }

# Use root connection config (no database) for initial creation
_db_config = read_db_config()
root_db_config = {
    'host': _db_config['host'],
    'port': _db_config['port'],
    'user': _db_config['user'],
    'password': _db_config['password'],
}

def setup_database():
    try:
        connection = mysql.connector.connect(**root_db_config)
        cursor = connection.cursor()
        
        # Create Database
        db_name = _db_config.get('database', read_env('MYSQLDATABASE', 'DB_NAME', default='mediflow_db'))
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        print(f"✓ Database '{db_name}' checked/created.")
        
        cursor.execute(f"USE {db_name}")
        
        # 1. Create Tables with all required columns
        # Users Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
          id INT AUTO_INCREMENT PRIMARY KEY,
          name VARCHAR(255) NOT NULL,
          phone VARCHAR(15) NOT NULL UNIQUE,
          password VARCHAR(255) NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("✓ Table 'users' checked/created.")

        # Hospitals Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS hospitals (
          id INT AUTO_INCREMENT PRIMARY KEY,
          name VARCHAR(255) NOT NULL,
          location VARCHAR(255) NOT NULL
        )
        """)

        # Doctors Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
          id INT AUTO_INCREMENT PRIMARY KEY,
          name VARCHAR(255) NOT NULL,
          specialization VARCHAR(100) NOT NULL,
          hospital_id INT,
          FOREIGN KEY (hospital_id) REFERENCES hospitals(id)
        )
        """)
        print("✓ Tables 'hospitals' and 'doctors' checked/created.")

        # Queries Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS queries (
          id INT AUTO_INCREMENT PRIMARY KEY,
          name VARCHAR(255) NOT NULL,
          email VARCHAR(255) NOT NULL,
          category VARCHAR(100) NOT NULL,
          message TEXT NOT NULL,
          user_id INT,
          hospital_id INT,
          doctor_id INT,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("✓ Table 'queries' checked/created.")

        # Appointments Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
          id INT AUTO_INCREMENT PRIMARY KEY,
          patient_name VARCHAR(255) NOT NULL,
          specialization VARCHAR(100) NOT NULL,
          appointment_date DATE NOT NULL,
          time_slot VARCHAR(50) NOT NULL,
          notes TEXT,
          user_id INT,
          hospital_id INT,
          doctor_id INT,
          payment_method VARCHAR(50),
          payment_status VARCHAR(50),
          fee DECIMAL(10, 2),
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("✓ Table 'appointments' checked/created.")

        # Patient Records Table (Unified History)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_records (
          id INT AUTO_INCREMENT PRIMARY KEY,
          patient_name VARCHAR(255) NOT NULL,
          doctor_name VARCHAR(255) NOT NULL,
          hospital_name VARCHAR(255) NOT NULL,
          location VARCHAR(255) NOT NULL,
          hospital_id INT NOT NULL,
          description TEXT NOT NULL,
          type VARCHAR(50) NOT NULL,
          payment_method VARCHAR(50),
          payment_status VARCHAR(50),
          fee DECIMAL(10, 2),
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("✓ Table 'patient_records' checked/created.")

        # 2. Migration: Add columns to existing tables if they were created earlier
        migration_statements = [
            "ALTER TABLE patient_records ADD COLUMN doctor_name VARCHAR(255)",
            "ALTER TABLE queries ADD COLUMN user_id INT",
            "ALTER TABLE queries ADD COLUMN hospital_id INT",
            "ALTER TABLE queries ADD COLUMN doctor_id INT",
            "ALTER TABLE appointments ADD COLUMN user_id INT",
            "ALTER TABLE appointments ADD COLUMN hospital_id INT",
            "ALTER TABLE appointments ADD COLUMN doctor_id INT",
            "ALTER TABLE appointments ADD COLUMN payment_method VARCHAR(50)",
            "ALTER TABLE appointments ADD COLUMN payment_status VARCHAR(50)",
            "ALTER TABLE appointments ADD COLUMN fee DECIMAL(10, 2)",
            "ALTER TABLE patient_records ADD COLUMN payment_method VARCHAR(50)",
            "ALTER TABLE patient_records ADD COLUMN payment_status VARCHAR(50)",
            "ALTER TABLE patient_records ADD COLUMN fee DECIMAL(10, 2)"
        ]
        
        for statement in migration_statements:
            try:
                cursor.execute(statement)
                print(f"✓ Migration: {statement}")
            except Error as e:
                # Column might already exist, which is fine
                if e.errno == 1060: # Duplicate column name
                    pass
                else:
                    print(f"Migration Note (safe to ignore if column exists): {e}")

        # 3. Seed initial data
        cursor.execute("SELECT COUNT(*) FROM hospitals")
        if cursor.fetchone()[0] == 0:
            hospitals_data = [
                ("City Care Hospital", "Downtown"),
                ("Metro General", "Westside"),
                ("Apollo Speciality", "Central"),
                ("Main Square Clinic", "Eastside"),
                ("St. Mary's Medical Center", "North Valley"),
                ("Oakwood General Hospital", "South Shore"),
                ("Green Valley Clinic", "Green Valley"),
                ("Sunrise Children's Hospital", "Eastside"),
                ("Pacific Heart Institute", "Harbor District"),
                ("North Star Orthopedics", "North Valley"),
                ("Lakeside Wellness Center", "South Shore"),
                ("Royal Park Hospital", "Central")
            ]
            cursor.executemany("INSERT INTO hospitals (name, location) VALUES (%s, %s)", hospitals_data)
            
            cursor.execute("SELECT id FROM hospitals")
            h_ids = [row[0] for row in cursor.fetchall()]
            
            doctors_data = [
                # Hospital 1
                ("Dr. Smith", "Cardiology", h_ids[0]),
                ("Dr. Wilson", "Neurology", h_ids[0]),
                ("Dr. Miller", "General Surgery", h_ids[0]),
                # Hospital 2
                ("Dr. Adams", "Dermatology", h_ids[1]),
                ("Dr. Taylor", "Orthopedics", h_ids[1]),
                ("Dr. Anderson", "ENT", h_ids[1]),
                # Hospital 3
                ("Dr. Brown", "Pediatrics", h_ids[2]),
                ("Dr. Thomas", "Internal Medicine", h_ids[2]),
                # Hospital 4
                ("Dr. Garcia", "General Health", h_ids[3]),
                ("Dr. Rodriguez", "Gastroenterology", h_ids[3]),
                # Hospital 5
                ("Dr. Martinez", "Psychiatry", h_ids[4]),
                ("Dr. Hernandez", "Oncology", h_ids[4]),
                # Hospital 6
                ("Dr. Lopez", "Urology", h_ids[5]),
                ("Dr. Gonzalez", "Ophthalmology", h_ids[5]),
                # Hospital 7
                ("Dr. Perez", "Gynecology", h_ids[6]),
                # Hospital 8
                ("Dr. Clark", "Pediatrics", h_ids[7]),
                ("Dr. Lewis", "Child Psychology", h_ids[7]),
                # Hospital 9
                ("Dr. Walker", "Cardiology", h_ids[8]),
                ("Dr. Young", "Cardiovascular Surgery", h_ids[8]),
                # Hospital 10
                ("Dr. Hall", "Orthopedics", h_ids[9]),
                ("Dr. Allen", "Sports Medicine", h_ids[9]),
                # Hospital 11
                ("Dr. Wright", "Physiotherapy", h_ids[10]),
                # Hospital 12
                ("Dr. King", "Endocrinology", h_ids[11]),
                ("Dr. Scott", "Rheumatology", h_ids[11])
            ]
            cursor.executemany("INSERT INTO doctors (name, specialization, hospital_id) VALUES (%s, %s, %s)", doctors_data)
            print("✓ Seeded sample hospitals and doctors data.")

        connection.commit()
        # Seed a demo user if none exists
        cursor.execute("SELECT COUNT(*) FROM users")
        try:
            user_count = cursor.fetchone()[0]
        except Exception:
            user_count = 0

        if user_count == 0:
            demo_pass = generate_password_hash('password123')
            cursor.execute("INSERT INTO users (name, phone, password) VALUES (%s, %s, %s)", ("Demo User", "9999999999", demo_pass))
            print("✓ Seeded demo user (phone: 9999999999 / password: password123)")

        connection.commit()
        print("\nAll systems ready! Run 'python app.py' to start the backend.")

    except Error as e:
        print(f"Database Error: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    # Optional: USER requested to ensure the database is updated.
    # We will run the setup.
    setup_database()
