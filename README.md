# Cisco Smart Branch 360

## Project Overview

**Smart Branch 360** is a secure small-office network designed and simulated in **Cisco Packet Tracer**. The project demonstrates VLAN-based network segmentation, inter-VLAN routing, DHCP, DNS reachability, NAT-based internet access, wireless connectivity, ACL-based security, and secure SSH management.

A **Python-based network assurance tool** is also developed to validate the network design and identify common configuration problems from an IP/VLAN plan and/or Cisco `show` command outputs.

The project is designed around the **Cisco Virtual Internship 2026 — Networking + Packet Tracer + Python** SmartBranch 360 problem statement.

---

## Problem Statement

A company is opening a new branch office that requires:

* Wired connectivity for employees
* Secure guest Wi-Fi
* An internal server
* Internet access
* Secure management of network devices
* Network segmentation using VLANs
* A method to automatically identify configuration problems

The goal is to design, configure, test, troubleshoot, and validate the complete branch-office network.

---

# Objectives

The main objectives of Smart Branch 360 are:

1. Design a functional branch-office network in Cisco Packet Tracer.
2. Separate employees, guests, servers, and network management using VLANs.
3. Provide DHCP services for the required VLANs.
4. Enable inter-VLAN routing using router-on-a-stick.
5. Provide DNS reachability and access to the internal server.
6. Provide internet connectivity through NAT.
7. Prevent guest users from accessing internal server and management networks.
8. Allow SSH management only from the Management VLAN.
9. Intentionally introduce network faults and troubleshoot them.
10. Develop a Python tool that identifies likely configuration problems.
11. Demonstrate successful diagnosis, correction, and verification.

---

# Network Architecture

The network contains:

* 1 Router
* 2 Layer-2 Switches
* 1 Wireless Access Point
* 1 Internal Server
* 8+ End Devices
* 1 ISP/Internet Cloud

### Logical Architecture

```text
                         INTERNET
                            |
                       [ ISP / Cloud ]
                            |
                         [ Router ]
                         R1 / Gateway
                            |
                         TRUNK
                            |
                       [ Switch 1 ]
                       /     |      \
                      /      |       \
                 Employee   Server   Management
                    PCs      Server      PC
                      |
                    TRUNK
                      |
                  [ Switch 2 ]
                   /         \
                  /           \
          Employee PCs      Wireless AP
                              |
                         Guest Devices
```

---

# VLAN Design

| VLAN | Name       | Purpose                | Subnet        | Default Gateway |
| ---: | ---------- | ---------------------- | ------------- | --------------- |
|   10 | EMPLOYEE   | Employee wired devices | 10.10.10.0/24 | 10.10.10.1      |
|   20 | GUEST      | Guest wireless devices | 10.10.20.0/24 | 10.10.20.1      |
|   30 | SERVER     | Internal server        | 10.10.30.0/24 | 10.10.30.1      |
|   99 | MANAGEMENT | Network administration | 10.10.99.0/24 | 10.10.99.1      |

Each VLAN uses a separate IP subnet as required by the project specification.

---

# Device Allocation

### VLAN 10 — Employee

Example devices:

* Employee-PC1
* Employee-PC2
* Employee-PC3
* Employee-PC4
* Employee-PC5

These devices receive their IP addresses through DHCP.

### VLAN 20 — Guest

Example devices:

* Guest-Laptop1
* Guest-Laptop2

Guest devices connect through the wireless AP and receive addresses from the Guest DHCP pool.

### VLAN 30 — Server

Example:

* Internal Server

The server provides internal services such as DNS and/or HTTP.

### VLAN 99 — Management

Example:

* Management-PC

Only the Management PC is permitted to establish SSH sessions with network devices.

---

# IP Addressing Plan

```text
VLAN 10
Network:    10.10.10.0/24
Gateway:    10.10.10.1
DHCP Range: 10.10.10.10 - 10.10.10.254

VLAN 20
Network:    10.10.20.0/24
Gateway:    10.10.20.1
DHCP Range: 10.10.20.10 - 10.10.20.254

VLAN 30
Network:    10.10.30.0/24
Gateway:    10.10.30.1
Server:     10.10.30.10

VLAN 99
Network:    10.10.99.0/24
Gateway:    10.10.99.1
Management: 10.10.99.10
```

---

# Core Networking Technologies

## 1. VLANs

Four VLANs are created:

```text
VLAN 10 → Employee
VLAN 20 → Guest
VLAN 30 → Server
VLAN 99 → Management
```

VLANs isolate different categories of users and infrastructure.

---

## 2. Trunking

The connection between the switches and the router uses trunking where multiple VLANs must travel over the same physical link.

The trunk carries:

```text
VLAN 10
VLAN 20
VLAN 30
VLAN 99
```

A missing VLAN from the trunk's allowed VLAN list is intentionally used as one of the troubleshooting scenarios.

