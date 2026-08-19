clear# TalkTribe - System Architecture

## 1. Overall System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  React + TypeScript (Vite)                               │  │
│  │  - Zustand (State Management)                            │  │
│  │  - React Query (Server State)                            │  │
│  │  - Tailwind CSS (Styling)                                │  │
│  │  - WebRTC (P2P Audio/Video)                              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↕ HTTP/WS
┌─────────────────────────────────────────────────────────────────┐
│                         API GATEWAY LAYER                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Nginx (Reverse Proxy) - Optional in production          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FastAPI Application                                     │  │
│  │  ┌────────────┬────────────┬─────────────────────────┐  │  │
│  │  │ REST API   │ WebSocket  │  Background Tasks       │  │  │
│  │  │ Endpoints  │ Manager    │  (Celery - Future)      │  │  │
│  │  └────────────┴────────────┴─────────────────────────┘  │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────┐    │  │
│  │  │  Core Modules                                  │    │  │
│  │  │  - Auth & JWT                                  │    │  │
│  │  │  - User Management                             │    │  │
│  │  │  - Matching Engine                             │    │  │
│  │  │  - Chat Service                                │    │  │
│  │  │  - WebRTC Signaling                            │    │  │
│  │  │  - Notification Service                        │    │  │
│  │  └────────────────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                    ↕                           ↕
┌─────────────────────────────┐   ┌───────────────────────────┐
│     DATA LAYER              │   │    CACHE LAYER            │
│  ┌────────────────────────┐ │   │  ┌─────────────────────┐ │
│  │  PostgreSQL            │ │   │  │  Redis              │ │
│  │  - User Data           │ │   │  │  - Sessions         │ │
│  │  - Messages            │ │   │  │  - Online Users     │ │
│  │  - Relationships       │ │   │  │  - WebSocket Rooms  │ │
│  │  - Language Prefs      │ │   │  │  - Rate Limiting    │ │
│  └────────────────────────┘ │   │  │  - Pub/Sub          │ │
└─────────────────────────────┘   │  └─────────────────────┘ │
                                  └───────────────────────────┘
