FROM openeuler/openeuler:21.03

MAINTAINER liuqi<469227928@qq.com>

RUN yum update && \
yum install -y wget python3-pip

RUN pip3 install requests

WORKDIR /work/invite-enterprise-members

COPY . /work/invite-enterprise-members

ENTRYPOINT ["python3", "update_invitation.py"]
