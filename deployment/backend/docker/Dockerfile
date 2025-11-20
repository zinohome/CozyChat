FROM phusion/passenger-full:latest
MAINTAINER CozyChat <cozychat@example.com>

# 复制构建脚本
COPY deployment/backend/docker/bd_build/* /bd_build/

# 复制项目代码（如果使用本地代码构建）
# 注意：如果使用Git克隆方式，可以注释掉下面的COPY，让install.sh从Git克隆
COPY backend /opt/cozychat/backend
COPY packages /opt/cozychat/packages

# Sys ENV
ENV DEBIAN_FRONTEND noninteractive
ENV HOME /root
ENV EXT_HOSTS=''

# ...put your own build instructions here...
RUN mkdir -p /data && chmod 755 /bd_build/install.sh && /bd_build/install.sh

# Clean up APT when done.
WORKDIR /opt/cozychat/backend

# Use baseimage-docker's init system.
EXPOSE 8000
VOLUME ["/data"]
CMD ["/sbin/my_init"]