```

## 2. Folder Structure

### Backend Structure
```
backend/
├── alembic/                    # Database migrations
│   ├── versions/
│   └── env.py
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI application entry point
│   ├── config.py              # Configuration management
│   ├── database.py            # Database connection & session
│   ├── dependencies.py        # FastAPI dependencies
│   │
│   ├── core/                  # Core functionality
│   │   ├── __init__.py
│   │   ├── security.py        # Password hashing, JWT
│   │   ├── redis.py           # Redis client
│   │   └── exceptions.py      # Custom exceptions
│   │
│   ├── models/                # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── language.py
│   │   ├── friendship.py
│   │   ├── message.py
│   │   └── call.py
│   │
│   ├── schemas/               # Pydantic schemas (request/response)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── auth.py
│   │   ├── language.py
│   │   ├── friendship.py
│   │   ├── message.py
│   │   └── call.py
│   │
│   ├── api/                   # API routes
│   │   ├── __init__.py
│   │   ├── deps.py            # Route dependencies
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py        # Login, register, refresh
│   │       ├── users.py       # User CRUD, profile
│   │       ├── languages.py   # Language endpoints
│   │       ├── matching.py    # Partner matching
│   │       ├── friendships.py # Friend requests
│   │       ├── messages.py    # Message history
│   │       └── calls.py       # Call history
│   │
│   ├── services/              # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── matching_service.py
│   │   ├── friendship_service.py
│   │   ├── message_service.py
│   │   └── call_service.py
│   │
│   ├── websocket/             # WebSocket functionality
│   │   ├── __init__.py
│   │   ├── manager.py         # WebSocket connection manager
│   │   ├── handlers.py        # Message handlers
│   │   └── signaling.py       # WebRTC signaling
│   │
│   └── utils/                 # Utility functions
│       ├── __init__.py
│       ├── validators.py
│       └── helpers.py
│
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── conftest.py           # Pytest fixtures
│   ├── test_auth.py
│   ├── test_users.py
│   ├── test_matching.py
│   ├── test_friendship.py
│   ├── test_messages.py
│   └── test_websocket.py
│
├── .env.example              # Environment variables template
├── .gitignore
├── alembic.ini               # Alembic configuration
├── pyproject.toml            # Poetry dependencies
├── pytest.ini                # Pytest configuration
├── Dockerfile
└── README.md
```

### Frontend Structure
```
frontend/
├── public/
│   └── vite.svg
├── src/
│   ├── assets/               # Images, fonts, etc.
│   │
│   ├── components/           # Reusable components
│   │   ├── common/
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Modal.tsx
│   │   │   └── Loading.tsx
│   │   ├── layout/
│   │   │   ├── Navbar.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Footer.tsx
│   │   └── features/
│   │       ├── auth/
│   │       ├── profile/
│   │       ├── chat/
│   │       └── call/
│   │
│   ├── pages/                # Route components
│   │   ├── Home.tsx
│   │   ├── Login.tsx
│   │   ├── Register.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Profile.tsx
│   │   ├── FindPartners.tsx
│   │   ├── Messages.tsx
│   │   └── VoiceCall.tsx
│   │
│   ├── hooks/                # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── useWebSocket.ts
│   │   ├── useWebRTC.ts
│   │   └── useChat.ts
│   │
│   ├── store/                # Zustand stores
│   │   ├── authStore.ts
│   │   ├── userStore.ts
│   │   ├── chatStore.ts
│   │   └── callStore.ts
│   │
│   ├── services/             # API client
│   │   ├── api.ts            # Axios instance
│   │   ├── authService.ts
│   │   ├── userService.ts
│   │   ├── matchingService.ts
│   │   ├── friendshipService.ts
│   │   └── messageService.ts
│   │
│   ├── types/                # TypeScript types
│   │   ├── user.ts
│   │   ├── message.ts
│   │   ├── friendship.ts
│   │   └── call.ts
│   │
│   ├── utils/                # Utility functions
│   │   ├── validators.ts
│   │   └── formatters.ts
│   │
│   ├── config/               # Configuration
│   │   └── constants.ts
│   │
│   ├── App.tsx              # Root component
│   ├── main.tsx             # Entry point
│   └── router.tsx           # React Router setup
│
├── .env.example
├── .gitignore
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── Dockerfile
└── README.md
```

## 3. Database Schema

### Entity Relationship Diagram

```
┌─────────────────────────┐
│        users            │
├─────────────────────────┤
│ id (PK)                 │
│ email (unique)          │
│ username (unique)       │
│ password_hash           │
│ first_name              │
│ last_name               │
│ bio                     │
│ avatar_url              │
│ country                 │
│ timezone                │
│ is_active               │
│ is_verified             │
│ created_at              │
│ updated_at              │
└─────────────────────────┘
         │ 1
         │
         │ *
┌─────────────────────────┐
│   user_languages        │
├─────────────────────────┤
│ id (PK)                 │
│ user_id (FK)            │
│ language_id (FK)        │
│ proficiency_level       │
│ is_native               │
│ is_learning             │
│ created_at              │
└─────────────────────────┘
         │ *
         │
         │ 1
┌─────────────────────────┐
│      languages          │
├─────────────────────────┤
│ id (PK)                 │
│ code (unique)           │
│ name                    │
│ native_name             │
│ created_at              │
└─────────────────────────┘


┌─────────────────────────┐
│     friendships         │
├─────────────────────────┤
│ id (PK)                 │
│ requester_id (FK)       │────┐
│ addressee_id (FK)       │────┼──→ users.id
│ status                  │    │
│ created_at              │    │
│ updated_at              │    │
└─────────────────────────┘    │
                               │
                               │
┌─────────────────────────┐    │
│       messages          │    │
├─────────────────────────┤    │
│ id (PK)                 │    │
│ sender_id (FK)          │────┤
│ receiver_id (FK)        │────┘
│ content                 │
│ is_read                 │
│ read_at                 │
│ created_at              │
└─────────────────────────┘


┌─────────────────────────┐
│         calls           │
├─────────────────────────┤
│ id (PK)                 │
│ caller_id (FK)          │────┐
│ callee_id (FK)          │────┼──→ users.id
│ call_type               │    │
│ status                  │    │
│ started_at              │    │
│ ended_at                │    │
│ duration_seconds        │    │
│ created_at              │    │
└─────────────────────────┘    │
                               │
                               │
