FROM openeuler/openeuler:24.03-lts

RUN yum install -y wget python3-pip

RUN groupadd -g 1000 robot && \
    useradd -u 1000 -g robot -s /bin/bash -m robot

USER robot

RUN pip3 install requests -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /work/invite-enterprise-members

COPY --chown=robot . /work/invite-enterprise-members

ENTRYPOINT ["python3", "update_invitation.py"]
