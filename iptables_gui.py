from flask import Flask, render_template_string, request, redirect, jsonify
import subprocess
import re
import json
from functools import wraps

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Advanced IPTables Manager</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        .tab {
            overflow: hidden;
            border: 1px solid #ccc;
            background-color: #f1f1f1;
            border-radius: 4px;
        }
        .tab button {
            background-color: inherit;
            float: left;
            border: none;
            outline: none;
            cursor: pointer;
            padding: 14px 16px;
            transition: 0.3s;
        }
        .tab button:hover {
            background-color: #ddd;
        }
        .tab button.active {
            background-color: #4CAF50;
            color: white;
        }
        .tabcontent {
            display: none;
            padding: 20px;
            border: 1px solid #ccc;
            border-top: none;
        }
        table { 
            border-collapse: collapse; 
            width: 100%;
            margin-bottom: 20px;
        }
        th, td { 
            border: 1px solid #ddd; 
            padding: 12px; 
            text-align: left; 
        }
        th { 
            background-color: #4CAF50; 
            color: white;
        }
        tr:nth-child(even) { 
            background-color: #f2f2f2; 
        }
        .button { 
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin: 5px;
        }
        .delete { 
            background-color: #f44336; 
        }
        .form-group {
            margin-bottom: 15px;
        }
        select, input {
            padding: 8px;
            margin: 5px;
            border-radius: 4px;
            border: 1px solid #ddd;
        }
        .status {
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
        }
        .status.success {
            background-color: #dff0d8;
            border: 1px solid #d6e9c6;
            color: #3c763d;
        }
        .status.error {
            background-color: #f2dede;
            border: 1px solid #ebccd1;
            color: #a94442;
        }
    </style>
    <script>
        function openTab(evt, tabName) {
            var i, tabcontent, tablinks;
            tabcontent = document.getElementsByClassName("tabcontent");
            for (i = 0; i < tabcontent.length; i++) {
                tabcontent[i].style.display = "none";
            }
            tablinks = document.getElementsByClassName("tablinks");
            for (i = 0; i < tablinks.length; i++) {
                tablinks[i].className = tablinks[i].className.replace(" active", "");
            }
            document.getElementById(tabName).style.display = "block";
            evt.currentTarget.className += " active";
        }

        function updateRuleDisplay() {
            const table = document.getElementById("table-select").value;
            const chain = document.getElementById("chain-select").value;
            fetch(`/get_rules/${table}/${chain}`)
                .then(response => response.json())
                .then(data => {
                    const rulesTable = document.getElementById("rules-table");
                    rulesTable.innerHTML = data.html;
                });
        }

        // Show rules tab by default
        document.addEventListener('DOMContentLoaded', function() {
            document.querySelector('.tablinks').click();
        });
    </script>
