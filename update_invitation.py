import base64
import logging
import os
import requests
import subprocess
import sys
from logging import handlers


class Logger(object):
    level_relations = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'crit': logging.CRITICAL
    }

    def __init__(self, filename, level='info', when='D', backCount=3,
                 fmt='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'):
        self.logger = logging.getLogger(filename)
        format_str = logging.Formatter(fmt)
        self.logger.setLevel(self.level_relations.get(level))
        sh = logging.StreamHandler()
        sh.setFormatter(format_str)
        th = handlers.TimedRotatingFileHandler(filename=filename, when=when, backupCount=backCount, encoding='utf-8')
        th.setFormatter(format_str)
        self.logger.addHandler(sh)
        self.logger.addHandler(th)


log = Logger('update_invitation.log', level='info')



def get_v8_token():
    """获取v8 token"""
    url = os.getenv('V8URL', '')
    params = {
        'token': os.getenv('QUERY_TOKEN', '')
    }
    r = requests.get(url, params=params)
    if r.status_code != 200:
        log.logger.error('Fail to get v8 token, status code: {}'.format(r.status_code))
        sys.exit(1)
    access_token = r.json()['access_token']
    return access_token


def get_new_invitation(access_token):
    """生成邀请链接"""
    url = os.getenv('InviteApiUrl', '')
    data = {
        'access_token': access_token,
        'role_id': os.getenv('RoleId', ''),
        'need_check': os.getenv('NeedCheck', 1)
    }
    r = requests.post(url, data=data)
    if r.status_code != 201:
        log.logger.error('Fail to generate new invitation, status code: {}'.format(r.status_code))
        sys.exit(1)
    invite_url = r.json()['invite_url']
    log.logger.info('Generate invitation: {}'.format(invite_url))
    return invite_url


def download_faq_file():
    """下载FAQ file"""
    subprocess.call('test -f openEuler-Infra-FAQ.md && rm -f openEuler-Infra-FAQ.md', shell=True)
    subprocess.call('wget https://gitee.com/openeuler/infrastructure/raw/master/docs/openEuler-Infra-FAQ.md', shell=True)


def get_current_invite_url(filepath):
    """获取当前的邀请链接"""
    with open(filepath, 'r') as f:
        pattern = '请点击[链接](https://gitee.com/open_euler?invite='
        for line in f.readlines():
            if pattern in line:
                current_url = line.split('(')[1].split(')')[0]
                log.logger.info('Current invitation: {}'.format(current_url))
                return current_url


def generate_b64code(current_url, invite_url, filepath):
    """修改FAQ并生成base64编码"""
    with open(filepath, 'r') as f:
        content = f.read()
    content = content.replace(current_url, invite_url)
    b64code = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    return b64code


def get_file_sha():
    """查询目标文件哈希值"""
    url = os.getenv('UpdateFileApiUrl', '')
    params = {
        'access_token': os.getenv('AccessToken', '')
    }
    r = requests.get(url, params=params)
    if r.status_code != 200:
        log.logger.error('Fail to get sha of the FAQ file, status code: {}'.format(r.status_code))
        sys.exit(1)
    sha_value = r.json()['sha']
    return sha_value


def update_repo_file(b64code, sha_value, filepath):
    """修改仓库中的文件"""
    url = os.getenv('UpdateFileApiUrl', '')
    data = {
        'access_token': os.getenv('AccessToken', ''),
        'content': b64code,
        'sha': sha_value,
        'message': 'update {}'.format(filepath)
    }
    r = requests.put(url, data=data)
    if r.status_code != 200:
        log.logger.error('Fail to update FAQ file, reason : {}'.format(r.json()))
    else:
        log.logger.info('Update FAQ file successfully!')


def main():
    filepath = os.getenv('FAQFilename', '')
    if not filepath:
        log.logger.error('Filepath is not exist, please check!')
        sys.exit(1)
    access_token = get_v8_token()
    invite_url = get_new_invitation(access_token)
    download_faq_file()
    current_url = get_current_invite_url(filepath)
    if current_url == invite_url:
        log.logger.info('Find there is no difference between current_url and invite_url, skip updating.')
        sys.exit()
    b64code = generate_b64code(current_url, invite_url, filepath)
    sha_value = get_file_sha()
    update_repo_file(b64code, sha_value, filepath)


if __name__ == '__main__':
    main()
