FROM openeuler/openeuler:24.03-lts

RUN yum install -y vim wget git xz tar make automake autoconf libtool gcc gcc-c++ kernel-devel libmaxminddb-devel pcre-devel openssl openssl-devel tzdata \
readline-devel libffi-devel python3-devel mariadb-devel python3-pip net-tools.x86_64 iputils

RUN groupadd -g 1000 robot useradd -u 1000 -g robot -s /bin/bash -m robot

RUN pip3 install requests -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /work/invite-enterprise-members

USER robot

COPY --chown=robot . /work/invite-enterprise-members

ENTRYPOINT ["python3", "update_invitation.py"]