</head>
<body>
    <div class="container">
        <h1>Advanced IPTables Manager</h1>
        
        <div class="tab">
            <button class="tablinks" onclick="openTab(event, 'Rules')">Rules Management</button>
            <button class="tablinks" onclick="openTab(event, 'Chains')">Chains</button>
            <button class="tablinks" onclick="openTab(event, 'NAT')">NAT Configuration</button>
            <button class="tablinks" onclick="openTab(event, 'Policies')">Default Policies</button>
            <button class="tablinks" onclick="openTab(event, 'Save')">Save/Restore</button>
        </div>

        <div id="Rules" class="tabcontent">
            <h2>Manage Rules</h2>
            <div class="form-group">
                <select id="table-select" onchange="updateRuleDisplay()">
                    <option value="filter">Filter</option>
                    <option value="nat">NAT</option>
                    <option value="mangle">Mangle</option>
                    <option value="raw">Raw</option>
                </select>
                <select id="chain-select" onchange="updateRuleDisplay()">
                    {% for chain in chains %}
                        <option value="{{ chain }}">{{ chain }}</option>
                    {% endfor %}
                </select>
            </div>

            <div id="rules-table">
                {{ rules_table | safe }}
            </div>

            <h3>Add New Rule</h3>
            <form method="POST" action="/add_rule">
                <div class="form-group">
                    <select name="table" required>
                        <option value="filter">Filter</option>
                        <option value="nat">NAT</option>
                        <option value="mangle">Mangle</option>
                        <option value="raw">Raw</option>
                    </select>
                    
                    <select name="chain" required>
                        {% for chain in chains %}
                            <option value="{{ chain }}">{{ chain }}</option>
                        {% endfor %}
                    </select>
                    
                    <select name="action" required>
                        <option value="ACCEPT">ACCEPT</option>
                        <option value="DROP">DROP</option>
                        <option value="REJECT">REJECT</option>
                        <option value="LOG">LOG</option>
                        <option value="SNAT">SNAT</option>
                        <option value="DNAT">DNAT</option>
                        <option value="MASQUERADE">MASQUERADE</option>
                    </select>
                </div>

                <div class="form-group">
                    <input type="text" name="source_ip" placeholder="Source IP">
                    <input type="text" name="dest_ip" placeholder="Destination IP">
                    <input type="text" name="source_port" placeholder="Source Port">
                    <input type="text" name="dest_port" placeholder="Destination Port">
                    <select name="protocol">
                        <option value="tcp">TCP</option>
                        <option value="udp">UDP</option>
                        <option value="icmp">ICMP</option>
                        <option value="all">All</option>
                    </select>
                </div>

                <div class="form-group">
                    <input type="text" name="to_source" placeholder="To-Source (for SNAT)">
                    <input type="text" name="to_destination" placeholder="To-Destination (for DNAT)">
                    <input type="text" name="in_interface" placeholder="Input Interface">
                    <input type="text" name="out_interface" placeholder="Output Interface">
                </div>

                <button type="submit" class="button">Add Rule</button>
            </form>
        </div>

        <div id="Chains" class="tabcontent">
            <h2>Chain Management</h2>
            <h3>Custom Chains</h3>
            <table>
                <tr>
                    <th>Table</th>
                    <th>Chain</th>
                    <th>Action</th>
                </tr>
                {% for chain in custom_chains %}
                <tr>
                    <td>{{ chain.table }}</td>
                    <td>{{ chain.name }}</td>
                    <td>
                        <form method="POST" action="/delete_chain" style="display: inline;">
                            <input type="hidden" name="table" value="{{ chain.table }}">
                            <input type="hidden" name="chain" value="{{ chain.name }}">
                            <button type="submit" class="button delete">Delete</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </table>

            <h3>Create New Chain</h3>
            <form method="POST" action="/create_chain">
                <select name="table" required>
                    <option value="filter">Filter</option>
                    <option value="nat">NAT</option>
                    <option value="mangle">Mangle</option>
                    <option value="raw">Raw</option>
                </select>
                <input type="text" name="chain" placeholder="Chain Name" required>
                <button type="submit" class="button">Create Chain</button>
            </form>
        </div>

        <div id="NAT" class="tabcontent">
            <h2>NAT Configuration</h2>
            <h3>Current NAT Rules</h3>
            <div id="nat-rules">
                {{ nat_rules | safe }}
            </div>

            <h3>Add NAT Rule</h3>
            <form method="POST" action="/add_nat_rule">
                <div class="form-group">
                    <select name="nat_type" required>
                        <option value="SNAT">Source NAT</option>
                        <option value="DNAT">Destination NAT</option>
                        <option value="MASQUERADE">Masquerade</option>
                    </select>
                    <input type="text" name="source" placeholder="Source Address">
                    <input type="text" name="destination" placeholder="Destination Address">
                    <input type="text" name="to_source" placeholder="To-Source Address">
                    <input type="text" name="to_destination" placeholder="To-Destination Address">
                </div>
                <button type="submit" class="button">Add NAT Rule</button>
            </form>
        </div>

        <div id="Policies" class="tabcontent">
            <h2>Default Policies</h2>
            <table>
                <tr>
                    <th>Table</th>
                    <th>Chain</th>
                    <th>Current Policy</th>
                    <th>Action</th>
                </tr>
                {% for policy in policies %}
                <tr>
                    <td>{{ policy.table }}</td>
                    <td>{{ policy.chain }}</td>
                    <td>{{ policy.policy }}</td>
                    <td>
                        <form method="POST" action="/set_policy">
                            <input type="hidden" name="table" value="{{ policy.table }}">
                            <input type="hidden" name="chain" value="{{ policy.chain }}">
                            <select name="policy">
                                <option value="ACCEPT">ACCEPT</option>
                                <option value="DROP">DROP</option>
                                <option value="REJECT">REJECT</option>
                            </select>
                            <button type="submit" class="button">Update</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>

        <div id="Save" class="tabcontent">
            <h2>Save/Restore Rules</h2>
            <form method="POST" action="/save_rules">
                <button type="submit" class="button">Save Current Rules</button>
            </form>
            
            <h3>Restore Rules</h3>
            <form method="POST" action="/restore_rules" enctype="multipart/form-data">
                <input type="file" name="rules_file" accept=".rules">
                <button type="submit" class="button">Restore Rules</button>
            </form>
        </div>
    </div>