┌─────────────────────────┐    │
│   refresh_tokens        │    │
├─────────────────────────┤    │
│ id (PK)                 │    │
│ user_id (FK)            │────┘
│ token (unique)          │ 
│ expires_at              │
│ revoked                 │
│ created_at              │
└─────────────────────────┘
```

### Detailed Table Definitions

#### users
```sql
CREATE TABLE users ( 
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    bio TEXT,
    avatar_url VARCHAR(500),
    country VARCHAR(100),
    timezone VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_is_active ON users(is_active);
```

#### languages
```sql
CREATE TABLE languages (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,  -- ISO 639-1 code (e.g., 'en', 'es')
    name VARCHAR(100) NOT NULL,         -- English name
    native_name VARCHAR(100),           -- Native name
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_languages_code ON languages(code);
```

#### user_languages
```sql
CREATE TYPE proficiency_level AS ENUM ('beginner', 'elementary', 'intermediate', 'advanced', 'fluent', 'native');

CREATE TABLE user_languages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    language_id INTEGER NOT NULL REFERENCES languages(id) ON DELETE CASCADE,
    proficiency_level proficiency_level NOT NULL,
    is_native BOOLEAN DEFAULT FALSE,
    is_learning BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, language_id)
);

CREATE INDEX idx_user_languages_user ON user_languages(user_id);
CREATE INDEX idx_user_languages_language ON user_languages(language_id);
CREATE INDEX idx_user_languages_native ON user_languages(is_native);
CREATE INDEX idx_user_languages_learning ON user_languages(is_learning);
```

#### friendships
```sql
CREATE TYPE friendship_status AS ENUM ('pending', 'accepted', 'rejected', 'blocked');

CREATE TABLE friendships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requester_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    addressee_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status friendship_status DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(requester_id, addressee_id),
    CHECK (requester_id != addressee_id)
);

CREATE INDEX idx_friendships_requester ON friendships(requester_id);
CREATE INDEX idx_friendships_addressee ON friendships(addressee_id);
CREATE INDEX idx_friendships_status ON friendships(status);
```

#### messages
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sender_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    receiver_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    CHECK (sender_id != receiver_id)
);

CREATE INDEX idx_messages_sender ON messages(sender_id);
CREATE INDEX idx_messages_receiver ON messages(receiver_id);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX idx_messages_conversation ON messages(sender_id, receiver_id, created_at DESC);
```

#### calls
```sql
CREATE TYPE call_type AS ENUM ('voice', 'video');
CREATE TYPE call_status AS ENUM ('initiated', 'ringing', 'answered', 'ended', 'missed', 'rejected');

CREATE TABLE calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    caller_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    callee_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    call_type call_type NOT NULL,
    status call_status DEFAULT 'initiated',
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    duration_seconds INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    CHECK (caller_id != callee_id)
);

CREATE INDEX idx_calls_caller ON calls(caller_id);
CREATE INDEX idx_calls_callee ON calls(callee_id);
CREATE INDEX idx_calls_created_at ON calls(created_at DESC);
```

#### refresh_tokens
```sql
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);
```

## 4. API Module Structure

### REST API Endpoints

#### Authentication (`/api/v1/auth`)
- `POST /register` - Register new user
- `POST /login` - Login user (returns access + refresh tokens)
- `POST /refresh` - Refresh access token
- `POST /logout` - Logout user (revoke refresh token)
- `POST /verify-email` - Verify email address
- `POST /forgot-password` - Request password reset
- `POST /reset-password` - Reset password

#### Users (`/api/v1/users`)
- `GET /me` - Get current user profile
- `PUT /me` - Update current user profile
- `GET /me/languages` - Get user's languages
- `POST /me/languages` - Add language to profile
- `PUT /me/languages/{id}` - Update language proficiency
- `DELETE /me/languages/{id}` - Remove language
- `GET /{user_id}` - Get user by ID (public profile)

#### Languages (`/api/v1/languages`)
- `GET /` - List all available languages
- `GET /{language_id}` - Get language by ID

#### Matching (`/api/v1/matching`)
- `GET /partners` - Find language partners (with filters)
- `GET /suggestions` - Get recommended partners

#### Friendships (`/api/v1/friendships`)
- `GET /` - List user's friendships
- `POST /` - Send friend request
- `GET /requests` - List pending friend requests
- `PUT /{friendship_id}/accept` - Accept friend request
- `PUT /{friendship_id}/reject` - Reject friend request
- `DELETE /{friendship_id}` - Remove friendship

#### Messages (`/api/v1/messages`)
- `GET /conversations` - List all conversations
- `GET /conversations/{user_id}` - Get conversation with user
- `GET /conversations/{user_id}/history` - Get message history
- `POST /` - Send message (fallback if WebSocket unavailable)
- `PUT /{message_id}/read` - Mark message as read

