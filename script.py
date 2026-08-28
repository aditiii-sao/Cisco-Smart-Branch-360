import re
import sys
from pathlib import Path

# Expected VLAN information from the current SmartBranch design
VLAN_CONFIG = {
    10: {
        "name": "employee",
        "network": "10.10.10.0",
        "gateway": "10.10.10.1",
    },
    20: {
        "name": "guests",
        "network": "10.10.20.0",
        "gateway": "10.10.20.1",
    },
    30: {
        "name": "server",
        "network": "10.10.30.0",
        "gateway": "10.10.30.1",
    },
    99: {
        "name": "management",
        "network": "10.10.99.0",
        "gateway": "10.10.99.1",
    }
}

# Current WAN design
WAN_INTERFACE = "GigabitEthernet0/0/1"
WAN_IP = "203.0.113.2"
ISP_GATEWAY = "203.0.113.1"

# Management PC
MANAGEMENT_PC = "10.10.99.3"

# Internal server
SERVER_IP = "10.10.30.2"


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def line_exists(config, text):
    return text.lower() in config.lower()


def print_ok(message):
    print("[OK]   " + message)


def print_warn(message):
    print("[WARN] " + message)


def print_error(message):
    print("[ERROR] " + message)


def print_info(message):
    print("[INFO] " + message)


# VLAN / SUBINTERFACE CHECK


def check_vlan_subinterfaces(config):
    print("\n--- VLAN / ROUTER SUBINTERFACE CHECK ---")

    for vlan, data in VLAN_CONFIG.items():

        interface = f"GigabitEthernet0/0/0.{vlan}"
        ip = data["gateway"]

        # Accept abbreviated interface names too
        interface_found = (
            interface.lower() in config.lower()
            or f"g0/0/0.{vlan}".lower() in config.lower()
        )

        if not interface_found:
            print_error(
                f"VLAN {vlan} ({data['name']}) subinterface is missing."
            )
            continue

        print_ok(
            f"VLAN {vlan} ({data['name']}) subinterface exists."
        )

        if ip in config:
            print_ok(
                f"VLAN {vlan} gateway {ip} found."
            )
        else:
            print_error(
                f"VLAN {vlan} gateway {ip} not found."
            )

        encapsulation = f"encapsulation dot1Q {vlan}"

        if encapsulation.lower() in config.lower():
            print_ok(
                f"VLAN {vlan} has dot1Q encapsulation."
            )
        else:
            print_error(
                f"VLAN {vlan} is missing dot1Q encapsulation."
            )


# DHCP CHECK

def check_dhcp(config):
    print("\n--- DHCP CHECK ---")

    pools = {
        "employee": ("10.10.10.0", "10.10.10.1"),
        "guests": ("10.10.20.0", "10.10.20.1"),
        "server": ("10.10.30.0", "10.10.30.1"),
        "management": ("10.10.99.0", "10.10.99.1"),
    }

    for pool, (network, gateway) in pools.items():

        if f"ip dhcp pool {pool}".lower() not in config.lower():
            print_error(
                f"DHCP pool '{pool}' is missing."
            )
            continue

        print_ok(
            f"DHCP pool '{pool}' exists."
        )

        # Find pool section
        pattern = (
            rf"ip dhcp pool {re.escape(pool)}"
            rf"(.*?)(?=ip dhcp pool|!|\Z)"
        )

        match = re.search(
            pattern,
            config,
            re.IGNORECASE | re.DOTALL
        )

        if not match:
            print_warn(
                f"Could not fully inspect DHCP pool '{pool}'."
            )
            continue

        pool_config = match.group(1)

        if network in pool_config:
            print_ok(
                f"DHCP pool '{pool}' has network {network}."
            )
        else:
            print_error(
                f"DHCP pool '{pool}' has incorrect/missing network."
            )

        if gateway in pool_config:
            print_ok(
                f"DHCP pool '{pool}' has gateway {gateway}."
            )
        else:
            print_error(
                f"DHCP pool '{pool}' has incorrect/missing gateway."
            )


# NAT CHECK

