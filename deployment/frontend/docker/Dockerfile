FROM phusion/passenger-full:latest
MAINTAINER CozyChat <cozychat@example.com>

# 构建参数：Git仓库URL
ARG GIT_REPO_URL=https://github.com/zinohome/CozyChat.git
ENV GIT_REPO_URL=${GIT_REPO_URL}

# 构建参数：前端环境变量（用于构建时注入）
# 注意：这些变量会在构建时注入到前端代码中
ARG VITE_AMAP_MAPS_API_KEY
ARG VITE_TAVILY_API_KEY
ARG VITE_API_BASE_URL
ARG VITE_LOG_LEVEL
ARG VITE_APP_VERSION
ARG VITE_DEMO_MODE
ARG VITE_DEMO_USERNAME
ARG VITE_DEMO_PASSWORD
ARG VITE_SENTRY_DSN
ARG VITE_SENTRY_ENVIRONMENT

# 导出为环境变量，供构建脚本使用
ENV VITE_AMAP_MAPS_API_KEY=${VITE_AMAP_MAPS_API_KEY}
ENV VITE_TAVILY_API_KEY=${VITE_TAVILY_API_KEY}
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_LOG_LEVEL=${VITE_LOG_LEVEL}
ENV VITE_APP_VERSION=${VITE_APP_VERSION}
ENV VITE_DEMO_MODE=${VITE_DEMO_MODE}
ENV VITE_DEMO_USERNAME=${VITE_DEMO_USERNAME}
ENV VITE_DEMO_PASSWORD=${VITE_DEMO_PASSWORD}
ENV VITE_SENTRY_DSN=${VITE_SENTRY_DSN}
ENV VITE_SENTRY_ENVIRONMENT=${VITE_SENTRY_ENVIRONMENT}

# 复制构建脚本
COPY deployment/frontend/docker/bd_build/* /bd_build/

# 复制项目代码（作为备选，优先使用Git克隆）
# 注意：install.sh 会优先从Git克隆代码，如果Git克隆失败才使用COPY的代码
# 这样可以避免复制本地的 node_modules 等不需要的文件
#COPY frontend /opt/cozychat/frontend

# Sys ENV
ENV DEBIAN_FRONTEND noninteractive
ENV HOME /root
ENV EXT_HOSTS=''

# ...put your own build instructions here...
RUN mkdir -p /data && chmod 755 /bd_build/install.sh && /bd_build/install.sh

# Clean up APT when done.
WORKDIR /opt/cozychat/frontend

# Use baseimage-docker's init system.
EXPOSE 5173
VOLUME ["/data"]
CMD ["/sbin/my_init"]

