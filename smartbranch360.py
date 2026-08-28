import re


# ============================================================
# SMARTBRANCH 360
# CLI CONFIGURATION ASSURANCE TOOL
# ============================================================

EXPECTED_VLANS = {
    "10": {
        "name": "Employee",
        "network": "10.10.10.0",
        "gateway": "10.10.10.1"
    },
    "20": {
        "name": "Guest",
        "network": "10.10.20.0",
        "gateway": "10.10.20.1"
    },
    "30": {
        "name": "Server",
        "network": "10.10.30.0",
        "gateway": "10.10.30.1"
    },
    "99": {
        "name": "Management",
        "network": "10.10.99.0",
        "gateway": "10.10.99.1"
    }
}

WAN_IP = "203.0.113.2"
ISP_GATEWAY = "203.0.113.1"
WAN_INTERFACE = "GigabitEthernet0/0/1"

MANAGEMENT_PC = "10.10.99.3"


# ============================================================
# OUTPUT FUNCTIONS
# ============================================================

def ok(message):
    print("[OK]    " + message)


def error(message):
    print("[ERROR] " + message)


def warning(message):
    print("[WARN]  " + message)


def info(message):
    print("[INFO]  " + message)


# ============================================================
# GET CISCO CONFIGURATION FROM USER
# ============================================================

def get_configuration():

    print("=" * 65)
    print("       SMARTBRANCH 360 CONFIGURATION ASSURANCE")
    print("=" * 65)

    print("\nPaste the output of:")
    print("show running-config")
    print()
    print("When finished, type:")
    print("END")
    print("-" * 65)

    lines = []

    while True:

        try:
            line = input()

        except EOFError:
            break

        if line.strip().upper() == "END":
            break

        lines.append(line)

    return "\n".join(lines)


# ============================================================
# VLAN CHECK
# ============================================================

def check_vlans(config):

    print("\n" + "=" * 65)
    print("VLAN / SUBINTERFACE CHECK")
    print("=" * 65)

    for vlan, data in EXPECTED_VLANS.items():

        interface = f"GigabitEthernet0/0/0.{vlan}"

        # Cisco may display the full or abbreviated interface name
        full_interface = interface.lower()
        short_interface = f"g0/0/0.{vlan}"

        if full_interface not in config.lower() and \
           short_interface not in config.lower():

            error(
                f"VLAN {vlan} ({data['name']}) "
                f"subinterface is missing."
            )

            continue

        ok(
            f"VLAN {vlan} ({data['name']}) "
            f"subinterface found."
        )

        if data["gateway"] in config:

            ok(
                f"Gateway {data['gateway']} found."
            )

        else:

            error(
                f"Gateway {data['gateway']} missing."
            )

        encapsulation = f"encapsulation dot1Q {vlan}"

        if encapsulation.lower() in config.lower():

            ok(
                f"VLAN {vlan} dot1Q encapsulation found."
            )

        else:

            error(
                f"VLAN {vlan} dot1Q encapsulation missing."
            )


# ============================================================
# DHCP CHECK
# ============================================================

def check_dhcp(config):

    print("\n" + "=" * 65)
    print("DHCP CHECK")
    print("=" * 65)

    pools = {
        "employee": ("10.10.10.0", "10.10.10.1"),
        "guests": ("10.10.20.0", "10.10.20.1"),
        "server": ("10.10.30.0", "10.10.30.1"),
        "management": ("10.10.99.0", "10.10.99.1")
    }

    for pool, values in pools.items():

        network, gateway = values

        if f"ip dhcp pool {pool}".lower() not in config.lower():

            error(
                f"DHCP pool '{pool}' is missing."
            )

            continue

        ok(
            f"DHCP pool '{pool}' exists."
        )

        # Extract DHCP pool section
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
            warning(
                f"Could not inspect pool '{pool}'."
            )
            continue

        pool_config = match.group(1)

        if network in pool_config:

            ok(
                f"Pool '{pool}' network = {network}"
            )

        else:

            error(
                f"Pool '{pool}' has wrong network."
            )

        if gateway in pool_config:

            ok(
                f"Pool '{pool}' gateway = {gateway}"
            )

        else:

            error(
                f"Pool '{pool}' has wrong gateway."
            )


# ============================================================
# NAT CHECK
# ============================================================

def check_nat(config):

    print("\n" + "=" * 65)
    print("NAT CHECK")
    print("=" * 65)

    # Inside interfaces
    for vlan in ["10", "20", "30", "99"]:

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

                ok(
                    f"VLAN {vlan} configured as NAT inside."
                )

            else:

                error(
                    f"VLAN {vlan} missing NAT inside."
                )

    # WAN
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

        section = match.group(1)

        if "ip nat outside" in section.lower():

            ok(
                f"{WAN_INTERFACE} configured as NAT outside."
            )

        else:

            error(
                f"{WAN_INTERFACE} missing NAT outside."
            )

    # NAT overload
    correct_nat = (
        "ip nat inside source list 1 "
        "interface GigabitEthernet0/0/1 overload"
    )

    if correct_nat.lower() in config.lower():

        ok(
            "NAT overload is using the ISP interface."
        )

    else:

        error(
            "NAT overload is missing or uses the wrong interface."
        )


