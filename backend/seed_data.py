"""
TalkTribe Database Seeder
Fills real, realistic language exchange data:
- Predefined Languages (English, Spanish, French, German, Japanese, Hindi, Mandarin, Portuguese, Italian, Korean, Russian, Arabic)
- Predefined Interests (20 topics)
- 10 Realistic Learner Users + Profiles + UserLanguages + UserInterests
"""

import asyncio
from sqlalchemy import select, text
from app.infrastructure.database.session import AsyncSessionLocal
from app.domains.auth.infrastructure.user_model import User
from app.domains.auth.infrastructure.token_model import RefreshToken  # noqa: F401
from app.domains.auth.infrastructure.otp_model import Otp  # noqa: F401
from app.domains.auth.domain.enums import AccountStatus, UserRole
from app.infrastructure.security.password import hash_password
from app.domains.profile.infrastructure.profile_model import Profile
from app.domains.languages.infrastructure.language_model import Language
from app.domains.profile.infrastructure.user_language_model import UserLanguage
from app.domains.profile.infrastructure.interest_model import Interest
from app.domains.profile.infrastructure.user_interest_model import UserInterest

LANGUAGES_DATA = [
    {"name": "English", "code": "en"},
    {"name": "Spanish", "code": "es"},
    {"name": "French", "code": "fr"},
    {"name": "German", "code": "de"},
    {"name": "Japanese", "code": "ja"},
    {"name": "Hindi", "code": "hi"},
    {"name": "Mandarin", "code": "zh"},
    {"name": "Portuguese", "code": "pt"},
    {"name": "Italian", "code": "it"},
    {"name": "Korean", "code": "ko"},
    {"name": "Russian", "code": "ru"},
    {"name": "Arabic", "code": "ar"},
]

INTERESTS_DATA = [
    "Art", "Books", "Business", "Cooking", "Fashion", "Fitness",
    "Gaming", "Movies", "Music", "Nature", "Science", "Sports",
    "Technology", "Travel", "Photography", "Coding", "Startups",
    "History", "Design", "Philosophy"
]

USERS_DATA = [
    {
        "username": "elena_r",
        "email": "elena@talktribe.com",
        "phone_number": "+79161234567",
        "full_name": "Elena Rostova",
        "bio": "Software developer in Moscow. Passionate about AI, open-source and indie games. Looking to improve conversational English for work and travel.",
        "profession": "Software Engineer",
        "location": "Moscow, Russia",
        "native": "Russian",
        "learning_level": "B2",
        "interests": ["Coding", "Technology", "Gaming", "Music", "Books"],
    },
    {
        "username": "marco_it",
        "email": "marco@talktribe.com",
        "phone_number": "+39061234567",
        "full_name": "Marco Rossi",
        "bio": "UI/UX designer based in Rome. Love typography, good espresso, cinema and exploring historic cities. Happy to practice English and share Italian culture!",
        "profession": "UX Designer",
        "location": "Rome, Italy",
        "native": "Italian",
        "learning_level": "B1",
        "interests": ["Design", "Art", "Movies", "Cooking", "Travel"],
    },
    {
        "username": "yuki_t",
        "email": "yuki@talktribe.com",
        "phone_number": "+81901234567",
        "full_name": "Yuki Tanaka",
        "bio": "Tech product manager in Tokyo. Big fan of anime, photography and street food. Practicing daily spoken English for international team meetings.",
        "profession": "Product Manager",
        "location": "Tokyo, Japan",
        "native": "Japanese",
        "learning_level": "B2",
        "interests": ["Technology", "Photography", "Travel", "Gaming", "Startups"],
    },
    {
        "username": "sophie_m",
        "email": "sophie@talktribe.com",
        "phone_number": "+33141234567",
        "full_name": "Sophie Martin",
        "bio": "Architect from Paris interested in sustainable urban design, classic literature and watercolor painting. Looking for fluent conversation partners.",
        "profession": "Architect",
        "location": "Paris, France",
        "native": "French",
        "learning_level": "C1",
        "interests": ["Art", "Design", "Books", "Philosophy", "Travel"],
    },
    {
        "username": "carlos_m",
        "email": "carlos@talktribe.com",
        "phone_number": "+34911234567",
        "full_name": "Carlos Mendoza",
        "bio": "Marketing director in Madrid. Huge football fan, foodie and avid traveler. Eager to gain fluency and confidence in English conversations.",
        "profession": "Marketing Director",
        "location": "Madrid, Spain",
        "native": "Spanish",
        "learning_level": "B1",
        "interests": ["Sports", "Business", "Cooking", "Travel", "Movies"],
    },
    {
        "username": "priya_s",
        "email": "priya@talktribe.com",
        "phone_number": "+919876543210",
        "full_name": "Priya Sharma",
        "bio": "Data scientist in Bengaluru working on machine learning and NLP. Love reading sci-fi, hiking and practicing spoken English nuances.",
        "profession": "Data Scientist",
        "location": "Bengaluru, India",
        "native": "Hindi",
        "learning_level": "C1",
        "interests": ["Technology", "Science", "Books", "Fitness", "Coding"],
    },
    {
        "username": "lucas_s",
        "email": "lucas@talktribe.com",
        "phone_number": "+55119123456",
        "full_name": "Lucas Silva",
        "bio": "Graphic designer and illustrator from Sao Paulo. Love music production, cycling and sharing Brazilian culture with fellow learners.",
        "profession": "Graphic Designer",
        "location": "Sao Paulo, Brazil",
        "native": "Portuguese",
        "learning_level": "B2",
        "interests": ["Music", "Art", "Fitness", "Nature", "Design"],
    },
    {
        "username": "hanna_w",
        "email": "hanna@talktribe.com",
        "phone_number": "+49301234567",
        "full_name": "Hanna Weber",
        "bio": "Medical student in Berlin. Passionate about healthcare innovation, trail running and classical music. Want to improve English for medical research.",
        "profession": "Medical Student",
        "location": "Berlin, Germany",
        "native": "German",
        "learning_level": "B2",
        "interests": ["Science", "Fitness", "Music", "Nature", "Books"],
    },
    {
        "username": "omar_m",
        "email": "omar@talktribe.com",
        "phone_number": "+97150123456",
        "full_name": "Omar Mansoor",
        "bio": "Financial analyst in Dubai. Interested in fintech, world economics and desert camping. Practicing business and casual English conversation.",
        "profession": "Financial Analyst",
        "location": "Dubai, UAE",
        "native": "Arabic",
        "learning_level": "B2",
        "interests": ["Business", "Startups", "Travel", "Technology", "Fitness"],
    },
    {
        "username": "mei_c",
        "email": "mei@talktribe.com",
        "phone_number": "+88691234567",
        "full_name": "Mei Chen",
        "bio": "Commercial photographer in Taipei. Love capturing candid street life, specialty coffee and indie films. Looking for friendly language partners!",
        "profession": "Photographer",
        "location": "Taipei, Taiwan",
        "native": "Mandarin",
        "learning_level": "B1",
        "interests": ["Photography", "Art", "Movies", "Travel", "Cooking"],
    },
]

