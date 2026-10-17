"""
Syncora AI - SMS & Phone Number OTP Verification Service
Implements real SMS delivery via Twilio / Fast2SMS, rate limiting,
attempt bounding, secure hashing, and honest developer sandbox disclosures.
"""

import os
import secrets
import hashlib
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import httpx
from fastapi import HTTPException
from config import settings
from database import get_db_connection

logger = logging.getLogger("sms_service")

class SMSService:
    _rate_limit_records: Dict[str, list] = {}

    @staticmethod
    def normalize_phone_number(phone: str, default_country_code: str = "+91") -> str:
        """
        Normalizes a phone number to standard E.164-like format.
        Defaults to India (+91) if no country code is supplied.
        """
        clean = re.sub(r"[^\d+]", "", phone.strip())
        if not clean:
            raise HTTPException(status_code=400, detail="Invalid phone number format.")
        
        if not clean.startswith("+"):
            if default_country_code.startswith("+"):
                clean = f"{default_country_code}{clean.lstrip('0')}"
            else:
                clean = f"+{default_country_code}{clean.lstrip('0')}"
        
        # Basic validation: standard phone numbers are 10-15 digits
        digits_only = re.sub(r"\D", "", clean)
        if len(digits_only) < 10 or len(digits_only) > 15:
            raise HTTPException(status_code=400, detail="Phone number must contain between 10 and 15 digits.")

        return clean

    @classmethod
    def _check_rate_limit(cls, identifier: str, max_requests: int = 3, window_seconds: int = 600):
        """Prevents OTP spam: max 3 requests per 10 minutes."""
        now = datetime.utcnow().timestamp()
        if identifier not in cls._rate_limit_records:
            cls._rate_limit_records[identifier] = []
        cls._rate_limit_records[identifier] = [
            t for t in cls._rate_limit_records[identifier] if now - t < window_seconds
        ]
        if len(cls._rate_limit_records[identifier]) >= max_requests:
            remaining_cooldown = int(window_seconds - (now - cls._rate_limit_records[identifier][0]))
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: Too many OTP requests. Please try again in {remaining_cooldown} seconds."
            )
        cls._rate_limit_records[identifier].append(now)

    @staticmethod
    def _hash_otp(otp: str, phone: str) -> str:
        """Computes SHA-256 hash with salt for secure storage."""
        salt = f"{phone}:{settings.JWT_SECRET}"
        return hashlib.sha256(f"{salt}:{otp}".encode("utf-8")).hexdigest()

    @classmethod
    async def _send_via_twilio(cls, phone_number: str, otp_code: str) -> bool:
        """Dispatches real SMS using Twilio REST API."""
        sid = settings.TWILIO_ACCOUNT_SID
        token = settings.TWILIO_AUTH_TOKEN
        from_num = settings.TWILIO_PHONE_NUMBER

        if not sid or not token or not from_num:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Twilio credentials not configured. Please set TWILIO_ACCOUNT_SID, "
                    "TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER in backend/.env"
                )
            )

        url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
        body = f"[Syncora AI] Your verification code is: {otp_code}. Valid for 5 minutes. Do not share this code."
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                url,
                data={"To": phone_number, "From": from_num, "Body": body},
                auth=(sid, token)
            )
            if res.status_code in (200, 201):
                return True
            else:
                logger.error(f"Twilio API error {res.status_code}: {res.text}")
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to deliver SMS via Twilio provider: {res.text[:120]}"
                )

    @classmethod
    async def _send_via_fast2sms(cls, phone_number: str, otp_code: str) -> bool:
        """Dispatches SMS using Fast2SMS API (common in India)."""
        api_key = settings.FAST2SMS_API_KEY
        if not api_key:
            raise HTTPException(
                status_code=503,
                detail="Fast2SMS API Key not configured. Please set FAST2SMS_API_KEY in backend/.env"
            )

        # Fast2SMS requires 10-digit Indian numbers without +91
        clean_num = phone_number.replace("+91", "").strip()
        url = "https://www.fast2sms.com/dev/bulkV2"
        headers = {"authorization": api_key}
        payload = {
            "variables_values": otp_code,
            "route": "otp",
            "numbers": clean_num
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(url, headers=headers, data=payload)
            if res.status_code == 200:
                data = res.json()
                if data.get("return"):
                    return True
            raise HTTPException(status_code=502, detail=f"Fast2SMS error: {res.text[:120]}")

    @classmethod
    async def request_otp(cls, member_id: str, phone_number: str, country_code: str = "+91") -> Dict[str, Any]:
        """
        Generates and dispatches a 6-digit OTP to the specified phone number.
        Enforces rate limiting, invalidates prior OTPs, and saves the hash.
        """
        normalized_phone = cls.normalize_phone_number(phone_number, country_code)
        cls._check_rate_limit(f"{member_id}:{normalized_phone}")

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if phone is already verified by another member
        cursor.execute(
            "SELECT id, name FROM members WHERE phone_number = ? AND is_phone_verified = 1 AND id != ?",
            (normalized_phone, member_id)
        )
        conflicting = cursor.fetchone()
        if conflicting:
            conn.close()
            raise HTTPException(
                status_code=409,
                detail=f"This phone number is already verified and linked to another account ({conflicting['name']})."
            )

        # Generate cryptographic 6-digit OTP
        otp_code = f"{secrets.randbelow(900000) + 100000}"
        otp_hash = cls._hash_otp(otp_code, normalized_phone)

        now = datetime.utcnow()
        expires_at = (now + timedelta(seconds=300)).isoformat()
        now_str = now.isoformat()
        verification_id = f"otp-{int(now.timestamp())}-{secrets.token_hex(4)}"

        # Invalidate old unused OTPs for this member and phone
        cursor.execute(
            "UPDATE phone_verifications SET verified = 2 WHERE member_id = ? AND verified = 0",
            (member_id,)
        )

        cursor.execute("""
            INSERT INTO phone_verifications (
                id, member_id, phone_number, otp_hash, attempts, expires_at, verified, created_at
            ) VALUES (?, ?, ?, ?, 0, ?, 0, ?)
        """, (verification_id, member_id, normalized_phone, otp_hash, expires_at, now_str))

        conn.commit()
        conn.close()

        provider = settings.SMS_PROVIDER.lower()
        is_demo_sandbox = False
        sandbox_otp = None

        if provider == "twilio":
            if not settings.TWILIO_ACCOUNT_SID:
                raise HTTPException(
                    status_code=503,
                    detail="Twilio credentials not configured in backend/.env. Please configure TWILIO_ACCOUNT_SID."
                )
            await cls._send_via_twilio(normalized_phone, otp_code)
            message = f"OTP sent via Twilio SMS to {normalized_phone}."

        elif provider == "fast2sms":
            if not settings.FAST2SMS_API_KEY:
                raise HTTPException(
                    status_code=503,
                    detail="Fast2SMS credentials not configured in backend/.env. Please configure FAST2SMS_API_KEY."
                )
            await cls._send_via_fast2sms(normalized_phone, otp_code)
            message = f"OTP sent via Fast2SMS to {normalized_phone}."

        else:
            # "dev" sandbox provider: Honest development sandbox disclosure
            is_demo_sandbox = True
            sandbox_otp = otp_code
            logger.info(f"[SMS Sandbox -> {normalized_phone}]: Your Syncora AI verification OTP is: {otp_code}")
            message = (
                f"Development Sandbox: OTP generated for {normalized_phone}. "
                "Configure Twilio credentials in backend/.env for live cellular SMS delivery."
            )

        return {
            "success": True,
            "phoneNumber": normalized_phone,
            "message": message,
            "expiresInSeconds": 300,
            "provider": provider,
            "isDemoSandbox": is_demo_sandbox,
            "sandboxOtp": sandbox_otp
        }

    @classmethod
    async def verify_otp(cls, member_id: str, phone_number: str, submitted_otp: str) -> Dict[str, Any]:
        """
        Validates the submitted OTP against the stored SHA-256 hash.
        Limits incorrect attempts to 3 and checks expiration.
        On success, marks member as verified.
        """
        normalized_phone = cls.normalize_phone_number(phone_number)
        submitted_clean = submitted_otp.strip()

        if len(submitted_clean) != 6 or not submitted_clean.isdigit():
            raise HTTPException(status_code=400, detail="OTP must be a 6-digit numeric code.")

        conn = get_db_connection()
        cursor = conn.cursor()
        now_str = datetime.utcnow().isoformat()

        # Find active verification record
        cursor.execute("""
            SELECT * FROM phone_verifications 
            WHERE member_id = ? AND phone_number = ? AND verified = 0
            ORDER BY created_at DESC LIMIT 1
        """, (member_id, normalized_phone))
        record = cursor.fetchone()

        if not record:
            conn.close()
            raise HTTPException(
                status_code=404,
                detail="No pending verification request found for this phone number. Please request a new OTP."
            )

        # Check expiration
        if record["expires_at"] < now_str:
            cursor.execute("UPDATE phone_verifications SET verified = 2 WHERE id = ?", (record["id"],))
            conn.commit()
            conn.close()
            raise HTTPException(status_code=400, detail="OTP has expired. Please request a fresh code.")

        # Check attempt limits (max 3)
        attempts = record["attempts"]
        if attempts >= 3:
            cursor.execute("UPDATE phone_verifications SET verified = 2 WHERE id = ?", (record["id"],))
            conn.commit()
            conn.close()
            raise HTTPException(
                status_code=429,
                detail="Too many incorrect attempts. This OTP has been invalidated. Please request a new OTP."
            )

        # Compare hash
        expected_hash = record["otp_hash"]
        actual_hash = cls._hash_otp(submitted_clean, normalized_phone)

        if actual_hash != expected_hash:
            cursor.execute(
                "UPDATE phone_verifications SET attempts = attempts + 1 WHERE id = ?",
                (record["id"],)
            )
            conn.commit()
            remaining = 2 - attempts
            conn.close()
            raise HTTPException(
                status_code=400,
                detail=f"Incorrect OTP. {remaining} attempt(s) remaining before invalidation."
            )

        # OTP is valid! Mark verification as complete
        cursor.execute("""
            UPDATE phone_verifications 
            SET verified = 1, verified_at = ?
            WHERE id = ?
        """, (now_str, record["id"]))

        # Update member profile in database
        cursor.execute("""
            UPDATE members 
            SET phone_number = ?, is_phone_verified = 1, phone_verified_at = ?
            WHERE id = ?
        """, (normalized_phone, now_str, member_id))

        conn.commit()
        conn.close()

        logger.info(f"Phone number {normalized_phone} successfully verified for member {member_id}.")

        return {
            "success": True,
            "verified": True,
            "phoneNumber": normalized_phone,
            "message": "Phone number successfully verified!",
            "verifiedAt": now_str
        }

    @classmethod
    def change_phone_number(cls, member_id: str, new_phone: Optional[str] = None) -> Dict[str, Any]:
        """
        Clears the verified status when changing phone number,
        requiring fresh re-verification.
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE members 
            SET phone_number = ?, is_phone_verified = 0, phone_verified_at = NULL
            WHERE id = ?
        """, (new_phone, member_id))

        # Invalidate old verification records
        cursor.execute(
            "UPDATE phone_verifications SET verified = 2 WHERE member_id = ? AND verified = 0",
            (member_id,)
        )

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "Phone number cleared. Please verify your new phone number."
        }

    @classmethod
    def get_status(cls, member_id: str) -> Dict[str, Any]:
        """Returns verification status and configured provider."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT phone_number, is_phone_verified, phone_verified_at FROM members WHERE id = ?", (member_id,))
        row = cursor.fetchone()
        conn.close()

        provider = settings.SMS_PROVIDER.lower()
        configured = True
        if provider == "twilio" and not settings.TWILIO_ACCOUNT_SID:
            configured = False
        elif provider == "fast2sms" and not settings.FAST2SMS_API_KEY:
            configured = False

        if row:
            return {
                "phoneNumber": row["phone_number"],
                "isVerified": bool(row["is_phone_verified"]),
                "verifiedAt": row["phone_verified_at"],
                "provider": provider,
                "providerConfigured": configured
            }

        return {
            "phoneNumber": None,
            "isVerified": False,
            "verifiedAt": None,
            "provider": provider,
            "providerConfigured": configured
        }