# ============================================================
# DEFAULT ROUTE CHECK
# ============================================================

def check_route(config):

    print("\n" + "=" * 65)
    print("WAN / DEFAULT ROUTE CHECK")
    print("=" * 65)

    route = (
        f"ip route 0.0.0.0 0.0.0.0 {ISP_GATEWAY}"
    )

    if route.lower() in config.lower():

        ok(
            f"Default route → {ISP_GATEWAY}"
        )

    else:

        error(
            f"Default route to {ISP_GATEWAY} missing."
        )

    if WAN_IP in config:

        ok(
            f"WAN IP {WAN_IP} found."
        )

    else:

        error(
            f"WAN IP {WAN_IP} missing."
        )


# ============================================================
# ACL CHECK
# ============================================================

def check_acl(config):

    print("\n" + "=" * 65)
    print("ACL SECURITY CHECK")
    print("=" * 65)

    # Guest ACL
    if "ip access-list extended GuestSecurity".lower() \
            in config.lower():

        ok("GuestSecurity ACL exists.")

        guest_rules = [
            ("10.10.20.0", "10.10.30.0",
             "Guest → Server"),

            ("10.10.20.0", "10.10.10.0",
             "Guest → Employee"),

            ("10.10.20.0", "10.10.99.0",
             "Guest → Management")
        ]

        for source, destination, description in guest_rules:

            if source in config and destination in config:

                ok(
                    f"{description} restriction found."
                )

            else:

                error(
                    f"{description} restriction missing."
                )

    else:

        error(
            "GuestSecurity ACL is missing."
        )

    # Employee ACL
    if "ip access-list extended EmployeeSecurity".lower() \
            in config.lower():

        ok("EmployeeSecurity ACL exists.")

        if "10.10.10.0" in config and \
           "10.10.99.0" in config:

            ok(
                "Employee → Management restriction found."
            )

    else:

        error(
            "EmployeeSecurity ACL is missing."
        )


# ============================================================
# SSH CHECK
# ============================================================

def check_ssh(config):

    print("\n" + "=" * 65)
    print("SSH MANAGEMENT CHECK")
    print("=" * 65)

    if "ip ssh version 2" in config.lower():

        ok("SSH version 2 enabled.")

    else:

        error("SSH version 2 missing.")

    if "ip domain-name" in config.lower():

        ok("Domain name configured.")

    else:

        error("Domain name missing.")

    if "username admin privilege 15" in config.lower():

        ok("Administrator account exists.")

    else:

        error("Administrator account missing.")

    if "transport input ssh" in config.lower():

        ok("VTY accepts SSH.")

    else:

        error("VTY is not configured for SSH.")

    if "login local" in config.lower():

        ok("Local authentication enabled.")

    else:

        error("Local authentication missing.")

    # SSH ACL
    if "SSH_Management".lower() in config.lower():

        ok("SSH_Management ACL exists.")

    else:

        error("SSH_Management ACL missing.")

    if MANAGEMENT_PC in config:

        ok(
            f"Management PC {MANAGEMENT_PC} "
            f"appears in SSH configuration."
        )

    else:

        warning(
            f"Management PC {MANAGEMENT_PC} "
            f"not found in SSH configuration."
        )


# ============================================================
# SUMMARY
# ============================================================

def summary(config):

    print("\n" + "=" * 65)
    print("FINAL SUMMARY")
    print("=" * 65)

    errors = 0

    # Basic checks
    required_items = [
        "GigabitEthernet0/0/0.10",
        "GigabitEthernet0/0/0.20",
        "GigabitEthernet0/0/0.30",
        "GigabitEthernet0/0/0.99",
        "GigabitEthernet0/0/1",
        "ip nat inside source list 1",
        "ip route 0.0.0.0 0.0.0.0"
    ]

    for item in required_items:

        if item.lower() not in config.lower():

            errors += 1

    if errors == 0:

        print("RESULT: Configuration appears healthy.")

    else:

        print(
            f"RESULT: {errors} major configuration "
            f"item(s) may be missing."
        )

    print("\nRemember:")
    print("The tool reports likely configuration problems.")
    print("Always verify the result using Packet Tracer tests.")


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    config = get_configuration()

    if not config.strip():

        print("\nNo configuration was entered.")
        return

    check_vlans(config)
    check_dhcp(config)
    check_nat(config)
    check_route(config)
    check_acl(config)
    check_ssh(config)
    summary(config)


if __name__ == "__main__":
    main()