---

## 3. Inter-VLAN Routing

The router uses **router-on-a-stick**.

Example subinterfaces:

```text
G0/0.10 → 10.10.10.1
G0/0.20 → 10.10.20.1
G0/0.30 → 10.10.30.1
G0/0.99 → 10.10.99.1
```

This allows the router to route traffic between VLANs while ACLs control which traffic is permitted.

---

# DHCP

DHCP is configured for the Employee, Guest, and Management networks as required.

Example:

```text
Employee DHCP Pool
Network: 10.10.10.0/24
Gateway: 10.10.10.1

Guest DHCP Pool
Network: 10.10.20.0/24
Gateway: 10.10.20.1

Management DHCP Pool
Network: 10.10.99.0/24
Gateway: 10.10.99.1
```

The Server VLAN can use a static IP address for the internal server.

---

# DNS

The internal server provides DNS functionality or acts as the configured DNS server for the branch.

Clients should be able to resolve the required internal/external names and reach the DNS service.

One of the fault scenarios tests what happens when an ACL incorrectly blocks DNS traffic.

---

# NAT and Internet Access

The branch router performs NAT/PAT to allow internal users to access the simulated internet through the ISP/Cloud.

Expected behavior:

```text
Employee → Internet     ALLOWED
Guest    → Internet     ALLOWED
Server   → Internet     As required
Management → Internet   As required
```

Private VLAN addresses are translated to the router's outside/public address before traffic reaches the ISP.

A NAT configuration failure is included as one of the troubleshooting scenarios.

---

# Security Design

## Guest Isolation

Guest users must be able to access the internet but must **not** access:

```text
Server VLAN
Management VLAN
Employee internal resources
```

Therefore:

```text
Guest → Internet       ✓
Guest → Server         ✗
Guest → Management     ✗
```

The official project check specifically requires guest devices to reach the internet while being blocked from the server and management networks.

---

## Secure Device Management

Network devices are configured for SSH management.

Only the Management VLAN is allowed to initiate SSH sessions.

```text
Management PC → Router       ✓
Management PC → Switch 1     ✓
Management PC → Switch 2     ✓

Employee PC → Router SSH     ✗
Guest PC → Router SSH        ✗
```

This demonstrates ACL-based management-plane security.

---

# Testing Plan

The following normal-operation tests must pass.

### Employee Testing

```text
Employee PC
     |
     ├── DHCP ✓
     ├── Ping Gateway ✓
     ├── Reach Server ✓
     └── Reach Internet ✓
```

### Guest Testing

```text
Guest Device
     |
     ├── DHCP ✓
     ├── Internet ✓
     ├── Server ✗
     └── Management Network ✗
```

### Management Testing

```text
Management PC
     |
     ├── SSH Router ✓
     ├── SSH Switch 1 ✓
     └── SSH Switch 2 ✓
```

These tests directly correspond to the project's required pass conditions.

---

# Fault Injection and Troubleshooting

At least five faults must be intentionally introduced into the working network.

## Fault 1 — Wrong Default Gateway

### Symptom

Client receives an IP address but cannot communicate outside its local subnet.

### Root Cause

Incorrect default gateway configured in the DHCP pool or client.

### Fix

Correct the gateway to the appropriate router subinterface.

Example:

```text
VLAN 10 → 10.10.10.1
VLAN 20 → 10.10.20.1
VLAN 30 → 10.10.30.1
VLAN 99 → 10.10.99.1
```

---

## Fault 2 — VLAN Missing From Trunk

### Symptom

Guest devices cannot communicate through the network.

### Root Cause

VLAN 20 is not permitted on the trunk.

### Fix

Add VLAN 20 to the trunk's allowed VLAN list.

Example finding:

```text
VLAN 20 missing on trunk SW1-F0/1
Symptom: Guest PC has no connectivity
Suggested fix: Add VLAN 20 to allowed trunk list
```

This follows the example finding specified in the project requirements.

---

## Fault 3 — DHCP Failure

### Symptom

Client receives an APIPA address or no valid IP address.

### Root Cause

DHCP pool configuration is incorrect or unavailable.

### Fix

Check:

```text
DHCP pool
Network
Default gateway
Excluded addresses
DHCP service
VLAN configuration
```

---

## Fault 4 — ACL Blocking DNS

### Symptom

Users can reach an IP address but DNS name resolution fails.

### Root Cause

ACL blocks DNS traffic.

### Fix

Permit the required DNS traffic while maintaining the intended security restrictions.

---

## Fault 5 — NAT Failure

### Symptom

Internal clients can communicate with the router but cannot access the internet.

### Root Cause

Incorrect or missing NAT configuration.

### Fix

Verify:

```text
Inside interfaces
Outside interface
NAT ACL
NAT/PAT rule
Default route
ISP connectivity
```

