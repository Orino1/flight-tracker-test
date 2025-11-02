from fastapi import FastAPI, Depends, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from .db import User, get_session
from .dep import get_current_user
from sqlmodel import Session, select
import firebase_admin
from firebase_admin import credentials, messaging

# firebase config
cred = credentials.Certificate("./serviceAccountKey.json")
firebase_admin.initialize_app(cred)

app = FastAPI()

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# for users ------------------------
# this is used as if a user opened app and tried to request a flight ect -> for now on appear of main view we ping this route to mimic a real intarction with backend
# in main app there is no login/signup routes -> we just hold our routes behind get_current_user ( wich will make sure to handle creating guest/registred users )
@app.get("/users/me/hello")
def hello(user: User = Depends(get_current_user)):
    print("--------------------------")
    print(f"id (auth token): {user.id}")
    print(f"email: {user.email}")
    print(f"fcm_token: {user.fcm_token}")
    print(f"anonymous: {user.anonymous}")
    print("--------------------------")
    return "hello"

# this is used for refresh ( and also initial fcm_token registration )
@app.get("/users/me/fcm-token/refresh")
def refresh_fcm_token(user: User = Depends(get_current_user), x_fcm_token: str = Header(...), session: Session = Depends(get_session)):
    if not x_fcm_token:
        raise HTTPException(status_code=401, detail="FCM token required")

    user.fcm_token = x_fcm_token
    user.active_token = True

    session.add(user)
    session.commit()

    return {"detail": "FCM token refreshed successfully"}





# for admin ------------------------

@app.get("/users/")
def read_all_users(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return users

@app.get("/users/{user_id}/notify")
def notify_user_via_push_notification(user_id: str, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if not user.active_token or user.fcm_token == "":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User have no active active_token")

    # we send a notification from here and be done with it
    message = messaging.Message(
        notification=messaging.Notification(
            title="Title",
            body="Body"
        ),
        token=user.fcm_token
    )
    messaging.send(message)

    return {"detail": "User notified successfully"}