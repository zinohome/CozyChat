FROM phusion/passenger-full:latest
MAINTAINER CozyChat <cozychat@example.com>

# 构建参数：Git仓库URL
ARG GIT_REPO_URL=https://github.com/zinohome/CozyChat.git
ENV GIT_REPO_URL=${GIT_REPO_URL}

# 复制构建脚本
COPY deployment/backend/docker/bd_build/* /bd_build/

# 复制项目代码（作为备选，优先使用Git克隆）
# 注意：install.sh 会优先从Git克隆代码，如果Git克隆失败才使用COPY的代码
# 这样可以避免复制本地的 venv 等不需要的文件
#COPY backend /opt/cozychat/backend

# Sys ENV
ENV DEBIAN_FRONTEND noninteractive
ENV HOME /root
ENV EXT_HOSTS=''

# ...put your own build instructions here...
RUN mkdir -p /data && chmod 755 /bd_build/install.sh && /bd_build/install.sh

# 最终清理：删除不必要的文件（包括模型缓存）
RUN rm -rf /tmp/* /var/tmp/* && \
    rm -rf /root/.cache && \
    rm -rf /root/.cache/huggingface && \
    rm -rf /root/.cache/torch && \
    rm -rf /root/.cache/transformers && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean && \
    # 查找并删除可能的模型文件（>50MB）
    find /opt/cozychat -type f -size +50M -not -path "*/\.venv/*" -delete 2>/dev/null || true

# Clean up APT when done.
WORKDIR /opt/cozychat/backend

# Use baseimage-docker's init system.
EXPOSE 8000
VOLUME ["/data"]
CMD ["/sbin/my_init"]

