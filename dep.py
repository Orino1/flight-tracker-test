from fastapi import Depends, Header, HTTPException
from .db import get_session, User
from sqlmodel import Session

from firebase_admin import auth


# TODO: re-name this
def get_current_user(session: Session = Depends(get_session), authorization: str | None = Header(default=None)) -> User:
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            decoded_token = auth.verify_id_token(token)
            uid = decoded_token["uid"]
            email = decoded_token.get("email")
            sign_in_provider = decoded_token.get("firebase", {}).get("sign_in_provider")
            is_anonymous = sign_in_provider == "anonymous"

            # fetch user using uuid
            user = session.get(User, uid)

            # we have our user
            if user:
                if user.anonymous and is_anonymous:
                    # simply just return the actual user as he is a guest
                    return user
                elif not user.anonymous and not is_anonymous:
                    # if the actual user is not anonymms in token and is not anonymms in teh actual db -> means that the user is registered and no need for update
                    return user
                elif user.anonymous and not is_anonymous:
                    # if user is not anonymos in token and anonymos in db -> that means we need to actually update our shit
                    user.email = email
                    user.anonymous = False
                    session.add(user)
                    session.commit()
                    session.refresh(user)
                    return user
                else:
                    raise HTTPException(status_code=401, detail="Something is wrong")
            else:
                # -> we simply create a user and return it -> based on if its annonymos or not
                if is_anonymous:
                    new_user = User(
                        id=uid,
                    )
                else:
                    new_user = User(
                        id=uid,
                        email=email,
                        anonymous=False
                    )
                session.add(new_user)
                session.commit()
                session.refresh(new_user)
                return new_user
        except Exception:
            raise HTTPException(status_code=401, detail="Authorization required")
    else:
        raise HTTPException(status_code=401, detail="Authorization required")