---

# Python Network Assurance Tool

A Python tool is developed to provide basic network configuration validation.

The tool can accept:

```text
1. VLAN/IP requirement file
2. Cisco show-command output
```

and generate readable findings.

### Example Input

```yaml
site: SmartBranch360

vlans:
  - id: 10
    name: EMPLOYEE
    subnet: 10.10.10.0/24
    gateway: 10.10.10.1

  - id: 20
    name: GUEST
    subnet: 10.10.20.0/24
    gateway: 10.10.20.1

  - id: 30
    name: SERVER
    subnet: 10.10.30.0/24
    gateway: 10.10.30.1

  - id: 99
    name: MANAGEMENT
    subnet: 10.10.99.0/24
    gateway: 10.10.99.1
```

### Example Python Output

```text
SMART BRANCH 360 - NETWORK VALIDATION
--------------------------------------

[PASS] VLAN 10 exists
[PASS] VLAN 20 exists
[FAIL] VLAN 20 missing from trunk SW1-F0/1

[PASS] VLAN 10 gateway: 10.10.10.1
[FAIL] VLAN 20 gateway mismatch

[PASS] DHCP pool EMPLOYEE found
[FAIL] DHCP pool GUEST missing

[PASS] Management VLAN configured
[WARNING] SSH access restriction should be verified

--------------------------------------
3 issues detected
2 checks passed with warnings
Suggested action: Review trunk, DHCP and gateway configuration.
```

The official specification requires the Python tool to produce clear findings such as a missing VLAN, incorrect gateway, or ACL-related problem.

---

# Project Deliverables

The completed project will contain:

```text
SmartBranch360/
│
├── README.md
│
├── packet-tracer/
│   └── SmartBranch360.pkt
│
├── documentation/
│   ├── topology.png
│   ├── vlan-ip-plan.xlsx
│   ├── security-rules.md
│   └── troubleshooting.md
│
├── requirements/
│   └── network_plan.yaml
│
├── python-checker/
│   ├── checker.py
│   ├── requirements.txt
│   └── sample_output.txt
│
├── fault-scenarios/
│   ├── fault-01-wrong-gateway.md
│   ├── fault-02-missing-vlan.md
│   ├── fault-03-dhcp-failure.md
│   ├── fault-04-dns-acl.md
│   └── fault-05-nat-failure.md
│
└── demo/
    └── demo-notes.md
```

The required submission includes the Packet Tracer file, design document, requirement file, Python tool and sample output, at least five fault cards, and a 5–10 minute demonstration video.

---

# Demo Flow

The final demonstration will follow this sequence:

### 1. Show the topology

Demonstrate:

* Router
* Two switches
* AP
* Server
* Employee devices
* Guest devices
* Management PC
* ISP/Cloud

### 2. Demonstrate normal operation

Show:

```text
Employee DHCP
Employee → Server
Employee → Internet
Guest DHCP
Guest → Internet
Guest → Server BLOCKED
Management → SSH devices
```

### 3. Inject a fault

For example:

```text
Remove VLAN 20 from the SW1 trunk.
```

### 4. Run Python checker

The tool identifies:

```text
VLAN 20 missing on trunk
```

### 5. Fix the Packet Tracer configuration

Restore VLAN 20 to the trunk.

### 6. Verify

Use:

```text
ping
tracert/traceroute
show vlan brief
show interfaces trunk
show ip interface brief
show ip route
show access-lists
show ip nat translations
```

### 7. Conclude

Demonstrate that the network has returned to normal operation.

---

# Success Criteria

The project is considered successful when:

* Employee devices obtain valid DHCP addresses.
* Employees can reach the internal server.
* Employees can access the internet.
* Guest devices obtain valid DHCP addresses.
* Guests can access the internet.
* Guests cannot access the Server VLAN.
* Guests cannot access the Management VLAN.
* Only the Management PC can SSH to network devices.
* Injected faults can be diagnosed and fixed.
* The Python checker produces useful and readable findings.
* The complete demonstration can be presented within 5–10 minutes.

---

# Technologies Used

* Cisco Packet Tracer
* Cisco IOS
* VLAN
* 802.1Q Trunking
* Router-on-a-Stick
* Inter-VLAN Routing
* DHCP
* DNS
* NAT/PAT
* ACL
* SSH
* IPv4
* Python
* YAML

---

# Project Goal

**Smart Branch 360 combines practical Cisco networking with Python-based network assurance.**

The project does not only demonstrate a working network; it demonstrates the complete engineering workflow:

```text
PLAN
  ↓
BUILD
  ↓
CONFIGURE
  ↓
TEST
  ↓
BREAK
  ↓
DIAGNOSE
  ↓
FIX
  ↓
VERIFY
```

This makes the project both a **networking implementation** and a **troubleshooting/automation project**.


