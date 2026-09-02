import requests
import json
from typing import Dict, List, Optional
from datetime import datetime

class SMSService:
    def __init__(self, provider: str = "twilio", api_key: str = "", api_secret: str = "", 
                 from_number: str = ""):
        self.provider = provider
        self.api_key = api_key
        self.api_secret = api_secret
        self.from_number = from_number
        
        self.message_templates = {
            "new_complaint": (
                "NEW COMPLAINT #{complaint_id}\n"
                "Priority: {priority_tier}\n"
                "Category: {category}\n"
                "Location: {location}\n"
                "Description: {description}\n"
                "Danger Score: {danger_score}/1.0\n"
                "Assigned: {assigned_to}\n"
                "Please respond immediately."
            ),
            "urgent_alert": (
                "URGENT ALERT #{complaint_id}\n"
                "Critical emergency detected!\n"
                "Category: {category}\n"
                "Location: {location}\n"
                "Children at risk: {has_children}\n"
                "IMMEDIATE ACTION REQUIRED"
            ),
            "assignment_update": (
                "COMPLAINT ASSIGNED #{complaint_id}\n"
                "You have been assigned complaint #{complaint_id}\n"
                "Category: {category}\n"
                "Priority: {priority_tier}\n"
                "Location: {location}\n"
                "Please acknowledge within 1 hour."
            ),
            "verification_request": (
                "VERIFICATION NEEDED #{complaint_id}\n"
                "Complaint #{complaint_id} needs verification.\n"
                "Please upload 'after' photo to confirm fix.\n"
                "Current status: {status}"
            ),
            "status_update": (
                "STATUS UPDATE #{complaint_id}\n"
                "Complaint status changed to: {status}\n"
                "Updated by: {updated_by}\n"
                "Notes: {notes}"
            ),
            "superior_notification": (
                "ADMIN ALERT - Complaint #{complaint_id}\n"
                "High priority complaint requires oversight.\n"
                "Category: {category}\n"
                "Priority: {priority_tier}\n"
                "Danger Score: {danger_score}/1.0\n"
                "Assigned to: {assigned_to}"
            )
        }
    
    def send_sms(self, to_number: str, message: str) -> Dict:
        if self.provider == "twilio":
            return self._send_twilio(to_number, message)
        elif self.provider == "textlocal":
            return self._send_textlocal(to_number, message)
        elif self.provider == "console":
            return self._send_console(to_number, message)
        else:
            return {"status": "error", "message": f"Unknown provider: {self.provider}"}
    
    def _send_twilio(self, to_number: str, message: str) -> Dict:
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.api_key}/Messages.json"
            
            data = {
                "From": self.from_number,
                "To": to_number,
                "Body": message
            }
            
            response = requests.post(
                url,
                data=data,
                auth=(self.api_key, self.api_secret),
                timeout=10
            )
            
            if response.status_code == 201:
                return {"status": "sent", "message_id": response.json().get("sid")}
            else:
                return {"status": "error", "message": response.text}
        
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _send_textlocal(self, to_number: str, message: str) -> Dict:
        try:
            url = "https://api.textlocal.in/send/"
            
            data = {
                "apikey": self.api_key,
                "numbers": to_number,
                "message": message,
                "sender": self.from_number or "TXTLCL"
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    return {"status": "sent", "batch_id": result.get("batch_id")}
                else:
                    return {"status": "error", "message": result.get("message")}
            else:
                return {"status": "error", "message": response.text}
        
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _send_console(self, to_number: str, message: str) -> Dict:
        print(f"\n{'='*60}")
        print(f"SMS TO: {to_number}")
        print(f"MESSAGE:\n{message}")
        print(f"{'='*60}\n")
        return {"status": "console_output", "message": "Printed to console"}
    
    def send_complaint_notification(self, complaint_id: int, complaint_data: Dict, 
                                   priority_data: Dict, targets: List[Dict]) -> List[Dict]:
        results = []
        
        for target in targets:
            template = "new_complaint"
            if priority_data.get("priority_tier") == "critical":
                template = "urgent_alert"
            
            message = self.message_templates[template].format(
                complaint_id=complaint_id,
                priority_tier=priority_data.get("priority_tier", "unknown"),
                category=complaint_data.get("category", "unknown"),
                location=f"{complaint_data.get('village', '')}, {complaint_data.get('city', '')}",
                description=complaint_data.get("complaint_text", "")[:100],
                danger_score=priority_data.get("final_score", 0),
                assigned_to=priority_data.get("assigned_official", {}).get("name", "Unassigned"),
                has_children="YES" if complaint_data.get("has_children_vulnerability") else "No"
            )
            
            sms_result = self.send_sms(target["phone"], message)
            
            results.append({
                "target": target,
                "message": message,
                "result": sms_result,
                "timestamp": datetime.now().isoformat()
            })
        
        return results
    
    def send_assignment_sms(self, official: Dict, complaint_id: int, 
                           complaint_data: Dict, priority_data: Dict) -> Dict:
        message = self.message_templates["assignment_update"].format(
            complaint_id=complaint_id,
            category=complaint_data.get("category", "unknown"),
            priority_tier=priority_data.get("priority_tier", "unknown"),
            location=f"{complaint_data.get('village', '')}, {complaint_data.get('city', '')}"
        )
        
        return self.send_sms(official["phone"], message)
    
    def send_verification_request_sms(self, complainant_phone: str, 
                                     complaint_id: int, status: str) -> Dict:
        message = self.message_templates["verification_request"].format(
            complaint_id=complaint_id,
            status=status
        )
        
        return self.send_sms(complainant_phone, message)
    
    def send_superior_notification(self, superior: Dict, complaint_id: int,
                                  complaint_data: Dict, priority_data: Dict) -> Dict:
        message = self.message_templates["superior_notification"].format(
            complaint_id=complaint_id,
            category=complaint_data.get("category", "unknown"),
            priority_tier=priority_data.get("priority_tier", "unknown"),
            danger_score=priority_data.get("final_score", 0),
            assigned_to=priority_data.get("assigned_official", {}).get("name", "Unassigned")
        )
        
        return self.send_sms(superior["phone"], message)
