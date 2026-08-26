# ADR-006: Use WebRTC for MVP Voice Calls

**Status:** Accepted

## Context

Voice connection is a core TalkTribe MVP capability. Users should be able to speak with automatically paired co-learners and manually call eligible friends.

## Decision

Use **WebRTC** for live voice media.

Voice calling is part of MVP. Video calling is deferred.

## Alternatives Considered

### Media relayed through FastAPI
Rejected because FastAPI should not act as the audio-media transport.

### Third-party full call platform
Not selected as the default architecture because WebRTC provides the core capability with more control and potentially lower cost.

### WebSockets for audio streaming
Rejected because WebSocket is not the appropriate media transport.

## Consequences

### Positive
- Low-latency peer-to-peer audio
- Browser-native technology
- Backend does not need to carry normal media traffic

### Negative
- NAT/firewall traversal requires STUN/TURN
- Call state and signaling must be carefully designed
- Reconnection is more complex than simple REST features

## Rule

WebRTC carries voice media. The backend coordinates authorization, signaling, call state, and TURN/STUN support.