#### Calls (`/api/v1/calls`)
- `GET /history` - Get call history
- `GET /{call_id}` - Get call details

### WebSocket Endpoints

#### `/ws/chat` - Real-time messaging
- Connection requires JWT token
- Events:
  - `message.send` - Send message
  - `message.received` - Receive message
  - `message.read` - Mark message as read
  - `typing.start` - User started typing
  - `typing.stop` - User stopped typing
  - `user.online` - User came online
  - `user.offline` - User went offline

#### `/ws/signaling` - WebRTC signaling
- Connection requires JWT token
- Events:
  - `call.initiate` - Initiate call
  - `call.offer` - Send WebRTC offer
  - `call.answer` - Send WebRTC answer
  - `call.ice_candidate` - Exchange ICE candidates
  - `call.accept` - Accept incoming call
  - `call.reject` - Reject incoming call
  - `call.end` - End call

## 5. Authentication Flow

### Registration Flow
```
User → Frontend: Submit registration form
Frontend → Backend: POST /api/v1/auth/register
Backend → Database: Create user record
Backend → Email Service: Send verification email (future)
Backend → Frontend: Return success message
Frontend → User: Show "Check your email" message
```

### Login Flow
```
User → Frontend: Submit login credentials
Frontend → Backend: POST /api/v1/auth/login
Backend → Database: Verify credentials
Backend → Redis: Store session
Backend → Frontend: Return access_token (JWT) + refresh_token
Frontend → LocalStorage: Store tokens
Frontend → Zustand: Update auth state
Frontend → Router: Redirect to dashboard
```

### JWT Structure
```json
{
  "access_token": {
    "type": "access",
    "user_id": "uuid",
    "email": "user@example.com",
    "exp": "timestamp",
    "iat": "timestamp"
  },
  "refresh_token": {
    "type": "refresh",
    "user_id": "uuid",
    "exp": "timestamp",
    "iat": "timestamp",
    "jti": "unique_token_id"
  }
}
```

### Token Refresh Flow
```
Frontend → Backend: Request with expired access_token
Backend → Frontend: Return 401 Unauthorized
Frontend Interceptor → Backend: POST /api/v1/auth/refresh with refresh_token
Backend → Database: Verify refresh_token not revoked
Backend → Frontend: Return new access_token
Frontend → Original Request: Retry with new token
```

### Authorization Middleware
```python
# Dependency injection pattern
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    # Verify JWT
    # Extract user_id
    # Fetch user from database
    # Return user object
```

## 6. WebSocket Architecture

### Connection Management

#### ConnectionManager Class
```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, str] = {}  # user_id -> connection_id
        
    async def connect(self, websocket: WebSocket, user_id: str)
    async def disconnect(self, user_id: str)
    async def send_personal_message(self, message: dict, user_id: str)
    async def broadcast(self, message: dict, user_ids: List[str])
```

### Message Flow

#### Chat Messages
```
User A → Frontend A: Type and send message
Frontend A → WS Client A: Emit 'message.send'
WS Client A → Backend: Send via WebSocket
Backend → Database: Store message
Backend → Redis: Publish to channel
Backend → WS Server: Process message
Backend → Frontend B: Send via WebSocket (if online)
Frontend B → User B: Display message
Frontend B → Backend: Emit 'message.read'
Backend → Database: Update message status
Backend → Frontend A: Notify message delivered
```

#### Online Presence
```
User connects → WebSocket established
Backend → Redis: SADD online_users {user_id}
Backend → Redis: EXPIRE online_users:{user_id} 300
Backend → Friends: Broadcast "user.online" event

Every 60s → Frontend: Send heartbeat
Backend → Redis: Refresh TTL

User disconnects → WebSocket closed
Backend → Redis: SREM online_users {user_id}
Backend → Friends: Broadcast "user.offline" event
```

## 7. WebRTC Signaling Architecture

### Call Initiation Flow

