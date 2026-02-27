from fastapi import FastAPI
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func
import enum
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import or_
app = FastAPI()

# SQLite database
DATABASE_URL = "sqlite:///./contacts.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Enum for primary / secondary
class LinkPrecedence(str, enum.Enum):
    primary = "primary"
    secondary = "secondary"

# Contact table
class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    phoneNumber = Column(String, nullable=True)
    email = Column(String, nullable=True)
    linkedId = Column(Integer, nullable=True)
    linkPrecedence = Column(Enum(LinkPrecedence), nullable=False)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())
    deletedAt = Column(DateTime(timezone=True), nullable=True)

# Create table automatically
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Database connected and server running"}

# Request schema
class IdentifyRequest(BaseModel):
    email: Optional[str] = None
    phoneNumber: Optional[str] = None


@app.post("/identify")
def identify(payload: IdentifyRequest):

    if not payload.email and not payload.phoneNumber:
        raise HTTPException(status_code=400, detail="Provide email or phoneNumber")

    db = SessionLocal()

    # Step 1: Find any contact matching email OR phone
    existing_contacts = db.query(Contact).filter(
        or_(
            Contact.email == payload.email,
            Contact.phoneNumber == payload.phoneNumber
        )
    ).all()

    # If nothing exists → create new primary
    if len(existing_contacts) == 0:
        new_contact = Contact(
            email=payload.email,
            phoneNumber=payload.phoneNumber,
            linkPrecedence=LinkPrecedence.primary
        )
        db.add(new_contact)
        db.commit()
        db.refresh(new_contact)

        return {
            "contact": {
                "primaryContatctId": new_contact.id,
                "emails": [payload.email] if payload.email else [],
                "phoneNumbers": [payload.phoneNumber] if payload.phoneNumber else [],
                "secondaryContactIds": []
            }
        }

    # Step 2: Get the true primary
    first = existing_contacts[0]

    if first.linkPrecedence == LinkPrecedence.primary:
        primary = first
    else:
        primary = db.query(Contact).filter(
            Contact.id == first.linkedId
        ).first()

    # Step 3: Get full group
    group = db.query(Contact).filter(
        or_(
            Contact.id == primary.id,
            Contact.linkedId == primary.id
        )
    ).all()

    emails = set([c.email for c in group if c.email])
    phones = set([c.phoneNumber for c in group if c.phoneNumber])

    # Step 4: Create secondary if new info
    if (payload.email and payload.email not in emails) or \
       (payload.phoneNumber and payload.phoneNumber not in phones):

        new_secondary = Contact(
            email=payload.email,
            phoneNumber=payload.phoneNumber,
            linkedId=primary.id,
            linkPrecedence=LinkPrecedence.secondary
        )

        db.add(new_secondary)
        db.commit()
        db.refresh(new_secondary)

        group.append(new_secondary)
        emails.add(payload.email)
        phones.add(payload.phoneNumber)

    secondary_ids = [
        c.id for c in group if c.linkPrecedence == LinkPrecedence.secondary
    ]

    return {
        "contact": {
            "primaryContatctId": primary.id,
            "emails": list(emails),
            "phoneNumbers": list(phones),
            "secondaryContactIds": secondary_ids
        }
    }