</body>
</html>
"""

def require_sudo(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not check_sudo():
            return jsonify({'error': 'Sudo privileges required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def check_sudo():
    try:
        subprocess.check_output(['sudo', '-n', 'true'])
        return True
    except:
        return False

def get_chains(table='filter'):
    try:
        output = subprocess.check_output(['sudo', 'iptables', '-t', table, '-L', '-n']).decode()
        chains = []
        for line in output.split('\n'):
            if line.startswith('Chain'):
                chain_name = line.split()[1]
                chains.append(chain_name)
        return chains
    except Exception as e:
        print(f"Error getting chains: {e}")
        return []

def get_custom_chains():
    tables = ['filter', 'nat', 'mangle', 'raw']
    custom_chains = []
    for table in tables:
        try:
            output = subprocess.check_output(['sudo', 'iptables', '-t', table, '-L', '-n']).decode()
            for line in output.split('\n'):
                if line.startswith('Chain') and not any(default in line for default in ['INPUT', 'OUTPUT', 'FORWARD', 'PREROUTING', 'POSTROUTING']):
                    chain_name = line.split()[1]
                    custom_chains.append({'table': table, 'name': chain_name})
        except:
            continue
    return custom_chains

def get_policies():
    tables = ['filter', 'nat', 'mangle', 'raw']
    policies = []
    for table in tables:
        try:
            output = subprocess.check_output(['sudo', 'iptables', '-t', table, '-L', '-n']).decode()
            for line in output.split('\n'):
                if line.startswith('Chain'):
                    parts = line.split()
                    if len(parts) > 3 and parts[2] == '(policy':
                        chain = parts[1]
                        policy = parts[3].rstrip(')')
                        policies.append({'table': table, 'chain': chain, 'policy': policy})
        except:
            continue
    return policies

@app.route('/')
def index():
    chains = get_chains()
    custom_chains = get_custom_chains()
    policies = get_policies()
    return render_template_string(HTML_TEMPLATE, 
                                chains=chains,
                                custom_chains=custom_chains,
                                policies=policies,
                                rules_table=get_rules_table('filter', 'INPUT'),
nat_rules=get_nat_rules())

def get_rules_table(table, chain):
    try:
        output = subprocess.check_output(['sudo', 'iptables', '-t', table, '-L', chain, '-n', '--line-numbers', '-v']).decode()
        lines = output.split('\n')[2:]  # Skip header lines
        html = '<table><tr><th>Num</th><th>Pkts</th><th>Bytes</th><th>Target</th><th>Prot</th><th>Opt</th><th>Source</th><th>Destination</th><th>Action</th></tr>'
        
        for line in lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 8:
                    html += f'''
                        <tr>
                            <td>{parts[0]}</td>
                            <td>{parts[1]}</td>
                            <td>{parts[2]}</td>
                            <td>{parts[3]}</td>
                            <td>{parts[4]}</td>
                            <td>{parts[5]}</td>
                            <td>{parts[6]}</td>
                            <td>{parts[7]}</td>
                            <td>
                                <form method="POST" action="/delete_rule" style="display: inline;">
                                    <input type="hidden" name="table" value="{table}">
                                    <input type="hidden" name="chain" value="{chain}">
                                    <input type="hidden" name="rule_number" value="{parts[0]}">
                                    <button type="submit" class="button delete">Delete</button>
                                </form>
                            </td>
                        </tr>
                    '''
        html += '</table>'
        return html
    except Exception as e:
        return f'<div class="status error">Error getting rules: {str(e)}</div>'

def get_nat_rules():
    try:
        output = subprocess.check_output(['sudo', 'iptables', '-t', 'nat', '-L', '-n', '-v']).decode()
        return f'<pre>{output}</pre>'
    except Exception as e:
        return f'<div class="status error">Error getting NAT rules: {str(e)}</div>'

@app.route('/get_rules/<table>/<chain>')
@require_sudo
def get_rules(table, chain):
    return jsonify({'html': get_rules_table(table, chain)})

@app.route('/add_rule', methods=['POST'])
@require_sudo
def add_rule():
    try:
        cmd = ['sudo', 'iptables', '-t', request.form['table'], '-A', request.form['chain']]
        
        # Add protocol if specified
        if request.form.get('protocol'):
            cmd.extend(['-p', request.form['protocol']])
        
        # Add source IP if specified
        if request.form.get('source_ip'):
            cmd.extend(['-s', request.form['source_ip']])
            
        # Add destination IP if specified
        if request.form.get('dest_ip'):
            cmd.extend(['-d', request.form['dest_ip']])
            
        # Add ports if specified
        if request.form.get('source_port'):
            cmd.extend(['--sport', request.form['source_port']])
        if request.form.get('dest_port'):
            cmd.extend(['--dport', request.form['dest_port']])
            
        # Add interfaces if specified
        if request.form.get('in_interface'):
            cmd.extend(['-i', request.form['in_interface']])
        if request.form.get('out_interface'):
            cmd.extend(['-o', request.form['out_interface']])
            
        # Add NAT-specific options
        if request.form['action'] == 'SNAT' and request.form.get('to_source'):
            cmd.extend(['-j', 'SNAT', '--to-source', request.form['to_source']])
        elif request.form['action'] == 'DNAT' and request.form.get('to_destination'):
            cmd.extend(['-j', 'DNAT', '--to-destination', request.form['to_destination']])
        else:
            cmd.extend(['-j', request.form['action']])
            
        subprocess.check_call(cmd)
        return redirect('/')
    except Exception as e:
        return f'<div class="status error">Error adding rule: {str(e)}</div>'

@app.route('/delete_rule', methods=['POST'])
@require_sudo
def delete_rule():
    try:
        subprocess.check_call([
            'sudo', 'iptables', 
            '-t', request.form['table'],
            '-D', request.form['chain'],
            request.form['rule_number']
        ])
        return redirect('/')
    except Exception as e:
        return f'<div class="status error">Error deleting rule: {str(e)}</div>'

@app.route('/create_chain', methods=['POST'])
@require_sudo
def create_chain():
    try:
        subprocess.check_call([
            'sudo', 'iptables',
            '-t', request.form['table'],
            '-N', request.form['chain']
        ])
        return redirect('/')
    except Exception as e:
        return f'<div class="status error">Error creating chain: {str(e)}</div>'

@app.route('/delete_chain', methods=['POST'])
@require_sudo
def delete_chain():
    try:
        # First flush the chain
        subprocess.check_call([
            'sudo', 'iptables',
            '-t', request.form['table'],
            '-F', request.form['chain']
        ])
        # Then delete it
        subprocess.check_call([
            'sudo', 'iptables',
            '-t', request.form['table'],
            '-X', request.form['chain']
        ])
        return redirect('/')
    except Exception as e:
        return f'<div class="status error">Error deleting chain: {str(e)}</div>'

@app.route('/set_policy', methods=['POST'])
@require_sudo
def set_policy():
    try:
        subprocess.check_call([
            'sudo', 'iptables',
            '-t', request.form['table'],
            '-P', request.form['chain'],
            request.form['policy']
        ])
        return redirect('/')
    except Exception as e:
        return f'<div class="status error">Error setting policy: {str(e)}</div>'

@app.route('/save_rules', methods=['POST'])
@require_sudo
def save_rules():
    try:
        subprocess.check_call(['sudo', 'iptables-save', '-f', '/etc/iptables/rules.v4'])
        return '<div class="status success">Rules saved successfully</div>'
    except Exception as e:
        return f'<div class="status error">Error saving rules: {str(e)}</div>'

@app.route('/restore_rules', methods=['POST'])
@require_sudo
def restore_rules():
    try:
        if 'rules_file' not in request.files:
            return '<div class="status error">No file uploaded</div>'
            
        file = request.files['rules_file']
        if file.filename == '':
            return '<div class="status error">No file selected</div>'
            
        # Save uploaded file temporarily
        temp_path = '/tmp/iptables_restore.rules'
        file.save(temp_path)
        
        # Restore rules
        subprocess.check_call(['sudo', 'iptables-restore', temp_path])
        return redirect('/')
    except Exception as e:
        return f'<div class="status error">Error restoring rules: {str(e)}</div>'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