```
Caller                  Signaling Server            Callee
  │                           │                       │
  │ 1. Initiate Call          │                       │
  ├──────────────────────────>│                       │
  │                           │ 2. call.incoming      │
  │                           ├──────────────────────>│
  │                           │                       │
  │                           │ 3. Accept/Reject      │
  │                           │<──────────────────────┤
  │ 4. call.accepted          │                       │
  │<──────────────────────────┤                       │
  │                           │                       │
  │ 5. Create Offer           │                       │
  │ (WebRTC)                  │                       │
  │                           │                       │
  │ 6. Send Offer             │                       │
  ├──────────────────────────>│ 7. Forward Offer     │
  │                           ├──────────────────────>│
  │                           │                       │
  │                           │ 8. Create Answer      │
  │                           │    (WebRTC)           │
  │                           │                       │
  │                           │ 9. Send Answer        │
  │ 10. Forward Answer        │<──────────────────────┤
  │<──────────────────────────┤                       │
  │                           │                       │
  │ 11. ICE Candidates        │                       │
  │<─────────────────────────>│<─────────────────────>│
  │                           │                       │
  │ 12. P2P Connection Established                   │
  │<═════════════════════════════════════════════════>│
  │         Audio/Video Stream (Direct)               │
```

### WebRTC Configuration

#### STUN/TURN Servers
```javascript
const rtcConfiguration = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' },
    // TURN server for production (behind NAT/firewall)
    {
      urls: 'turn:your-turn-server.com:3478',
      username: 'user',
      credential: 'password'
    }
  ]
};
```

### Signaling Messages

#### Call Initiation
```json
{
  "type": "call.initiate",
  "data": {
    "call_id": "uuid",
    "caller_id": "uuid",
    "callee_id": "uuid",
    "call_type": "voice"
  }
}
```

#### WebRTC Offer
```json
{
  "type": "call.offer",
  "data": {
    "call_id": "uuid",
    "sdp": "WebRTC SDP string"
  }
}
```

#### WebRTC Answer
```json
{
  "type": "call.answer",
  "data": {
    "call_id": "uuid",
    "sdp": "WebRTC SDP string"
  }
}
```

#### ICE Candidate
```json
{
  "type": "call.ice_candidate",
  "data": {
    "call_id": "uuid",
    "candidate": "ICE candidate string"
  }
}
```

## 8. Redis Usage

### Use Cases

#### 1. Session Storage
```redis
# Store JWT session
SET session:{user_id} {session_data} EX 3600

# Verify session exists
GET session:{user_id}

# Revoke session
DEL session:{user_id}
```

#### 2. Online Users
```redis
# Add user to online set
SADD online_users {user_id}

# Set expiration (5 minutes)
EXPIRE online_users:{user_id} 300

# Check if user is online
SISMEMBER online_users {user_id}

# Get all online friends
SINTER online_users friends:{user_id}
```

#### 3. WebSocket Connection Mapping
```redis
# Map user to connection ID
HSET ws_connections {user_id} {connection_id}

# Get connection for user
HGET ws_connections {user_id}

# Remove on disconnect
HDEL ws_connections {user_id}
```

#### 4. Pub/Sub for Horizontal Scaling
```redis
# Publish message to channel
PUBLISH chat:{receiver_id} {message_data}

# Subscribe to user's channel
SUBSCRIBE chat:{user_id}
```

#### 5. Rate Limiting
```redis
# Increment API call count
INCR rate_limit:{user_id}:{endpoint}
EXPIRE rate_limit:{user_id}:{endpoint} 60

# Check rate limit
GET rate_limit:{user_id}:{endpoint}
```

#### 6. Typing Indicators
```redis
# User started typing
SETEX typing:{sender_id}:{receiver_id} 5 1

# Check if typing
GET typing:{sender_id}:{receiver_id}
```

#### 7. Call State
```redis
# Store active call
HSET active_calls {call_id} {call_data}
EXPIRE active_calls 3600

# Get call details
HGET active_calls {call_id}

# Remove on call end
HDEL active_calls {call_id}
```

## 9. Docker Architecture