def check_nat(config):
    print("\n--- NAT CHECK ---")

    # Inside interfaces
    for vlan in [10, 20, 30, 99]:

        pattern = (
            rf"interface\s+GigabitEthernet0/0/0\.{vlan}"
            rf"(.*?)(?=interface\s+|\Z)"
        )

        match = re.search(
            pattern,
            config,
            re.IGNORECASE | re.DOTALL
        )

        if match:

            section = match.group(1)

            if "ip nat inside" in section.lower():
                print_ok(
                    f"VLAN {vlan} is configured as NAT inside."
                )
            else:
                print_error(
                    f"VLAN {vlan} is missing 'ip nat inside'."
                )

    # WAN outside
    pattern = (
        rf"interface\s+{re.escape(WAN_INTERFACE)}"
        rf"(.*?)(?=interface\s+|\Z)"
    )

    match = re.search(
        pattern,
        config,
        re.IGNORECASE | re.DOTALL
    )

    if match:

        wan_section = match.group(1)

        if "ip nat outside" in wan_section.lower():
            print_ok(
                f"{WAN_INTERFACE} is configured as NAT outside."
            )
        else:
            print_error(
                f"{WAN_INTERFACE} is missing 'ip nat outside'."
            )

    # NAT overload
    correct_nat = (
        "ip nat inside source list 1 "
        "interface GigabitEthernet0/0/1 overload"
    )

    if correct_nat.lower() in config.lower():

        print_ok(
            "NAT overload is configured on the ISP-facing interface."
        )

    else:

        print_error(
            "NAT overload rule is missing or uses the wrong interface."
        )

    # NAT ACL
    networks = [
        "10.10.10.0",
        "10.10.20.0",
        "10.10.30.0",
        "10.10.99.0"
    ]

    for network in networks:

        if network in config:

            # Don't treat this as a perfect proof; just report
            # that the network appears in the configuration.
            print_info(
                f"NAT/internal network {network} appears in configuration."
            )


# DEFAULT ROUTE CHECK

def check_default_route(config):
    print("\n--- DEFAULT ROUTE CHECK ---")

    expected = (
        "ip route 0.0.0.0 0.0.0.0 "
        + ISP_GATEWAY
    )

    if expected.lower() in config.lower():

        print_ok(
            f"Default route points to ISP {ISP_GATEWAY}."
        )

    else:

        print_error(
            f"Default route to ISP {ISP_GATEWAY} is missing."
        )


# GUEST SECURITY ACL

def check_guest_acl(config):
    print("\n--- GUEST SECURITY ACL CHECK ---")

    acl_pattern = (
        r"ip access-list extended GuestSecurity"
        r"(.*?)(?=ip access-list|access-list|line vty|end|\Z)"
    )

    match = re.search(
        acl_pattern,
        config,
        re.IGNORECASE | re.DOTALL
    )

    if not match:

        print_error(
            "GuestSecurity ACL is missing."
        )
        return

    acl = match.group(1).lower()

    required_blocks = [
        ("10.10.20.0", "10.10.30.0", "Guest -> Server"),
        ("10.10.20.0", "10.10.10.0", "Guest -> Employee"),
        ("10.10.20.0", "10.10.99.0", "Guest -> Management"),
    ]

    for source, destination, description in required_blocks:

        if source in acl and destination in acl:

            print_ok(
                f"{description} restriction appears configured."
            )

        else:

            print_error(
                f"{description} restriction is missing."
            )

    if "permit ip any any" in acl:

        print_ok(
            "Guest ACL allows remaining traffic, including Internet traffic."
        )

    else:

        print_warn(
            "Guest ACL has no 'permit ip any any'."
        )


# EMPLOYEE ACL

def check_employee_acl(config):
    print("\n--- EMPLOYEE SECURITY ACL CHECK ---")

    acl_pattern = (
        r"ip access-list extended EmployeeSecurity"
        r"(.*?)(?=ip access-list|access-list|line vty|end|\Z)"
    )

    match = re.search(
        acl_pattern,
        config,
        re.IGNORECASE | re.DOTALL
    )

    if not match:

        print_error(
            "EmployeeSecurity ACL is missing."
        )
        return

    acl = match.group(1).lower()

    if "10.10.10.0" in acl and "10.10.99.0" in acl:

        print_ok(
            "Employee -> Management restriction appears configured."
        )

    else:

        print_warn(
            "Employee -> Management restriction is missing."
        )

    if "permit ip any any" in acl:

        print_ok(
            "Employee ACL permits other traffic."
        )


