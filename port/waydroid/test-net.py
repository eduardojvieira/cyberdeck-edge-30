#!/usr/bin/env python3
"""Host-safe regression: run only firewall functions with shell command stubs."""
from pathlib import Path
import subprocess
import sys

source = Path(sys.argv[1]).read_text()
start = source[source.index("start_iptables() {"):source.index("start_nftables() {")]
stop = source[source.index("stop_iptables() {"):source.index("stop_nftables() {")]
stubs = '''
set -e
IPTABLES_BIN=ipt
LXC_BRIDGE=waydroid0
start_ipv6() { :; }
ipt() {
    case "$*" in
        *CHECKSUM*) return 1;;
        *MASQUERADE*) [ "$fail_nat" = no ];;
        *) return 0;;
    esac
}
ethtool() {
    [ "$*" = "-K waydroid0 tx off" ] || exit 90
    echo software-checksum
    [ "$fail_ethtool" = no ]
}
'''
for fail_nat, fail_ethtool, success in [("no", "no", True), ("yes", "no", False), ("no", "yes", False)]:
    script = f"fail_nat={fail_nat}\nfail_ethtool={fail_ethtool}\n" + stubs + start + stop
    result = subprocess.run(["sh", "-c", script + "\nstart_iptables; stop_iptables; echo PASS"], capture_output=True, text=True)
    assert (result.returncode == 0) == success, (fail_nat, fail_ethtool, result)
    if success:
        assert result.stdout == "software-checksum\nPASS\n", result
    if fail_nat == "yes":
        assert "software-checksum" not in result.stdout, result
print("PASS: checksum fallback; NAT and ethtool failures remain fatal; cleanup succeeds")
