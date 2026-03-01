from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.user_models import UserModel, UserProfileModel
from app.models.user import UserCreate, UserLogin, UserResponse, UserProfileUpdate, Token, TokenData
from app.utils.auth import verify_password, get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from datetime import timedelta, datetime
import os
import shutil
import logging
from jose import JWTError, jwt

logger = logging.getLogger(__name__)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = db.query(UserModel).filter(UserModel.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user


# ==================== REGISTER ====================
@router.post("/register", response_model=Token, status_code=201)
def register(req: UserCreate, db: Session = Depends(get_db)):
    email = req.email.lower().strip()
    existing = db.query(UserModel).filter(UserModel.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered. Please sign in.")

    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    hashed = get_password_hash(req.password)
    user = UserModel(
        name=req.name.strip(),
        email=email,
        hashed_password=hashed,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create empty profile
    profile = UserProfileModel(user_id=user.id, full_name=req.name.strip())
    db.add(profile)
    db.commit()

    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}


# ==================== LOGIN ====================
@router.post("/login", response_model=Token)
def login(req: UserLogin, db: Session = Depends(get_db)):
    email = req.email.lower().strip()
    user = db.query(UserModel).filter(UserModel.email == email).first()

    if not user or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}


# ==================== PROFILE ====================
@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == current_user.id).first()
    profile = db.query(UserProfileModel).filter(UserProfileModel.user_id == user.id).first()
    if not profile:
        profile = UserProfileModel(user_id=user.id)
        db.add(profile)
        db.commit()
    return {"id": user.id, "name": user.name, "email": user.email, "created_at": user.created_at, "profile": profile}

@router.put("/profile", response_model=UserResponse)
def update_profile(
    update: UserProfileUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(UserProfileModel).filter(UserProfileModel.user_id == current_user.id).first()
    if not profile:
        profile = UserProfileModel(user_id=current_user.id)
        db.add(profile)

    if update.full_name is not None:
        profile.full_name = update.full_name
    if update.additional_details is not None:
        profile.additional_details = update.additional_details
    if update.linkedin_cookie is not None:
        profile.linkedin_cookie = update.linkedin_cookie
    db.commit()
    db.refresh(profile)

    return {"id": current_user.id, "name": current_user.name, "email": current_user.email,
            "created_at": current_user.created_at, "profile": profile}

@router.post("/profile/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    UPLOAD_DIR = "uploads/resumes"
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    ext = os.path.splitext(file.filename)[1]
    filename = f"{current_user.id}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    profile = db.query(UserProfileModel).filter(UserProfileModel.user_id == current_user.id).first()
    if not profile:
        profile = UserProfileModel(user_id=current_user.id)
        db.add(profile)
    profile.resume_path = filepath
    db.commit()

    return {"message": "Resume uploaded successfully.", "path": filepath}

@router.delete("/account")
def delete_account(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(UserProfileModel).filter(UserProfileModel.user_id == current_user.id).delete()
    db.delete(current_user)
    db.commit()
    return {"message": "Account deleted."}
