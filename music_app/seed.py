import random
from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import Base, User, Track, Upload, DATABASE_URL

fake = Faker()

# --- Setup DB connection ---
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed():
    db = SessionLocal()

    # --- Helper functions ---
    def get_or_create_user(email):
        user = db.query(User).filter_by(email=email).first()
        if not user:
            user = User(email=email)
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    def get_or_create_track(title, artist, album=None, provider=None, external_id=None, duration=None):
        track = db.query(Track).filter_by(title=title, artist=artist).first()
        if not track:
            track = Track(
                title=title,
                artist=artist,
                album=album,
                provider=provider,
                external_id=external_id,
                duration=duration
            )
            db.add(track)
            db.commit()
            db.refresh(track)
        return track

    def get_or_create_upload(filename, user_id):
        upload = db.query(Upload).filter_by(filename=filename, user_id=user_id).first()
        if not upload:
            upload = Upload(filename=filename, user_id=user_id)
            db.add(upload)
            db.commit()
            db.refresh(upload)
        return upload

    # --- Fixed seed data ---
    alice = get_or_create_user("alice@example.com")
    bob = get_or_create_user("bob@example.com")

    track1 = get_or_create_track("Song A", "Artist A", "Album A", "spotify", "12345", 210)
    track2 = get_or_create_track("Song B", "Artist B", "Album B", "apple", "67890", 180)

    get_or_create_upload("demo1.mp3", alice.id)
    get_or_create_upload("demo2.mp3", bob.id)

    # --- Random users ---
    for _ in range(10):
        email = fake.unique.email()
        get_or_create_user(email)

    # --- Random tracks ---
    providers = ["spotify", "apple", "soundcloud"]
    for _ in range(15):
        title = fake.sentence(nb_words=3).replace(".", "")
        artist = fake.name()
        album = fake.word().capitalize()
        provider = random.choice(providers)
        external_id = str(fake.uuid4())
        duration = random.randint(120, 360)  # 2–6 minutes
        get_or_create_track(title, artist, album, provider, external_id, duration)

    # --- Random uploads ---
    users = db.query(User).all()
    for _ in range(10):
        user = random.choice(users)
        filename = fake.file_name(extension="mp3")
        get_or_create_upload(filename, user.id)

    print("✅ Database seeded with demo + random data!")

if __name__ == "__main__":
    seed()
