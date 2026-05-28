import os
import csv
import logging
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import boto3

# הגדרת לוגים
os.makedirs('logs', exist_ok=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S', filename='logs/worker.log', filemode='a')

# הגדרות AWS
S3_BUCKET_NAME = "devops-project-bucket-yahali"
SNS_TOPIC_NAME = "devops-app-alerts"
AWS_REGION = "us-east-1"

# הגדרות חיבור למסד הנתונים מתוך משתני הסביבה
DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER", "dbadmin")
DB_PASS = os.environ.get("DB_PASS", "SuperSecretPassword123!")
DB_NAME = os.environ.get("DB_NAME", "appdb")

def get_db_connection():
    host = DB_HOST.split(':')[0] if DB_HOST else 'localhost'
    return psycopg2.connect(host=host, database=DB_NAME, user=DB_USER, password=DB_PASS)

def generate_report():
    logging.info("Starting daily report generation...")
    if not DB_HOST:
        logging.error("No DB_HOST configured. Cannot generate report.")
        return None
    
    filename = f"/tmp/daily_report_{datetime.now().strftime('%Y%m%d')}.csv"
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # משיכת כל המכונות שנוצרו
        cur.execute('SELECT * FROM machines ORDER BY created_at DESC;')
        machines = cur.fetchall()
        
        # כתיבה לקובץ CSV
        with open(filename, 'w', newline='') as f:
            if machines:
                writer = csv.DictWriter(f, fieldnames=machines[0].keys())
                writer.writeheader()
                writer.writerows(machines)
            else:
                f.write("No machines provisioned yet.\n")
                
        cur.close()
        conn.close()
        logging.info(f"Report generated successfully: {filename}")
        return filename
    except Exception as e:
        logging.error(f"Error generating report: {e}")
        return None

def upload_to_s3(filename):
    s3 = boto3.client('s3', region_name=AWS_REGION)
    object_name = os.path.basename(filename)
    try:
        s3.upload_file(filename, S3_BUCKET_NAME, object_name)
        logging.info(f"Uploaded {object_name} to S3 bucket {S3_BUCKET_NAME}")
        return True
    except Exception as e:
        logging.error(f"Failed to upload to S3: {e}")
        return False

def get_sns_topic_arn(sns_client, topic_name):
    # משיכת ה-ARN המלא של ה-SNS שנוצר ב-Terraform
    topics = sns_client.list_topics()['Topics']
    for topic in topics:
        if topic['TopicArn'].endswith(f":{topic_name}"):
            return topic['TopicArn']
    return None

def send_sns_notification(message):
    sns = boto3.client('sns', region_name=AWS_REGION)
    topic_arn = get_sns_topic_arn(sns, SNS_TOPIC_NAME)
    
    if not topic_arn:
        logging.error(f"SNS Topic '{SNS_TOPIC_NAME}' not found.")
        return
        
    try:
        sns.publish(
            TopicArn=topic_arn,
            Subject="DevOps Infra Report Uploaded",
            Message=message
        )
        logging.info("SNS notification sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send SNS notification: {e}")

if __name__ == "__main__":
    print("Running daily worker job...")
    report_file = generate_report()
    if report_file:
        success = upload_to_s3(report_file)
        if success:
            msg = f"Daily infrastructure report generated and uploaded successfully to S3.\nFile: {os.path.basename(report_file)}"
            send_sns_notification(msg)
            print("Done! Check your email for the SNS alert.")
        else:
            send_sns_notification("Failed to upload daily report to S3.")
    print("Worker job completed.")