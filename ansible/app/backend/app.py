from flask import Flask, request, jsonify
from flask_cors import CORS
from pydantic import BaseModel, Field, ValidationError
from src.machine import Machine
import logging
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Setup logging and directories
os.makedirs('logs', exist_ok=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S', filename='logs/provisioning.log', filemode='a')

app = Flask(__name__)
# Enable CORS so your future Frontend UI can send requests here
CORS(app) 

# Database connection settings from environment variables
# אלו משתני הסביבה שהזרקנו פנימה דרך Ansible וה-systemd
DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER", "dbadmin")
DB_PASS = os.environ.get("DB_PASS", "SuperSecretPassword123!")
DB_NAME = os.environ.get("DB_NAME", "appdb")

def get_db_connection():
    # Terraform מחזיר את הכתובת עם הפורט בסוף (endpoint:5432)
    # psycopg2 דורש את ההוסט והפורט בנפרד, אז אנחנו חותכים את הפורט מהמחרוזת
    host = DB_HOST.split(':')[0] if DB_HOST else 'localhost'
    conn = psycopg2.connect(
        host=host,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    return conn

def init_db():
    """Create the machines table if it doesn't exist."""
    try:
        if not DB_HOST:
            logging.warning("DB_HOST is not set. Running in local/test mode without DB.")
            return
            
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS machines (
                id SERIAL PRIMARY KEY,
                instance_id VARCHAR(100) NOT NULL,
                name VARCHAR(100) NOT NULL,
                os_type VARCHAR(50) NOT NULL,
                cpu INTEGER NOT NULL,
                ram INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        conn.commit()
        cur.close()
        conn.close()
        logging.info("Database initialized successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize database: {e}")

# Initialize DB on startup
init_db()

# Keeping your excellent strict validation!
class InstanceConfig(BaseModel):
    name: str = Field(..., min_length=2)
    os: str = Field(..., min_length=2)
    cpu: int = Field(..., gt=0, le=32) 
    ram: int = Field(..., gt=0, le=128)
    provision: bool = False 

@app.route('/api/provision', methods=['POST'])
def provision_machine():
    try:
        # 1. Get the JSON data sent from the Frontend UI
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No JSON payload provided"}), 400
        
        # 2. Validate the input using your Pydantic model
        config = InstanceConfig(**data)
        
        # 3. Create the Machine object
        new_vm = Machine(
            name=config.name, 
            os_type=config.os, 
            cpu=config.cpu, 
            ram=config.ram
        )
        
        # 4. Save to AWS RDS PostgreSQL
        if DB_HOST:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO machines (instance_id, name, os_type, cpu, ram)
                VALUES (%s, %s, %s, %s, %s)
            ''', (new_vm.instance_id, new_vm.name, new_vm.os_type, new_vm.cpu, new_vm.ram))
            conn.commit()
            cur.close()
            conn.close()
            logging.info(f"Machine '{config.name}' saved to RDS database.")
        else:
            logging.warning("DB_HOST missing, skipping DB insertion.")

        # 5. Send a success response back to the UI
        return jsonify({
            "status": "success",
            "message": f"Machine '{config.name}' provisioned and saved to DB successfully!",
            "data": {
                "instance_id": new_vm.instance_id,
                "name": new_vm.name
            }
        }), 201

    except ValidationError as e:
        # Handle Pydantic validation errors nicely
        errors = [{"field": err["loc"][0], "message": err["msg"]} for err in e.errors()]
        logging.error(f"[API] Validation Error: {errors}")
        return jsonify({"status": "error", "message": "Invalid input", "details": errors}), 400
        
    except Exception as e:
        # Catch-all for unexpected server errors
        logging.error(f"[API] Internal Server Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# NEW ROUTE: Retrieve machines from the DB (Requested by Aviad)
@app.route('/api/machines', methods=['GET'])
def get_machines():
    try:
        if not DB_HOST:
            return jsonify({"status": "error", "message": "Database not configured"}), 500
            
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM machines ORDER BY created_at DESC;')
        machines = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify({"status": "success", "data": machines}), 200
        
    except Exception as e:
        logging.error(f"[API] Error fetching machines: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Run the Flask app on port 5001, accessible from any IP
    print("Starting Infra Portal Backend API on http://0.0.0.0:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)