# SSH CHECK


def check_ssh(config):
    print("\n--- SSH MANAGEMENT CHECK ---")

    if "ip ssh version 2" in config.lower():

        print_ok(
            "SSH version 2 is enabled."
        )

    else:

        print_error(
            "SSH version 2 is missing."
        )

    if "ip domain-name" in config.lower():

        print_ok(
            "IP domain name is configured."
        )

    else:

        print_error(
            "IP domain name is missing."
        )

    if "username admin privilege 15" in config.lower():

        print_ok(
            "Administrative user exists."
        )

    else:

        print_error(
            "Administrative SSH user is missing."
        )

    if "transport input ssh" in config.lower():

        print_ok(
            "VTY lines allow SSH."
        )

    else:

        print_error(
            "VTY lines are not configured for SSH."
        )

    if "login local" in config.lower():

        print_ok(
            "VTY uses local authentication."
        )

    else:

        print_error(
            "VTY is missing 'login local'."
        )

    # SSH ACL
    if "ip access-list standard SSH_Management".lower() in config.lower():

        print_ok(
            "SSH_Management ACL exists."
        )

        if MANAGEMENT_PC in config:

            print_ok(
                f"Management PC {MANAGEMENT_PC} is permitted for SSH."
            )

        else:

            print_error(
                f"Management PC {MANAGEMENT_PC} is not permitted."
            )

    else:

        print_error(
            "SSH_Management ACL is missing."
        )

    if "access-class SSH_Management in".lower() in config.lower():

        print_ok(
            "SSH_Management ACL is applied to VTY lines."
        )

    else:

        print_error(
            "SSH_Management ACL is not applied to VTY lines."
        )


# SERVER CHECK

def check_server(config):
    print("\n--- SERVER CHECK ---")

    if SERVER_IP in config:

        print_info(
            f"Server IP {SERVER_IP} appears in the configuration."
        )

    else:

        print_warn(
            f"Server IP {SERVER_IP} was not found in this configuration."
        )

    print_info(
        "Remember: the actual Packet Tracer server IP must be checked "
        "from the Server device itself."
    )


# GENERAL CHECK

def check_general(config):
    print("\n--- GENERAL CHECK ---")

    if "interface GigabitEthernet0/0/0" in config:

        print_ok(
            "Router trunk interface G0/0/0 exists."
        )

    else:

        print_error(
            "Router trunk interface G0/0/0 is missing."
        )

    if WAN_IP in config:

        print_ok(
            f"WAN IP {WAN_IP} is configured."
        )

    else:

        print_error(
            f"WAN IP {WAN_IP} was not found."
        )

# MAIN

def run_checker(config):
    print("=" * 60)
    print("       SMARTBRANCH 360 NETWORK ASSURANCE TOOL")
    print("=" * 60)

    check_general(config)
    check_vlan_subinterfaces(config)
    check_dhcp(config)
    check_nat(config)
    check_default_route(config)
    check_guest_acl(config)
    check_employee_acl(config)
    check_ssh(config)
    check_server(config)

    print("\n" + "=" * 60)
    print("CHECK COMPLETE")
    print("=" * 60)

    print("\nLegend:")
    print("[OK]    Configuration appears correct")
    print("[WARN]  Possible issue / manual verification required")
    print("[ERROR] Likely configuration problem")
    print("[INFO]  Additional information")


# READ CONFIGURATION FILE

def main():

    if len(sys.argv) < 2:

        print("Usage:")
        print("python smartbranch_checker.py router.txt")
        print()
        print("Example:")
        print("python smartbranch_checker.py router.txt")
        return

    filename = Path(sys.argv[1])

    if not filename.exists():

        print_error(
            f"File '{filename}' was not found."
        )
        return

    try:

        config = filename.read_text(
            encoding="utf-8",
            errors="ignore"
        )

    except Exception as e:

        print_error(
            f"Could not read configuration: {e}"
        )
        return

    run_checker(config)


if __name__ == "__main__":
    main()
