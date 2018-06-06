import json
import re
import sys
import itertools

# Original file from https://github.com/RetireJS/retire.js/blob/master/repository/jsrepository.json
with open('../data/jsrepository.json') as f:
    retirejs_json = json.load(f)

def process_version(vuln, field):
    if field in vuln:
        splitted = vuln[field].split('.')
        for num in splitted:
            if not num.isdigit():
                print('Cannot process %s' % str(num))
                sys.exit(1)
        vuln[field] = [int(x) for x in splitted]

for lib, data in retirejs_json.items():
    if lib not in ['retire-example', 'dont check']:
        for vuln in data['vulnerabilities']:
            process_version(vuln, 'atOrAbove')
            process_version(vuln, 'below')


def clean_version(version):
    result = []
    for num in version.split('.'):
        match = re.search(r'^\d+', num)
        if match:
            result.append(int(match.group(0)))
        else:
            break
    return result

def atOrAbove(vuln, version):
    for vuln_num, found_num in itertools.zip_longest(vuln['atOrAbove'], version, fillvalue=0):
        if found_num > vuln_num:
            return True
        if found_num < vuln_num:
            return False
    return True

def below(vuln, version):
    for vuln_num, found_num in itertools.zip_longest(vuln['below'], version, fillvalue=0):
        if found_num > vuln_num:
            return False
        if found_num < vuln_num:
            return True
    return False

results={}
with open('../data/crawler_result.csv') as f:
    for line in f:
        if line[-1:] == "\n":
            line = line[:-1]
        splited = line.split(';', 2)
        if splited[0] not in results:
            results[splited[0]] = {}
        version = clean_version(splited[2])
        if version:
            results[splited[0]][splited[1]] = version

host_vulns_sum = {}
with open('../data/list.txt') as f:
    for line in f:
        if line[-1:] == "\n":
            line = line[:-1]
        host_vulns_sum[line] = 0

for host, libs in results.items():
    for lib, version in libs.items():
        for vuln_lib, data in retirejs_json.items():
            if vuln_lib not in ['retire-example', 'dont check'] and vuln_lib == lib:
                for vuln in data['vulnerabilities']:
                    if 'atOrAbove' in vuln and 'below' in vuln:
                        vulnerable = atOrAbove(vuln, version) and below(vuln, version)
                    elif 'atOrAbove' in vuln:
                        vulnerable = atOrAbove(vuln, version)
                    elif 'below' in vuln:
                        vulnerable = below(vuln, version)
                    else:
                        print('No atOrAbove or below in %s?', lib)
                    if vulnerable:
                        #print('Vulnerability found for %s: %s %s! %s' % (host, lib, version, vuln))
                        #print()
                        host_vulns_sum[host] += 1

i = 0
for host, vulns in host_vulns_sum.items():
    i += 1
    print('%d;%d;%s;%d' % (i, (i//1000)*1000, host, vulns))

#print(host_vulns_sum)
#print('Hosts found with at least one vulnerability: %d' % len([x for x in host_vulns_sum.items() if x[1] > 0]))
