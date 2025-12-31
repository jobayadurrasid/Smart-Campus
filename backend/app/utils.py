#/backend/app/utils.py
from deepface import DeepFace
from sqlalchemy.orm import Session
from . import models
import os
import json
from scipy.spatial.distance import cosine

import json
from scipy.spatial.distance import cosine

def check_duplicate_face(image_path: str, db: Session, threshold: float = 0.3) -> bool:
    """
    Check for duplicate face:
    1. First try embedding match (fast).
    2. If a user's embedding is missing, fallback to image-to-image match.
    """
    try:
        # Generate embedding for the new image
        target_repr = DeepFace.represent(
            img_path=image_path,
            model_name="VGG-Face",
            enforce_detection=False
        )[0]["embedding"]

        # Loop through all existing users
        for user in db.query(models.User).all():
            if user.face_embedding:
                # Compare embeddings
                try:
                    stored_repr = json.loads(user.face_embedding)
                    distance = cosine(target_repr, stored_repr)
                    if distance < threshold:
                        print(f"[MATCH] Embedding match with cosine distance: {distance}")
                        return True
                except Exception as e:
                    continue
            else:
                # No embedding stored — fallback to image-to-image comparison
                try:
                    result = DeepFace.verify(
                        img1_path=image_path,
                        img2_path=user.image_path,
                        model_name="VGG-Face",
                        enforce_detection=False,
                        detector_backend="skip"
                    )
                    if result["verified"]:
                        return True
                except Exception as e:
                    continue

    except Exception as e:
        raise e

    return False

def generate_user_id(enrollment_year: int, department_code: str, role: str, db: Session):
    """Generate ID in format: YYYYRRDDDXXX"""
    role_code = {
        "admin": "01",
        "teacher": "02",
        "student": "03"
    }.get(role.lower(), "99")
    
    # Find last user in same department/year/role
    last_user = db.query(models.User).filter(
        models.User.id.like(f"{enrollment_year}{role_code}{department_code}%")
    ).order_by(models.User.id.desc()).first()
    
    seq = int(last_user.id[-3:]) + 1 if last_user else 1
    
    return f"{enrollment_year}{role_code}{department_code}{seq:03d}"

