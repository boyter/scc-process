import requests
from multiprocessing import Pool
import multiprocessing
import hashlib
import os
import re
import string
import boto3
import subprocess

def process(site):
    pid = str(multiprocessing.current_process().pid)
    filename, _ = process_path(site)
    print('processing', site, pid, filename)

    

    try:    
        os.chdir('/tmp')
        os.system('rm -rf /tmp/scc-tmp-path-' + pid)
        p = subprocess.Popen(['git', 'clone', '--depth=1', site, '/tmp/scc-tmp-path-' + pid])
        p.wait(60)        
        # os.system('git clone --depth=1 ' + site + ' scc-tmp-path-' + pid)
        os.system('scc -f json -o /tmp/' + filename + ' /tmp/scc-tmp-path-' + pid)
        
        s3 = boto3.client('s3')
        with open('/tmp/' + filename, 'rb') as f:
            s3.upload_fileobj(f, 'sloccloccode', filename)
    except:
        p.kill()

    print('cleaning up', site, pid, filename)
    os.system('rm /tmp/' + filename)
    os.system('rm -rf /tmp/scc-tmp-path-' + pid)


def process_path(path):
    path = re.sub('', '', path, flags=re.MULTILINE )

    s = [clean_string(x) for x in path.lower().split('/') if x != '']

    if len(s) != 4:
        return None, None

    # Cheap clean check
    for x in s:
        if x == '':
            return None, None

    # File for json
    filename = s[1].replace('.com', '').replace('.org', '')
    filename += '.' + s[2]
    filename += '.' + s[3].replace('.git', '') + '.json'

    # Need path
    path = s[3].replace('.git', '')

    return (filename, path)


def clean_string(s):
    valid = string.ascii_lowercase
    valid += string.digits
    valid += '-'
    valid += '.'
    valid += '_'

    clean = ''

    for c in s:
        if c in valid:
            clean += c

    return clean

if __name__ == '__main__':
    sites = []
    count = 0
    for line in open('urls.txt'):
        count += 1
        line = line.strip()

        if line != '':
            line += '.git'

            # we already processed the first 2 million or so
            if count > 0:
                sites.append(line)

    p = Pool(processes=32)
    p.map(process, sites)
    sites = []