async def seed_all():
    print("[*] Starting database seed...")
    async with AsyncSessionLocal() as session:
        # 1. Seed Languages
        print("[*] Seeding languages...")
        lang_map = {}
        for l in LANGUAGES_DATA:
            res = await session.execute(select(Language).where(Language.name == l["name"]))
            existing = res.scalar_one_or_none()
            if not existing:
                existing = Language(name=l["name"], code=l["code"])
                session.add(existing)
                await session.flush()
            lang_map[l["name"]] = existing.id
        await session.commit()
        print(f"[+] Languages ready: {len(lang_map)} languages.")

        # 2. Seed Predefined Interests
        print("[*] Seeding interests...")
        interest_map = {}
        for name in INTERESTS_DATA:
            res = await session.execute(select(Interest).where(Interest.name == name))
            existing = res.scalar_one_or_none()
            if not existing:
                existing = Interest(name=name, is_predefined=True, is_active=True)
                session.add(existing)
                await session.flush()
            interest_map[name] = existing.id
        await session.commit()
        print(f"[+] Interests ready: {len(interest_map)} interests.")

        # 3. Seed Users & Profiles
        print("[*] Seeding realistic learner users...")
        english_id = lang_map.get("English")
        default_pwd = hash_password("TalkTribe123!")

        seeded_count = 0
        for u in USERS_DATA:
            res = await session.execute(select(User).where(User.username == u["username"]))
            existing_user = res.scalar_one_or_none()

            if not existing_user:
                existing_user = User(
                    username=u["username"],
                    email=u["email"],
                    phone_number=u["phone_number"],
                    password=default_pwd,
                    full_name=u["full_name"],
                    is_active=True,
                    role=UserRole.USER,
                    account_status=AccountStatus.ACTIVE,
                )
                session.add(existing_user)
                await session.flush()
                seeded_count += 1
            else:
                existing_user.account_status = AccountStatus.ACTIVE
                existing_user.is_active = True
                await session.flush()

            # Profile
            res_p = await session.execute(select(Profile).where(Profile.user_id == existing_user.id))
            prof = res_p.scalar_one_or_none()
            if not prof:
                prof = Profile(
                    user_id=existing_user.id,
                    bio=u["bio"],
                    profession=u["profession"],
                    location=u["location"],
                )
                session.add(prof)
            else:
                prof.bio = u["bio"]
                prof.profession = u["profession"]
                prof.location = u["location"]
            await session.flush()

            # User Languages: 1 NATIVE and 1 LEARNING (English)
            native_id = lang_map.get(u["native"])
            if native_id:
                res_nl = await session.execute(
                    select(UserLanguage).where(
                        UserLanguage.user_id == existing_user.id,
                        UserLanguage.role == "NATIVE",
                    )
                )
                nl = res_nl.scalar_one_or_none()
                if not nl:
                    session.add(UserLanguage(user_id=existing_user.id, language_id=native_id, role="NATIVE"))
                else:
                    nl.language_id = native_id

            if english_id:
                res_ll = await session.execute(
                    select(UserLanguage).where(
                        UserLanguage.user_id == existing_user.id,
                        UserLanguage.role == "LEARNING",
                    )
                )
                ll = res_ll.scalar_one_or_none()
                if not ll:
                    session.add(UserLanguage(
                        user_id=existing_user.id,
                        language_id=english_id,
                        role="LEARNING",
                        proficiency=u["learning_level"],
                    ))
                else:
                    ll.language_id = english_id
                    ll.proficiency = u["learning_level"]
            await session.flush()

            # User Interests
            for int_name in u["interests"]:
                int_id = interest_map.get(int_name)
                if int_id:
                    res_ui = await session.execute(
                        select(UserInterest).where(
                            UserInterest.user_id == existing_user.id,
                            UserInterest.interest_id == int_id,
                        )
                    )
                    if not res_ui.scalar_one_or_none():
                        session.add(UserInterest(user_id=existing_user.id, interest_id=int_id))
            await session.flush()

        await session.commit()
        print(f"[+] Successfully seeded/updated {len(USERS_DATA)} active user profiles!")
        print("[+] Test password for all seeded users: TalkTribe123!")

if __name__ == "__main__":
    asyncio.run(seed_all())