### Service Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│                      (talktribe)                         │
│                                                          │
│  ┌───────────────┐  ┌───────────────┐                  │
│  │   Frontend    │  │    Backend    │                  │
│  │   (React)     │  │   (FastAPI)   │                  │
│  │   Port: 5173  │  │   Port: 8000  │                  │
│  └───────────────┘  └───────────────┘                  │
│          │                   │                           │
│          │                   │                           │
│          │                   ├──────────┐                │
│          │                   │          │                │
│  ┌───────────────┐  ┌───────────────┐  │               │
│  │   PostgreSQL  │  │     Redis     │  │               │
│  │   Port: 5432  │  │   Port: 6379  │  │               │
│  └───────────────┘  └───────────────┘  │               │
│          │                   │          │                │
│          │                   │          │                │
│  ┌──────────────────────────────────┐  │               │
│  │         Volume Mounts             │  │               │
│  │  - postgres_data                  │  │               │
│  │  - redis_data                     │  │               │
│  └──────────────────────────────────┘  │               │
└─────────────────────────────────────────────────────────┘
```

### docker-compose.yml Structure

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_USER: talktribe
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: talktribe_db
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-BASH", "pg_isready -U talktribe"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://talktribe:${DB_PASSWORD}@postgres:5432/talktribe_db
      REDIS_URL: redis://redis:6379/0
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      JWT_ALGORITHM: HS256
      ACCESS_TOKEN_EXPIRE_MINUTES: 30
      REFRESH_TOKEN_EXPIRE_DAYS: 7
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "5173:5173"
    environment:
      VITE_API_URL: http://localhost:8000
      VITE_WS_URL: ws://localhost:8000
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev

volumes:
  postgres_data:
  redis_data:

networks:
  default:
    name: talktribe
```

### Container Images

#### Backend Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run migrations and start server
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Frontend Dockerfile
```dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application
COPY . .

# Expose port
EXPOSE 5173

# Start dev server
CMD ["npm", "run", "dev", "--", "--host"]
```

## 10. Development Milestones

### Phase 1: Foundation (Weeks 1-2)
**Goal**: Set up project structure, authentication, and basic user management

- Milestone 1.1: Project Setup & Infrastructure
- Milestone 1.2: Database Models & Migrations
- Milestone 1.3: Authentication System
- Milestone 1.4: User Profile Management

### Phase 2: Social Features (Weeks 3-4)
**Goal**: Enable users to find partners and connect

- Milestone 2.1: Language Management
- Milestone 2.2: Partner Matching System
- Milestone 2.3: Friendship System
- Milestone 2.4: User Search & Filtering

### Phase 3: Real-time Communication (Weeks 5-6)
**Goal**: Implement real-time chat functionality

- Milestone 3.1: WebSocket Infrastructure
- Milestone 3.2: Real-time Chat
- Milestone 3.3: Message History & Persistence
- Milestone 3.4: Online Presence & Typing Indicators

### Phase 4: Voice Calling (Weeks 7-8)
**Goal**: Implement WebRTC voice calling

- Milestone 4.1: WebRTC Signaling Infrastructure
- Milestone 4.2: Voice Call Implementation
- Milestone 4.3: Call Management (accept/reject/end)
- Milestone 4.4: Call History & Recording Metadata

### Phase 5: Polish & Production (Weeks 9-10)
**Goal**: Testing, optimization, and deployment

- Milestone 5.1: Comprehensive Testing
- Milestone 5.2: Performance Optimization
- Milestone 5.3: Security Hardening
- Milestone 5.4: Production Deployment

### Future Phases
- **Phase 6**: Video Calling
- **Phase 7**: AI Language Learning Features
- **Phase 8**: Mobile App (React Native)
- **Phase 9**: Advanced Features (gamification, streaks, achievements)

---

## Technical Decisions & Rationale

### Why FastAPI?
- Native async support for WebSocket
- Automatic OpenAPI documentation
- Type hints and Pydantic validation
- High performance (comparable to Node.js)
- Modern Python features

### Why PostgreSQL?
- ACID compliance for transactional data
- Complex queries for matching algorithm
- JSON support for flexible data
- Mature ecosystem
- Strong relationship handling

### Why Redis?
- Sub-millisecond latency for session data
- Pub/Sub for WebSocket scaling
- Built-in expiration for rate limiting
- Atomic operations for presence
- Horizontal scaling support

### Why WebRTC?
- P2P communication (lower latency)
- Browser native support
- Industry standard for real-time
- Scales better than server-mediated calls
- Lower infrastructure costs

### Why Docker?
- Consistent development environment
- Easy onboarding for contributors
- Production-like local setup
- Simplified deployment
- Service isolation

---

This architecture is designed for:
- **Scalability**: Can handle thousands of concurrent users
- **Maintainability**: Clear separation of concerns
- **Testability**: Each layer can be tested independently
- **Security**: JWT authentication, input validation, SQL injection prevention
- **Performance**: Redis caching, database indexing, async operations
- **Production-readiness**: Logging, error handling, monitoring hooks

Next step: Review this architecture and let me know if you'd like any modifications before we proceed to detailed milestone planning.
