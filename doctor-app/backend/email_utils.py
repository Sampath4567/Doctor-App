import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import settings
import logging

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, html_body: str):
    """Send an HTML email via SMTP."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
        msg["To"] = to_email

        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())

        logger.info(f"Email sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        # Don't raise — email failure shouldn't block booking


def send_booking_confirmation(
    patient_email: str,
    patient_name: str,
    doctor_name: str,
    specialization: str,
    slot_date: str,
    start_time: str,
    end_time: str,
    reason: str,
):
    subject = f"✅ Appointment Confirmed – {slot_date} at {start_time}"
    html = f"""
    <div style="font-family: 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; background: #f8fafc; padding: 40px 20px;">
      <div style="background: #fff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.07);">
        <div style="background: linear-gradient(135deg, #0f4c81 0%, #1a7fbf 100%); padding: 36px 40px;">
          <h1 style="color: #fff; margin: 0; font-size: 26px; font-weight: 700;">Appointment Confirmed</h1>
          <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0;">DoctorBook – Your health, simplified</p>
        </div>
        <div style="padding: 36px 40px;">
          <p style="font-size: 16px; color: #374151;">Hi <strong>{patient_name}</strong>,</p>
          <p style="color: #6b7280;">Your appointment has been successfully booked. Here are the details:</p>

          <div style="background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 12px; padding: 24px; margin: 24px 0;">
            <table style="width: 100%; border-collapse: collapse;">
              <tr>
                <td style="padding: 8px 0; color: #6b7280; font-size: 14px; width: 40%;">Doctor</td>
                <td style="padding: 8px 0; color: #111827; font-weight: 600;">Dr. {doctor_name}</td>
              </tr>
              <tr>
                <td style="padding: 8px 0; color: #6b7280; font-size: 14px;">Specialization</td>
                <td style="padding: 8px 0; color: #111827; font-weight: 600;">{specialization}</td>
              </tr>
              <tr>
                <td style="padding: 8px 0; color: #6b7280; font-size: 14px;">Date</td>
                <td style="padding: 8px 0; color: #111827; font-weight: 600;">{slot_date}</td>
              </tr>
              <tr>
                <td style="padding: 8px 0; color: #6b7280; font-size: 14px;">Time</td>
                <td style="padding: 8px 0; color: #111827; font-weight: 600;">{start_time} – {end_time}</td>
              </tr>
              {"<tr><td style='padding: 8px 0; color: #6b7280; font-size: 14px;'>Reason</td><td style='padding: 8px 0; color: #111827; font-weight: 600;'>" + reason + "</td></tr>" if reason else ""}
            </table>
          </div>

          <p style="color: #6b7280; font-size: 14px;">Please arrive 10 minutes early. If you need to cancel, please do so at least 2 hours in advance.</p>
          <p style="color: #6b7280; font-size: 14px; margin-top: 24px;">— The DoctorBook Team</p>
        </div>
      </div>
    </div>
    """
    send_email(patient_email, subject, html)


def send_doctor_notification(
    doctor_email: str,
    doctor_name: str,
    patient_name: str,
    patient_phone: str,
    slot_date: str,
    start_time: str,
    end_time: str,
    reason: str,
):
    subject = f"📅 New Appointment Booked – {slot_date} at {start_time}"
    html = f"""
    <div style="font-family: 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; background: #f8fafc; padding: 40px 20px;">
      <div style="background: #fff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.07);">
        <div style="background: linear-gradient(135deg, #064e3b 0%, #059669 100%); padding: 36px 40px;">
          <h1 style="color: #fff; margin: 0; font-size: 26px; font-weight: 700;">New Appointment</h1>
          <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0;">A patient has booked your slot</p>
        </div>
        <div style="padding: 36px 40px;">
          <p style="font-size: 16px; color: #374151;">Hi Dr. <strong>{doctor_name}</strong>,</p>
          <p style="color: #6b7280;">A new appointment has been booked for you:</p>

          <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 12px; padding: 24px; margin: 24px 0;">
            <table style="width: 100%; border-collapse: collapse;">
              <tr>
                <td style="padding: 8px 0; color: #6b7280; font-size: 14px; width: 40%;">Patient</td>
                <td style="padding: 8px 0; color: #111827; font-weight: 600;">{patient_name}</td>
              </tr>
              <tr>
                <td style="padding: 8px 0; color: #6b7280; font-size: 14px;">Phone</td>
                <td style="padding: 8px 0; color: #111827; font-weight: 600;">{patient_phone or "N/A"}</td>
              </tr>
              <tr>
                <td style="padding: 8px 0; color: #6b7280; font-size: 14px;">Date</td>
                <td style="padding: 8px 0; color: #111827; font-weight: 600;">{slot_date}</td>
              </tr>
              <tr>
                <td style="padding: 8px 0; color: #6b7280; font-size: 14px;">Time</td>
                <td style="padding: 8px 0; color: #111827; font-weight: 600;">{start_time} – {end_time}</td>
              </tr>
              {"<tr><td style='padding: 8px 0; color: #6b7280; font-size: 14px;'>Reason</td><td style='padding: 8px 0; color: #111827; font-weight: 600;'>" + reason + "</td></tr>" if reason else ""}
            </table>
          </div>

          <p style="color: #6b7280; font-size: 14px;">— The DoctorBook Team</p>
        </div>
      </div>
    </div>
    """
    send_email(doctor_email, subject, html)


def send_cancellation_email(
    to_email: str,
    recipient_name: str,
    role: str,
    slot_date: str,
    start_time: str,
):
    subject = f"❌ Appointment Cancelled – {slot_date} at {start_time}"
    html = f"""
    <div style="font-family: 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; background: #f8fafc; padding: 40px 20px;">
      <div style="background: #fff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.07);">
        <div style="background: linear-gradient(135deg, #7f1d1d 0%, #ef4444 100%); padding: 36px 40px;">
          <h1 style="color: #fff; margin: 0; font-size: 26px; font-weight: 700;">Appointment Cancelled</h1>
        </div>
        <div style="padding: 36px 40px;">
          <p style="font-size: 16px; color: #374151;">Hi {"Dr. " if role == "doctor" else ""}<strong>{recipient_name}</strong>,</p>
          <p style="color: #6b7280;">The appointment scheduled on <strong>{slot_date}</strong> at <strong>{start_time}</strong> has been cancelled.</p>
          <p style="color: #6b7280; font-size: 14px;">— The DoctorBook Team</p>
        </div>
      </div>
    </div>
    """
    send_email(to_email, subject, html)


def send_prescription_email(
    to_email: str,
    patient_name: str,
    doctor_name: str,
    slot_date: str,
    notes: str,
    medications: str,
):
    subject = f"💊 Prescription Details – Visit on {slot_date}"
    html = f"""
    <div style="font-family: 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; background: #f8fafc; padding: 40px 20px;">
      <div style="background: #fff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.07);">
        <div style="background: linear-gradient(135deg, #0f4c81 0%, #1a7fbf 100%); padding: 36px 40px;">
          <h1 style="color: #fff; margin: 0; font-size: 26px; font-weight: 700;">Prescription & Notes</h1>
          <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0;">Dr. {doctor_name}</p>
        </div>
        <div style="padding: 36px 40px;">
          <p style="font-size: 16px; color: #374151;">Hi <strong>{patient_name}</strong>,</p>
          <p style="color: #6b7280;">Thank you for your visit. Here are your prescription details and doctor's notes:</p>

          <div style="background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 12px; padding: 24px; margin: 24px 0;">
            <h3 style="margin-top: 0; color: #0f4c81;">Medications</h3>
            <p style="white-space: pre-wrap; color: #111827;">{medications}</p>
            
            <hr style="border: 0; border-top: 1px solid #bae6fd; margin: 20px 0;" />
            
            <h3 style="color: #0f4c81;">Doctor's Notes</h3>
            <p style="white-space: pre-wrap; color: #111827;">{notes}</p>
          </div>

          <p style="color: #6b7280; font-size: 14px;">If you have any questions regarding this prescription, please contact the clinic.</p>
          <p style="color: #6b7280; font-size: 14px; margin-top: 24px;">— The DoctorBook Team</p>
        </div>
      </div>
    </div>
    """
    send_email(to_email, subject, html)
