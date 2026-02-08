# Gettings started
## Test It Out
find your ip address
```
ip a
```
Create P1
```
python3 main.py
```
Create P2 on a different port
```
PORT=8001 python3 main.py
```
on P1, Connect to P2
```
chat 'ip address from above'
```
you will be prompted from their port. enter 8001.
Then send them a message
```
send 'test message'
```

# Sequence Diagrams:
## Full Registration
```mermaid
sequenceDiagram
    P1->>P2: REGISTRATION_MESSAGE
    P2->>P1: REGISTRATION_MESSAGE
    P1->>P2: ACK_SUCCESS
```
## Half Registration
```mermaid
sequenceDiagram
    P1->>P2: ACK_UNREGISTERED
    P2->>P1: REGISTRATION_MESSAGE
    P1->>P2: ACK_SUCCESS
```
## Example interaction
```mermaid
sequenceDiagram
    User->>P1: Chat 'host' 'port'
    alt First interaction between P1 and P2
        P1->>P2: REGISTRATION_MESSAGE
        P2->>P2: Create Client Object
        P2->>P1: REGISTRATION_MESSAGE
        P1->>P1: Create Client Object
        P1->>P2: ACK_SUCCESS
    end
    loop read messages
        P1->>P1: Display messages from P2's client obj messages
    end
    P1->>P2: TEXT_MESSAGE
    alt P2 restarted and forgot P2
        P2->>P1: ACK_UNREGISTERED
        P1->>P2: REGISTRATION_MESSAGE
        P2->>P1: ACK_SUCCESS
    end
    alt P1 send malformed packet
        P2->>P1: ACK_INVALID
    end
    P2->>P1: ACK_SUCCESS
    P2->>P2: Save message
    P2->>P1: TEXT_MESSAGE
    P1->>P2: ACK_SUCCESS
    P1->>P1: 'read message' loop displays message
```
# Packet Diagrams
## Text Message Packet
```mermaid
packet
title Text Message Packet
+16: "Message ID"
+16: "Message Length"
32-63: "Message (variable length)"
```
## Registration Packet
```mermaid
packet
title Registration Packet
+16: "Message ID"
+16: "Port"
+16: "pub_key Length"
+16: "pub_key (variable length)"
```
## Ack Packet
```mermaid
packet
title Ack Packet
+16: "Message ID"
+16: "Ack ID"
```




TODO:
- have to change registration to send pubkey and listening port

Known Problems:
- An random empheral port is used to register new peers. This could cause problems on networks with blocked ports.
- does not handle if the host changes their port. Will cause a name conflict with the existing host:port if you try to register a new one.