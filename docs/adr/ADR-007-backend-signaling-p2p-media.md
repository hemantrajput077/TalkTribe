# ADR-007: Backend Handles Signaling, Peers Handle Media

**Status:** Accepted

## Context

WebRTC requires a signaling mechanism for call setup, but does not define one.

## Decision

Use the TalkTribe backend and WebSocket transport for:

- call initiation
- incoming call notification
- accept/reject/cancel/end
- WebRTC offer
- WebRTC answer
- ICE candidate exchange
- authorization of signaling participants

After negotiation, normal audio flows directly between peers or through TURN when direct connectivity fails.

## Alternatives Considered

### Direct client-to-client signaling
Rejected because it would bypass backend authorization and application rules.

### Backend media relay
Rejected as unnecessary for MVP.

## Consequences

### Positive
- Server retains control of call authorization
- Works with existing WebSocket infrastructure
- Media bandwidth stays off the application backend

### Negative
- Backend must track call lifecycle
- Signaling events require strict authorization

## Security Rule

A user may send WebRTC signaling only for an active call in which that authenticated user is a participant.
