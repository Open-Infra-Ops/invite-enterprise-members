FROM openeuler/openeuler:22.03-lts

MAINTAINER liuqi<469227928@qq.com>

RUN yum install -y wget python3-pip

RUN pip3 install requests -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /work/invite-enterprise-members

COPY . /work/invite-enterprise-members

ENTRYPOINT ["python3", "update_invitation.py"]
