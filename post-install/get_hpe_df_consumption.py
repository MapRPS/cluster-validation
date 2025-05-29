import subprocess
import json

def run_maprcli_command(cmd):
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        output = result.stdout.decode("utf-8")
        data = json.loads(output)
        if data.get("status") == "ERROR":
            error_msgs = "; ".join(err.get("desc", "") for err in data.get("errors", []))
            raise RuntimeError(f"Command failed: {cmd}\nError: {error_msgs}")
        return data
    except json.JSONDecodeError:
        raise RuntimeError(f"Failed to parse JSON output from command: {cmd}\nOutput: {result.stdout.decode('utf-8')}")

def get_dashboard_info():
    dashboard_data = run_maprcli_command("maprcli dashboard info -json")
    if not dashboard_data.get("data"):
        return {}
    dashboard = dashboard_data["data"][0]
    cluster_info = dashboard.get("cluster", {})

    return {
        "cluster": {
            "name": cluster_info.get("name", "N/A"),
            "id": cluster_info.get("id", "N/A"),
            "nodesUsed": cluster_info.get("nodesUsed", 0)
        },
        "version": dashboard.get("version", "unknown"),
        "disk_space": dashboard.get("utilization", {}).get("disk_space", {}),
        "cpu": dashboard.get("utilization", {}).get("cpu", {}),
        "memory": dashboard.get("utilization", {}).get("memory", {})
    }

def print_table(nodes):
    headers = ["Hostname", "IP", "CPUs", "DUsed", "DAvail", "DTotal"]
    widths = [30, 15, 5, 6, 7, 7]

    header_row = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    print(header_row)
    print("-" * len(header_row))

    for node in nodes:
        row = [
            node.get("hostname", ""),
            node.get("ip", ""),
            str(node.get("cpus", "")),
            str(node.get("dused", "")),
            str(node.get("davail", "")),
            str(node.get("dtotal", ""))
        ]
        print("  ".join(val.ljust(w) for val, w in zip(row, widths)))

def print_dashboard_summary(info, license_id):
    cluster = info.get("cluster", {})
    print("\nDashboard Summary:")
    print(f"  Cluster Name: {cluster.get('name', 'N/A')}")
    print(f"  Cluster ID:   {cluster.get('id', 'N/A')}")
    print(f"  Nodes Used:   {cluster.get('nodesUsed', 'N/A')}")
    print(f"  Version:      {info.get('version', 'N/A')}")

    print("  Disk Space:")
    for k, v in info.get("disk_space", {}).items():
        print(f"    {k.capitalize()}: {v}")

    print("  CPU Usage:")
    print(f"    Total: {info['cpu'].get('total')} | Active: {info['cpu'].get('active')} | Util: {info['cpu'].get('util')}%")

    print("  Memory Usage:")
    print(f"    Total: {info['memory'].get('total')} MB | Active: {info['memory'].get('active')} MB")

def main():
    try:
        license_data = run_maprcli_command("maprcli license showid -json")
        if "data" not in license_data or not license_data["data"]:
            raise ValueError(f"Invalid license data: {license_data}")
        license_id = license_data["data"][0]["id"]

        node_data = run_maprcli_command("maprcli node list -columns ip,dused,davail,dtotal,cpus,hostname -json")
        if "data" not in node_data:
            raise ValueError(f"Invalid node list data: {node_data}")

        dashboard_info = get_dashboard_info()

        merged = {
            "license": {
                "id": license_id
            },
            "nodes": node_data["data"],
            "dashboard": dashboard_info
        }

        with open("hpe_df_consumption_data.json", "w") as f:
            json.dump(merged, f, indent=2)

        print_table(merged["nodes"])
        print_dashboard_summary(merged["dashboard"], license_id)

    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    main()

