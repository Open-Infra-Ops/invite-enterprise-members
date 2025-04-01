import base64
import logging
import os
import requests
import subprocess
import sys
from logging import handlers
import json

Config = dict()


def load_config():
    config_path = "/vault/secrets/config.json"
    with open(os.path.expanduser(config_path), "r") as secret:
        global Config
        Config = json.load(secret)

    os.remove(config_path)


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
    url = Config.get('V8URL', '')
    params = {
        'token': Config.get('QUERY_TOKEN', '')
    }
    r = requests.get(url, params=params)
    if r.status_code != 200:
        log.logger.error('Fail to get v8 token, status code: {}'.format(r.status_code))
        sys.exit(1)
    access_token = r.json()['access_token']
    return access_token


def get_new_invitation(access_token):
    """生成邀请链接"""
    url = Config.get('InviteApiUrl', '')
    data = {
        'access_token': access_token,
        'role_id': Config.get('RoleId', ''),
        'need_check': Config.get('NeedCheck', 1)
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
    subprocess.call('wget https://gitee.com/openeuler/infrastructure/raw/master/docs/openEuler-Infra-FAQ.md',
                    shell=True)
    subprocess.call('test -f openEuler-Infra-FAQ-en.md && rm -f openEuler-Infra-FAQ-en.md', shell=True)
    subprocess.call('wget https://gitee.com/openeuler/infrastructure/raw/master/docs/openEuler-Infra-FAQ-en.md',
                    shell=True)


def get_current_invite_url(filepath):
    """获取当前的邀请链接"""
    with open(filepath, 'r') as f:
        pattern = '(https://gitee.com/open_euler?invite='
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


def get_file_sha(url):
    """查询目标文件哈希值"""
    params = {
        'access_token': Config.get('AccessToken', '')
    }
    r = requests.get(url, params=params)
    if r.status_code != 200:
        log.logger.error('Fail to get sha of the FAQ file, status code: {}'.format(r.status_code))
        sys.exit(1)
    sha_value = r.json()['sha']
    return sha_value


def update_repo_file(url, b64code, sha_value, filepath):
    """修改仓库中的文件"""
    data = {
        'access_token': Config.get('AccessToken', ''),
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
    load_config()
    filepath = Config.get('FAQFilename', '')
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
    update_file_api_url = Config.get('UpdateFileApiUrl', '')
    sha_value = get_file_sha(update_file_api_url)
    update_repo_file(update_file_api_url, b64code, sha_value, filepath)

    en_filepath = filepath.replace('.md', '-en.md')
    en_current_url = get_current_invite_url(en_filepath)
    en_b64code = generate_b64code(en_current_url, invite_url, en_filepath)
    en_update_file_api_url = update_file_api_url.replace(filepath, en_filepath)
    en_sha_vale = get_file_sha(en_update_file_api_url)
    update_repo_file(en_update_file_api_url, en_b64code, en_sha_vale, en_filepath)


if __name__ == '__main__':
    main()
